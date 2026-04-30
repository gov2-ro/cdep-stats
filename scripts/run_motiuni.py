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


def detect_legislatura(year: int) -> int:
    if year >= 2024:
        return 2024
    if year >= 2020:
        return 2020
    if year >= 2016:
        return 2016
    return 2012


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024, help="Legislatură (default: 2024)")
    parser.add_argument("--cam", type=int, default=2, help="Cameră (default: 2 = CD)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print(f"Scrape moțiuni: cam={args.cam} (cdep.ro returnează doar legislatura curentă)")
    items = scrape_all(args.leg, args.cam)

    if not items:
        print("Niciun rezultat.")
        return 0

    # Group după legislatura detectată din data_inregistrare
    # cdep.ro returnează toate motiunile actuale; le asignăm la legislatura corectă
    from collections import defaultdict

    by_leg: dict[int, list] = defaultdict(list)
    for item in items:
        if item.data_inregistrare:
            real_leg = detect_legislatura(item.data_inregistrare.year)
        else:
            real_leg = args.leg
        # Override item legislatura
        item_dict = item.model_dump(mode="json", exclude_none=False)
        item_dict["legislatura"] = real_leg
        by_leg[real_leg].append(item_dict)

    # Sortez în fiecare grup și scriu fișiere separate per legislatura
    for leg, group in by_leg.items():
        group.sort(key=lambda x: x.get("data_inregistrare") or "", reverse=True)
        out_path = ROOT / "data" / "v1" / "motiuni" / f"legislatura-{leg}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        meta = Meta(
            generated_at=datetime.now(UTC),
            source_url=f"https://www.cdep.ro/pls/parlam/motiuni2015.lista?cam={args.cam}",
            scraper_version=SCRAPER_VERSION,
            count=len(group),
        )
        payload = {"meta": meta.model_dump(mode="json"), "data": group}
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  legislatura {leg}: {len(group)} moțiuni → {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
