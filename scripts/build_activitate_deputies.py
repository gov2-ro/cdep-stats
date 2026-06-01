"""Build per-deputy activitate payload pentru deputati-activitate.html circle dashboard.

Citește indexul de deputați și emite câmpurile de activitate parlamentară,
îmbogățite cu partid_short (din indexul declaratii-avere) și imagine.

Output: data/v1/stats/activitate-deputies-{leg}.json
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

from _party_history import parse_group_history  # noqa: E402
from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020]

ACTIVITY_FIELDS = [
    "activitate_sedinte",
    "activitate_luari_cuvant",
    "activitate_propuneri_legislative",
    "activitate_legi_promulgate",
    "activitate_declaratii_politice",
    "activitate_intrebari_interpelari",
]


def _load_parties(root: Path) -> dict[str, str]:
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


def _load_partid_map(root: Path, leg: int) -> dict[int, str]:
    """Returns {cdep_idm: partid_short} from the avere index."""
    avere_file = root / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}.json"
    if not avere_file.exists():
        return {}
    data = json.loads(avere_file.read_text(encoding="utf-8"))["data"]
    return {d["cdep_idm"]: d.get("partid_short") or "Neafiliat" for d in data}


def _load_group_histories(root: Path, leg: int) -> dict[int, list[dict]]:
    """Returns {cdep_idm: partid_history} from deputati index."""
    deputati_file = root / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not deputati_file.exists():
        return {}
    data = json.loads(deputati_file.read_text(encoding="utf-8")).get("data", [])
    histories = {}
    for d in data:
        if "cdep_idm" in d:
            history = parse_group_history(d.get("current_group"))
            if history:
                histories[d["cdep_idm"]] = history
    return histories


def build_leg(leg: int, root: Path = ROOT) -> int:
    deputati_file = root / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not deputati_file.exists():
        print(f"Lipsește {deputati_file}.", file=sys.stderr)
        return 1

    deputati = json.loads(deputati_file.read_text(encoding="utf-8"))["data"]
    partid_map = _load_partid_map(root, leg)
    parties = _load_parties(root)
    group_histories = _load_group_histories(root, leg)

    deputies = []
    for d in deputati:
        idm: int = d["cdep_idm"]
        partid = partid_map.get(idm) or "Neafiliat"
        record: dict = {
            "cdep_idm": idm,
            "name": d.get("name") or d.get("deputat_nume") or "",
            "partid": partid,
            "partid_history": group_histories.get(idm, []),
            "image": d.get("image", ""),
        }
        for f in ACTIVITY_FIELDS:
            record[f] = d.get(f)
        deputies.append(record)

    payload = {
        "meta": Meta(
            generated_at=datetime.now(UTC),
            source_url=(
                f"https://endimion2k.github.io/cdep-api-poc/"
                f"data/v1/deputati/legislatura-{leg}.json"
            ),
            scraper_version="0.1.0",
            count=len(deputies),
        ).model_dump(mode="json"),
        "parties": parties,
        "deputies": deputies,
    }

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"activitate-deputies-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK leg {leg}: {len(deputies)} deputați → {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true")
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
