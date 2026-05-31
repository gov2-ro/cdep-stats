"""Build per-deputy avere payload pentru deputati-avere.html circle dashboard.

Joins:
  1. data/v1/declaratii-avere/legislatura-{leg}.json  — index (cdep_idm, name, partid, metrics)
  2. data/v1/declaratii-avere/legislatura-{leg}/{cdep_idm}.json — detalii (suprafata/auto/datorii)
  3. data/v1/deputati/legislatura-{leg}.json — imagine URL

Emite: data/v1/stats/avere-deputies-{leg}.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020]


def _load_detail_extras(root: Path, leg: int) -> dict[int, dict]:
    """Returnează {cdep_idm: {suprafata_mp, auto_count, datorii_ron}} din ultima declarație."""
    detail_dir = root / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}"
    extras: dict[int, dict] = {}
    if not detail_dir.is_dir():
        return extras
    for fpath in detail_dir.glob("*.json"):
        try:
            raw = json.loads(fpath.read_text(encoding="utf-8"))["data"]
            declaratii = raw.get("declaratii") or []
            if not declaratii:
                continue
            last = declaratii[-1]
            extras[raw["cdep_idm"]] = {
                "suprafata_mp": last.get("suprafata_total_mp"),
                "auto_count": last.get("auto_count"),
                "datorii_ron": last.get("datorii_total_ron"),
            }
        except (KeyError, json.JSONDecodeError):
            continue
    return extras


def _load_images(root: Path, leg: int) -> dict[int, str]:
    """Returnează {cdep_idm: image_url} din indexul de deputați."""
    deputati_file = root / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not deputati_file.exists():
        return {}
    data = json.loads(deputati_file.read_text(encoding="utf-8")).get("data", [])
    return {d["cdep_idm"]: d.get("image", "") for d in data if "cdep_idm" in d}


def _load_parties(root: Path) -> dict[str, str]:
    """Returnează {partid_short: logo_filename} din legenda-partide.csv."""
    csv_file = root / "data" / "assets" / "legenda-partide.csv"
    parties: dict[str, str] = {}
    if not csv_file.exists():
        return parties
    with csv_file.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = (row.get("ID") or "").strip()
            logo = (row.get("Logo") or "").strip()
            if pid and logo:
                parties[pid] = logo
    return parties


def build_leg(leg: int, root: Path = ROOT) -> int:
    index_file = root / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}.json"
    if not index_file.exists():
        print(
            f"Lipsește {index_file}. Rulează întâi build_declaratii_avere.py --leg {leg}",
            file=sys.stderr,
        )
        return 1

    avere_index: list[dict] = json.loads(index_file.read_text(encoding="utf-8"))["data"]
    extras = _load_detail_extras(root, leg)
    images = _load_images(root, leg)
    parties = _load_parties(root)

    deputies = []
    for d in avere_index:
        idm: int = d["cdep_idm"]
        ex = extras.get(idm, {})
        has_decl = d.get("n_declaratii", 0) > 0
        # Evoluție în mandat: only meaningful cu ≥2 declarații; altfel null (afișat ca "—").
        has_evo = d.get("n_declaratii", 0) > 1
        deputies.append(
            {
                "cdep_idm": idm,
                "name": d["deputat_nume"],
                "partid": d.get("partid_short") or "Neafiliat",
                "image": images.get(idm, ""),
                "venituri_ron": d.get("ultima_venituri_ron") if has_decl else None,
                "conturi_ron": d.get("ultima_conturi_ron") if has_decl else None,
                "imobile_count": d.get("ultima_imobile_count") if has_decl else None,
                "suprafata_mp": ex.get("suprafata_mp") if has_decl else None,
                "auto_count": ex.get("auto_count") if has_decl else None,
                "datorii_ron": ex.get("datorii_ron") if has_decl else None,
                "delta_conturi_ron": d.get("delta_conturi_ron") if has_evo else None,
                "delta_imobile": d.get("delta_imobile") if has_evo else None,
            }
        )

    payload = {
        "meta": Meta(
            generated_at=datetime.now(UTC),
            source_url=(
                f"https://endimion2k.github.io/cdep-api-poc/"
                f"data/v1/declaratii-avere/legislatura-{leg}.json"
            ),
            scraper_version="0.1.0",
            count=len(deputies),
        ).model_dump(mode="json"),
        "parties": parties,
        "deputies": deputies,
    }

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"avere-deputies-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK leg {leg}: {len(deputies)} deputați · {len(parties)} partide → {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build per-deputy avere JSON for circle dashboard."
    )
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true", help="Build all legs")
    args = parser.parse_args()

    legs = ALL_LEGS if args.all else [args.leg]
    ret = 0
    for leg in legs:
        r = build_leg(leg)
        if r != 0 and not args.all:
            return r
        ret = ret or r
    return ret


if __name__ == "__main__":
    sys.exit(main())
