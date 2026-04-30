"""Împarte fișierele mari (interpelari, proiecte) în fișiere per an.

Beneficii:
- Reducere timp încărcare pe mobil (de la 21MB la ~3MB/an)
- Cache CDN mai eficient (clienții fetch doar anul de interes)
- Backward compat: fișierul big legislatura-{leg}.json rămâne intact

Output:
- data/v1/interpelari/legislatura-2024/2024.json, 2025.json, 2026.json (+ _index.json)
- data/v1/proiecte/legislatura-2024/2024.json, 2025.json, 2026.json (+ _index.json)

`_index.json` din folder conține lista de ani disponibili + count per an.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

BUILDER_VERSION = "0.1.0"


def split_endpoint(endpoint: str, leg: int, date_field: str) -> int:
    """Împarte un endpoint pe an. Returnează numărul total de records procesate."""
    src = ROOT / "data" / "v1" / endpoint / f"legislatura-{leg}.json"
    if not src.exists():
        logging.warning(f"Nu există: {src}")
        return 0

    data = json.loads(src.read_text(encoding="utf-8"))
    items = data.get("data", [])
    if not items:
        return 0

    out_dir = ROOT / "data" / "v1" / endpoint / f"legislatura-{leg}"
    out_dir.mkdir(parents=True, exist_ok=True)

    by_year: dict[str, list] = defaultdict(list)
    for item in items:
        date_str = item.get(date_field) or ""
        year = date_str[:4] if date_str else "necunoscut"
        by_year[year].append(item)

    # Scrie un fișier per an
    year_summary: dict[str, int] = {}
    for year, year_items in sorted(by_year.items()):
        year_items.sort(key=lambda x: x.get(date_field) or "", reverse=True)
        meta = Meta(
            generated_at=datetime.now(UTC),
            source_url=f"split from /v1/{endpoint}/legislatura-{leg}.json",
            scraper_version=BUILDER_VERSION,
            count=len(year_items),
        )
        payload = {
            "meta": meta.model_dump(mode="json"),
            "data": year_items,
        }
        out_path = out_dir / f"{year}.json"
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        year_summary[year] = len(year_items)
        size_kb = out_path.stat().st_size / 1024
        print(
            f"  {endpoint}/legislatura-{leg}/{year}.json: {len(year_items)} records, {size_kb:.1f} KB"
        )

    # Scrie un _index.json cu lista anilor
    idx_meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"split index for /v1/{endpoint}/legislatura-{leg}",
        scraper_version=BUILDER_VERSION,
        count=len(items),
    )
    idx_path = out_dir / "_index.json"
    idx_payload = {
        "meta": idx_meta.model_dump(mode="json"),
        "ani": [
            {"year": y, "count": n, "url": f"{y}.json"} for y, n in sorted(year_summary.items())
        ],
        "full": f"../legislatura-{leg}.json",
    }
    idx_path.write_text(json.dumps(idx_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {idx_path} (index cu {len(year_summary)} ani)")

    return len(items)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=None, help="Legislatură specifică")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    legislaturi = [args.leg] if args.leg else [2016, 2020, 2024]

    # Endpoint -> câmp de dată folosit pentru grupare
    targets = [
        ("interpelari", "data_inregistrare"),
        ("proiecte", "data_inregistrare_cd"),  # fallback la data_prezentare
    ]

    total = 0
    for leg in legislaturi:
        print(f"\n=== Legislatura {leg} ===")
        for endpoint, date_field in targets:
            n = split_endpoint(endpoint, leg, date_field)
            total += n

    print(f"\nOK: {total} records procesate cross-endpoint")
    return 0


if __name__ == "__main__":
    sys.exit(main())
