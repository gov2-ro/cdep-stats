"""Rulează scraperul de moțiuni și salvează JSON.

Storage: data/v1/motiuni/legislatura-{leg}.json (toate moțiunile dintr-o cameră +
legislatură).

Utilizare:
    python scripts/run_motiuni.py --leg 2024
    python scripts/run_motiuni.py --leg 2020 --cam 2
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
from scrapers.motiuni import scrape_all  # noqa: E402

SCRAPER_VERSION = "0.1.0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024, help="Legislatură (default: 2024)")
    parser.add_argument("--cam", type=int, default=2, help="Cameră (default: 2 = CD)")
    parser.add_argument(
        "--full", action="store_true", help="Refetch toate moțiunile (ignoră skip_ids)."
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_path = ROOT / "data" / "v1" / "motiuni" / f"legislatura-{args.leg}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Citim existent
    existing_ids: set[int] = set()
    existing_data: list[dict] = []
    if out_path.exists() and not args.full:
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_data = existing.get("data", [])
            existing_ids = {int(d["cdep_idm"]) for d in existing_data if d.get("cdep_idm")}
            print(f"Index existent: {len(existing_ids)} moțiuni (mod incremental)")
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    print(f"Scrape moțiuni: leg={args.leg} cam={args.cam} (cdep.ro acceptă filtru leg)")
    items = scrape_all(
        args.leg,
        args.cam,
        skip_ids=existing_ids if not args.full else None,
    )

    if not items and not existing_data:
        print("Niciun rezultat.")
        return 0

    # cdep.ro respectă filtrul ?leg= → toate moțiunile primite aparțin legislaturii cerute.
    new_dicts = []
    for item in items:
        item_dict = item.model_dump(mode="json", exclude_none=False)
        item_dict["legislatura"] = args.leg
        new_dicts.append(item_dict)

    # Merge: overwrite idm-urile re-fetched, păstrează restul
    if existing_data and not args.full:
        new_ids = {int(d["cdep_idm"]) for d in new_dicts if d.get("cdep_idm")}
        group = [d for d in existing_data if int(d.get("cdep_idm", 0)) not in new_ids] + new_dicts
    else:
        group = new_dicts
    group.sort(key=lambda x: x.get("data_inregistrare") or "", reverse=True)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"https://www.cdep.ro/ords/pls/parlam/motiuni2015.lista?leg={args.leg}&cam={args.cam}",
        scraper_version=SCRAPER_VERSION,
        count=len(group),
    )
    payload = {"meta": meta.model_dump(mode="json"), "data": group}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  legislatura {args.leg}: {len(group)} moțiuni → {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
