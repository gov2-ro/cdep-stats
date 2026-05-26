"""Rulează scraperul de proiecte legislative și salvează JSON.

Storage: data/v1/proiecte/legislatura-{leg}.json (un fișier per legislatură,
toți anii inclusi).

Utilizare:
    python scripts/run_proiecte.py                          # incremental, leg + anul curent
    python scripts/run_proiecte.py --year 2025
    python scripts/run_proiecte.py --years 2024 2025 2026
    python scripts/run_proiecte.py --year 2025 --leg 2024
    python scripts/run_proiecte.py --year 2025 --cam 2
    python scripts/run_proiecte.py --full                   # refetch complet (recomandat săptămânal
                                                            # pt actualizare stadii proiecte vechi)

NOTĂ: implicit, scriptul sare peste proiectele deja salvate (incremental).
Cu ``--full`` refetchează tot — necesar dacă vrem să prindem schimbări de stadiu
(timeline, vot final, promulgare) pentru proiecte cunoscute.
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

from schemas.common import Meta  # noqa: E402
from scrapers.proiecte import scrape_year  # noqa: E402

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
    parser.add_argument("--year", type=int, default=None, help="An (default: anul curent)")
    parser.add_argument("--years", type=int, nargs="+", help="Multiple ani: --years 2024 2025 2026")
    parser.add_argument("--cam", type=int, default=2, help="Cameră (1=Senat, 2=CD, default: 2)")
    parser.add_argument(
        "--leg", type=int, default=None, help="Legislatura (default: detect din year)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Refetch complet (ignoră skip_ids). Default: incremental.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    years = args.years or [args.year or date.today().year]
    leg = args.leg or detect_legislatura(max(years))

    out_path = ROOT / "data" / "v1" / "proiecte" / f"legislatura-{leg}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Citim existent (idempotent)
    existing_ids: set[int] = set()
    existing_data: list[dict] = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_data = existing.get("data", [])
            existing_ids = {item["cdep_idp"] for item in existing_data}
            print(f"Index existent: {len(existing_ids)} proiecte")
        except (json.JSONDecodeError, KeyError):
            pass

    # Scrape ani — implicit incremental (sare peste idp deja procesate)
    skip = set() if args.full else existing_ids
    if args.full:
        print("Mod --full: refetch toate proiectele (poate dura ore).")
    else:
        print(f"Mod incremental: skip {len(existing_ids)} proiecte cunoscute.")

    all_new = []
    for year in years:
        print(f"\n=== Anul {year} (cam={args.cam}) ===")
        items = scrape_year(year, legislatura=leg, cam=args.cam, skip_ids=skip)
        print(f"  {len(items)} noi parsate")
        all_new.extend(items)

    if not all_new:
        print("Nicio actualizare.")
        return 0

    # Merge cu existent — în modul --full overwrite-uim doar idp-urile re-fetched
    new_dicts = [i.model_dump(mode="json", exclude_none=False) for i in all_new]
    if args.full:
        # Overwrite idp-urile re-fetched, păstrează restul
        new_ids = {d["cdep_idp"] for d in new_dicts}
        all_data = [d for d in existing_data if d.get("cdep_idp") not in new_ids] + new_dicts
    else:
        all_data = existing_data + new_dicts
    # Sortez după nr_camera_deputati descrescător (proiectele recente primele)
    all_data.sort(
        key=lambda x: x.get("data_inregistrare_cd") or x.get("data_prezentare") or "",
        reverse=True,
    )

    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"https://www.cdep.ro/ords/pls/proiecte/upl_pck2015.lista?anp={max(years)}&cam={args.cam}",
        scraper_version=SCRAPER_VERSION,
        count=len(all_data),
    )
    payload = {"meta": meta.model_dump(mode="json"), "data": all_data}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nOK +{len(all_new)} noi. Total în fișier: {len(all_data)}.")
    print(f"   {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
