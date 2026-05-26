"""Rulează scraperul de stenograme.

Storage:
    data/v1/stenograme/legislatura-{leg}/{YYYYMMDD}.json  -- per ședință
    data/v1/stenograme/legislatura-{leg}/_index.json       -- index sumar

Utilizare:
    python scripts/run_stenograme.py                       # leg + an curent, incremental
    python scripts/run_stenograme.py --year 2026
    python scripts/run_stenograme.py --years 2024 2025 2026
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import contextlib  # noqa: E402

from schemas.common import Meta  # noqa: E402
from scrapers.stenograme import scrape_year  # noqa: E402

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
    parser.add_argument("--year", type=int, default=None)
    parser.add_argument("--years", type=int, nargs="+")
    parser.add_argument("--cam", type=int, default=2)
    parser.add_argument("--leg", type=int, default=None)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    years = args.years or [args.year or date.today().year]
    leg = args.leg or detect_legislatura(max(years))

    out_dir = ROOT / "data" / "v1" / "stenograme" / f"legislatura-{leg}"
    out_dir.mkdir(parents=True, exist_ok=True)
    index_path = out_dir / "_index.json"

    # Citim datele deja procesate (incremental)
    existing_dates: set[date] = set()
    if index_path.exists() and not args.full:
        try:
            existing = json.loads(index_path.read_text(encoding="utf-8"))
            for item in existing.get("data", []):
                ds = item.get("session_date")
                if ds:
                    with contextlib.suppress(ValueError):
                        existing_dates.add(date.fromisoformat(ds))
            print(f"Index existent: {len(existing_dates)} stenograme (mod incremental)")
        except (json.JSONDecodeError, KeyError):
            pass

    if args.full:
        print("Mod --full: refetch toate stenogramele.")

    # Scrape ani
    all_new = []
    for year in years:
        print(f"\n=== Anul {year} (cam={args.cam}) ===")
        items = scrape_year(year, legislatura=leg, cam=args.cam, skip_dates=existing_dates)
        all_new.extend(items)
        print(f"  {len(items)} stenograme noi parsate")

    if not all_new:
        print("Nicio actualizare.")
        return 0

    # Salvăm fiecare stenograma ca fișier individual
    for st in all_new:
        ymd = st.session_date.strftime("%Y%m%d")
        detail_path = out_dir / f"{ymd}.json"
        payload = {
            "meta": Meta(
                generated_at=datetime.now(UTC),
                source_url=str(st.source_url),
                scraper_version=SCRAPER_VERSION,
                count=len(st.interventions),
            ).model_dump(mode="json"),
            "data": st.model_dump(mode="json", exclude_none=False),
        }
        detail_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Actualizăm index sumar
    new_summaries = [
        {
            "id": st.id,
            "session_date": st.session_date.isoformat(),
            "cam": st.cam,
            "legislatura": st.legislatura,
            "titlu": st.titlu,
            "n_interventions": len(st.interventions),
            "text_complet_len": st.text_complet_len,
            "detail_url": f"stenograme/legislatura-{leg}/{st.session_date.strftime('%Y%m%d')}.json",
        }
        for st in all_new
    ]
    existing_summaries = []
    if index_path.exists():
        with contextlib.suppress(json.JSONDecodeError, KeyError):
            existing_summaries = json.loads(index_path.read_text(encoding="utf-8")).get("data", [])
    new_dates_set = {s["session_date"] for s in new_summaries}
    merged = [s for s in existing_summaries if s.get("session_date") not in new_dates_set]
    merged.extend(new_summaries)
    merged.sort(key=lambda x: x.get("session_date") or "", reverse=True)

    index_payload = {
        "meta": Meta(
            generated_at=datetime.now(UTC),
            source_url=f"https://www.cdep.ro/ords/pls/steno/steno2015.calendar?cam={args.cam}",
            scraper_version=SCRAPER_VERSION,
            count=len(merged),
        ).model_dump(mode="json"),
        "data": merged,
    }
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nOK +{len(all_new)} stenograme noi. Total în index: {len(merged)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
