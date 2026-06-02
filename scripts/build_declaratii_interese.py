"""Build endpoint /declaratii-interese — parsare PDF-uri pentru toți deputații.

Pentru fiecare deputat, descarcă TOATE PDF-urile de interese și extrage cu
pdfplumber: companii deținute, funcții în conducere, funcții de partid,
contracte cu instituții publice. Salvează:

- ``data/v1/declaratii-interese/legislatura-{leg}.json``        — index/sumar
- ``data/v1/declaratii-interese/legislatura-{leg}/{idm}.json``  — detalii per deputat

Utilizare:
    python scripts/build_declaratii_interese.py                   # legislatura 2024
    python scripts/build_declaratii_interese.py --leg 2020
    python scripts/build_declaratii_interese.py --limit 10        # test rapid
    python scripts/build_declaratii_interese.py --no-cache        # re-download PDF-uri

NOTE:
- Sursa listei: data/v1/declaratii/legislatura-{leg}.json (produs de run_declaratii.py)
- PDF-urile sunt cache-uite în data/analize/_pdfs_interese/ (același dir ca downloader)
- Procesare incrementală: PDF-urile existente nu sunt re-descărcate dacă --no-cache absent
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

try:
    import pdfplumber  # noqa: F401
except ImportError:
    print("EROARE: pdfplumber nu e instalat. Rulează: pip install pdfplumber")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from parsers.interese_pdf import parse_pdf  # noqa: E402
from schemas.common import Meta  # noqa: E402
from schemas.interese import InteresDeclaratie, InteresDeputat, InteresSummary  # noqa: E402
from scrapers._http import get as http_get  # noqa: E402

SCRAPER_VERSION = "0.1.0"
ALL_LEGS = [2024, 2020, 2016]
PDF_CACHE = ROOT / "data" / "analize" / "_pdfs_interese"


def _strip_diacritics(s: str) -> str:
    import unicodedata

    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _voter_canonical_id(name: str) -> str:
    norm = " ".join(_strip_diacritics(name).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _interese_id(leg: int, idm: int) -> str:
    return hashlib.sha256(f"{leg}|{idm}|interese".encode()).hexdigest()[:16]


def _pdf_name(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12] + "_interese.pdf"


def _download_pdf(url: str, dest: Path, force: bool = False) -> bool:
    if dest.exists() and not force:
        return True
    try:
        r = http_get(url)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        logging.warning(f"  download failed {url}: {e}")
        return False


def _parse_isodate(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def process_deputat(d: dict, leg: int, force: bool = False) -> InteresDeputat | None:
    """Procesează toate PDF-urile de interese ale unui deputat."""
    interese_pdfs = d.get("interese") or []
    if not interese_pdfs:
        return None

    interese_pdfs_sorted = sorted(interese_pdfs, key=lambda x: x.get("data") or "")

    declaratii: list[InteresDeclaratie] = []
    for fis in interese_pdfs_sorted:
        url = fis["url"]
        data_dep = _parse_isodate(fis.get("data"))

        pdf_path = PDF_CACHE / _pdf_name(url)
        if not _download_pdf(url, pdf_path, force=force):
            declaratii.append(
                InteresDeclaratie(
                    pdf_url=url,
                    data_depunere=data_dep,
                    text_extracted=False,
                    error="download failed",
                )
            )
            continue

        parsed = parse_pdf(pdf_path)
        declaratii.append(
            InteresDeclaratie(
                pdf_url=url,
                data_depunere=data_dep,
                **parsed,
            )
        )

    if not declaratii:
        return None

    ultima = declaratii[-1]

    return InteresDeputat(
        id=_interese_id(leg, d["cdep_idm"]),
        cdep_idm=d["cdep_idm"],
        deputat_nume=d["deputat_nume"],
        deputat_canonical_id=d.get("deputat_canonical_id")
        or _voter_canonical_id(d["deputat_nume"]),
        legislatura=leg,
        partid_short=d.get("partid_short"),
        declaratii=declaratii,
        ultima_data=ultima.data_depunere or ultima.data_completarii,
        ultima_nr_companii=ultima.nr_companii,
        ultima_are_functie_partid=ultima.are_functie_partid,
        ultima_are_contracte_publice=ultima.are_contracte_publice,
        ultima_contracte_total_ron=ultima.contracte_total_ron,
    )


def run_leg(leg: int, args: argparse.Namespace) -> int:
    decl_file = ROOT / "data" / "v1" / "declaratii" / f"legislatura-{leg}.json"
    if not decl_file.exists():
        print(
            f"Lipsește {decl_file}. Rulează: python scripts/run_declaratii.py --leg {leg}"
        )
        return 1

    PDF_CACHE.mkdir(parents=True, exist_ok=True)
    out_dir = ROOT / "data" / "v1" / "declaratii-interese" / f"legislatura-{leg}"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = (
        ROOT / "data" / "v1" / "declaratii-interese" / f"legislatura-{leg}.json"
    )

    declaratii = json.loads(decl_file.read_text(encoding="utf-8"))["data"]
    if args.limit:
        declaratii = declaratii[: args.limit]
    print(f"Procesez {len(declaratii)} deputați pentru legislatura {leg}...")

    summaries: list[dict] = []
    stats = {"ok": 0, "err": 0, "skip": 0}

    for i, d in enumerate(declaratii, 1):
        try:
            dep = process_deputat(d, leg, force=args.no_cache)
        except Exception as e:
            logging.warning(f"  {d['deputat_nume']}: {e}")
            stats["err"] += 1
            continue

        if not dep:
            stats["skip"] += 1
            continue

        # Per-deputat detail file
        detail_path = out_dir / f"{dep.cdep_idm}.json"
        payload = {
            "meta": Meta(
                generated_at=datetime.now(UTC),
                source_url=f"https://www.cdep.ro/ords/pls/dic/declaratii2015.deputati?tip=ai&leg={leg}",
                scraper_version=SCRAPER_VERSION,
                count=len(dep.declaratii),
            ).model_dump(mode="json"),
            "data": dep.model_dump(mode="json", exclude_none=False),
        }
        detail_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        summaries.append(
            InteresSummary(
                id=dep.id,
                cdep_idm=dep.cdep_idm,
                deputat_nume=dep.deputat_nume,
                legislatura=dep.legislatura,
                partid_short=dep.partid_short,
                n_declaratii=len(dep.declaratii),
                ultima_data=dep.ultima_data,
                ultima_nr_companii=dep.ultima_nr_companii,
                ultima_are_functie_partid=dep.ultima_are_functie_partid,
                ultima_are_contracte_publice=dep.ultima_are_contracte_publice,
                ultima_contracte_total_ron=dep.ultima_contracte_total_ron,
                detail_url=f"declaratii-interese/legislatura-{leg}/{dep.cdep_idm}.json",
            ).model_dump(mode="json", exclude_none=False)
        )

        stats["ok"] += 1
        if i % 25 == 0:
            print(f"  [{i}/{len(declaratii)}] {d['deputat_nume']}")
        if i % 10 == 0:
            time.sleep(0.5)

    summaries.sort(key=lambda x: (x.get("partid_short") or "ZZZ", x["deputat_nume"]))

    index_payload = {
        "meta": Meta(
            generated_at=datetime.now(UTC),
            source_url=f"https://www.cdep.ro/ords/pls/dic/declaratii2015.deputati?tip=ai&leg={leg}",
            scraper_version=SCRAPER_VERSION,
            count=len(summaries),
        ).model_dump(mode="json"),
        "data": summaries,
    }
    index_path.write_text(
        json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print()
    print(f"OK: {stats['ok']} deputați procesați.")
    print(f"   Skip (fără PDF interese): {stats['skip']}")
    print(f"   Erori: {stats['err']}")
    print(f"   Index: {index_path}")
    print(f"   Detalii: {out_dir}/")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build declarații-interese: descarcă PDF-uri și parsează."
    )
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true", help="Build 2024 + 2020 + 2016")
    parser.add_argument(
        "--limit", type=int, default=None, help="Limită deputați (test)"
    )
    parser.add_argument("--no-cache", action="store_true", help="Forțează re-download")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    legs = ALL_LEGS if args.all else [args.leg]
    for leg in legs:
        ret = run_leg(leg, args)
        if ret != 0 and not args.all:
            return ret
    return 0


if __name__ == "__main__":
    sys.exit(main())
