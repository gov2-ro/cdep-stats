"""Rulează scraperul de deputați și salvează JSON-ul.

    python scripts/run_deputati.py                    # incremental, leg 2024
    python scripts/run_deputati.py --limit 3          # test rapid
    python scripts/run_deputati.py --leg 2020         # altă legislatură
    python scripts/run_deputati.py --full             # refetch toate profilele

IMPLICIT incremental: doar deputații noi (idm necunoscut). Cu ``--full`` refetchează
toate profilele — recomandat săptămânal pentru a captura schimbări de partid,
comisii, activitate (cifrele cu prezența).

Env pentru paralelism (util pe CI):
    CDEP_SCRAPE_WORKERS=4
    CDEP_HTTP_THROTTLE_SECONDS=0.25
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402
from scrapers.deputati import scrape  # noqa: E402

SCRAPER_VERSION = "0.1.0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--cam", type=int, default=2)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--full",
        action="store_true",
        help="Refetch toate profilele (ignoră skip_ids). Default: incremental.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_path = args.out or ROOT / "data" / "v1" / "deputati" / f"legislatura-{args.leg}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Citim existent pentru a determina idm-urile cunoscute (incremental)
    existing_ids: set[int] = set()
    existing_data: list[dict] = []
    if out_path.exists() and not args.full:
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_data = existing.get("data", [])
            existing_ids = {int(d["cdep_idm"]) for d in existing_data if d.get("cdep_idm")}
            print(f"Index existent: {len(existing_ids)} deputați (mod incremental)")
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    if args.full:
        print("Mod --full: refetch toate profilele deputaților.")

    deputati = scrape(
        leg=args.leg,
        cam=args.cam,
        limit=args.limit,
        skip_ids=existing_ids if not args.full else None,
    )

    # Merge cu existent: overwrite idm-urile re-fetched, păstrează restul
    new_dicts = [d.model_dump(mode="json", exclude_none=False) for d in deputati]
    if existing_data and not args.full:
        new_ids = {int(d["cdep_idm"]) for d in new_dicts if d.get("cdep_idm")}
        merged = [d for d in existing_data if int(d.get("cdep_idm", 0)) not in new_ids] + new_dicts
        # Sortare stabilă după idm
        merged.sort(key=lambda d: int(d.get("cdep_idm", 0)))
        new_data = merged
    else:
        new_data = new_dicts

    # Semantic-diff: nu suprascriem dacă data e identică (doar timestamp)
    data_changed = True
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            if existing.get("data") == new_data:
                data_changed = False
        except (json.JSONDecodeError, KeyError):
            pass

    if not data_changed:
        print(f"OK {len(new_data)} deputati - date identice, skip overwrite.")
        return 0

    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"https://www.cdep.ro/ords/pls/parlam/structura2015.home?leg={args.leg}",
        scraper_version=SCRAPER_VERSION,
        count=len(new_data),
    )
    payload = {"meta": meta.model_dump(mode="json"), "data": new_data}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"OK {len(new_data)} deputati salvați (+{len(deputati)} re-fetched) în {out_path}")
    print(f"   File size: {out_path.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
