"""Rulează scraperul de documente comisii.

Storage: data/v1/doc-comisii/all.json (un singur fișier cu toate documentele)

Utilizare:
    python scripts/run_doc_comisii.py                # incremental (1 pagină — ~99 cele mai recente)
    python scripts/run_doc_comisii.py --pages 10     # primele 10 pagini = ~990 docs
    python scripts/run_doc_comisii.py --full         # toate ~870 pagini = ~85.895 docs (durează ore)

NOTĂ: documente comisii au ~85.895 înregistrări totale. Recomandare:
- Daily cron: --pages 1 (incremental — doar cele noi)
- Săptămânal: --pages 10 (siguranță)
- Bootstrap inițial: --full (rulează o singură dată)
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
from scrapers.doc_comisii import scrape_pages  # noqa: E402

SCRAPER_VERSION = "0.1.0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pages", type=int, default=1, help="Număr de pagini de scrappiat (default: 1)"
    )
    parser.add_argument("--full", action="store_true", help="Toate paginile (~870, durează ore)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    out_path = ROOT / "data" / "v1" / "doc-comisii" / "all.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Citim existent
    existing_data: list[dict] = []
    seen_pdf_urls: set[str] = set()
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            existing_data = existing.get("data", [])
            seen_pdf_urls = {d.get("pdf_url", "") for d in existing_data if d.get("pdf_url")}
            print(f"Index existent: {len(seen_pdf_urls)} documente")
        except (json.JSONDecodeError, KeyError):
            pass

    pages = 9999 if args.full else args.pages
    print(f"Scrape doc-comisii: {pages} pagini max...")

    new_items = scrape_pages(max_pages=pages, seen_pdf_urls=seen_pdf_urls)

    if not new_items:
        print("Nicio actualizare.")
        return 0

    new_dicts = [d.model_dump(mode="json", exclude_none=False) for d in new_items]
    all_data = new_dicts + existing_data  # new first

    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url="https://www.cdep.ro/ords/pls/proiecte/upl_com2015.lista",
        scraper_version=SCRAPER_VERSION,
        count=len(all_data),
    )
    payload = {"meta": meta.model_dump(mode="json"), "data": all_data}
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Stats pe tipuri
    types: dict[str, int] = {}
    for d in new_items:
        types[d.tip] = types.get(d.tip, 0) + 1
    print(
        f"OK +{len(new_items)} documente noi. Total: {len(all_data)}.\n"
        f"   Tipuri noi: " + ", ".join(f"{k}={v}" for k, v in types.items())
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
