"""Descarcă PDF-urile de declarații de interese pentru analiza structurii.

Citește lista din data/v1/declaratii/legislatura-{leg}.json și descarcă
PDF-urile de interese în data/analize/_pdfs_interese/.

Utilizare:
    python scripts/download_interese_pdfs.py                # leg=2024, toți deputații
    python scripts/download_interese_pdfs.py --limit 20     # primii 20 (test/explorare)
    python scripts/download_interese_pdfs.py --leg 2020
    python scripts/download_interese_pdfs.py --no-cache     # re-descarcă dacă există

Fișierele sunt numite după hash-ul URL-ului (același cache ca pentru avere):
    <sha1(url)[:12]>_interese.pdf
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scrapers._http import get as http_get  # noqa: E402

PDF_CACHE = ROOT / "data" / "analize" / "_pdfs_interese"

logger = logging.getLogger(__name__)


def _pdf_name(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12] + "_interese.pdf"


def download_pdf(url: str, dest: Path, force: bool = False) -> bool:
    if dest.exists() and not force:
        logger.debug(f"  cache hit: {dest.name}")
        return True
    try:
        r = http_get(url)
        r.raise_for_status()
        dest.write_bytes(r.content)
        logger.debug(f"  downloaded: {dest.name} ({len(r.content):,} bytes)")
        return True
    except Exception as e:
        logger.warning(f"  download failed {url}: {e}")
        return False


def run(leg: int, limit: int | None, force: bool) -> int:
    decl_file = ROOT / "data" / "v1" / "declaratii" / f"legislatura-{leg}.json"
    if not decl_file.exists():
        print(
            f"Lipsește {decl_file}. Rulează mai întâi: python scripts/run_declaratii.py --leg {leg}"
        )
        return 1

    PDF_CACHE.mkdir(parents=True, exist_ok=True)

    deputies = json.loads(decl_file.read_text(encoding="utf-8"))["data"]
    if limit:
        deputies = deputies[:limit]

    total_pdfs = sum(len(d.get("interese") or []) for d in deputies)
    print(f"leg={leg}: {len(deputies)} deputați · {total_pdfs} PDF-uri interese")
    print(f"Cache: {PDF_CACHE}")
    print()

    stats = {"ok": 0, "skip": 0, "err": 0}
    for i, d in enumerate(deputies, 1):
        name = d["deputat_nume"]
        interese_pdfs = d.get("interese") or []
        if not interese_pdfs:
            print(f"  [{i:3d}] {name} — fără PDF interese")
            stats["skip"] += 1
            continue

        results = []
        for fis in interese_pdfs:
            url = fis["url"]
            dest = PDF_CACHE / _pdf_name(url)
            ok = download_pdf(url, dest, force=force)
            results.append(("OK" if ok else "ERR", url, dest))
            if ok:
                stats["ok"] += 1
            else:
                stats["err"] += 1

        status_str = " ".join(r[0] for r in results)
        print(f"  [{i:3d}] {name} — {len(interese_pdfs)} PDF(uri): {status_str}")

        # Pauză mică între deputați (nu între PDF-uri individuale)
        if i % 10 == 0:
            time.sleep(1)

    print()
    print(
        f"Descărcat: {stats['ok']} OK · {stats['err']} erori · {stats['skip']} fără PDF"
    )
    print(f"Fișiere în: {PDF_CACHE}")

    if stats["ok"] > 0:
        sizes = [f.stat().st_size for f in PDF_CACHE.glob("*_interese.pdf")]
        print(
            f"Total pe disc: {sum(sizes) / 1024 / 1024:.1f} MB · avg {sum(sizes) / len(sizes) / 1024:.0f} KB/PDF"
        )

    return 0 if stats["err"] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Descarcă PDF-uri declarații interese")
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument(
        "--limit", type=int, default=None, help="Limitează la primii N deputați"
    )
    parser.add_argument("--no-cache", action="store_true", help="Forțează re-download")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    return run(leg=args.leg, limit=args.limit, force=args.no_cache)


if __name__ == "__main__":
    sys.exit(main())
