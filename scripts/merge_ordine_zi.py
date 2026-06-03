#!/usr/bin/env python3
"""
Merge split ordine-zi files back into a single JSON:
- sesiuni.csv → session metadata
- items.csv → agenda items (docs linked via item_id)
- docs.csv → documents for items
- entities.json → entities for items

Reconstructs original schema with session.items[].docs and .entities fields.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from collections import defaultdict


def main():
    output_dir = Path("data/v1/ordine-zi")
    sesiuni_file = output_dir / "sesiuni.csv"
    items_file = output_dir / "items.csv"
    docs_file = output_dir / "docs.csv"
    entities_file = output_dir / "entities.json"

    # Verify all files exist
    for f in [sesiuni_file, items_file, docs_file, entities_file]:
        if not f.exists():
            print(f"Error: {f.name} not found", file=sys.stderr)
            sys.exit(1)

    # Load sessions
    sessions_by_id = {}
    with open(sesiuni_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["id"]
            if sid not in sessions_by_id:
                sessions_by_id[sid] = {
                    "id": sid,
                    "session_date": row["session_date"],
                    "session_date_end": row["session_date_end"],
                    "legislatura": int(row["legislatura"]),
                    "cam": int(row["cam"]),
                    "titlu": row["titlu"],
                    "data_aprobare": row["data_aprobare"],
                    "pdf_url": row["pdf_url"] or None,
                    "items": [],
                }

    # Load items
    items_by_id = {}
    items_by_session = defaultdict(list)
    with open(items_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            item_id = f"{row['sesiune_id']}_{row['item_index'].zfill(3)}"
            item = {
                "pozitie": int(row["pozitie"]) if row["pozitie"] else None,
                "nr_inregistrare": row["nr_inregistrare"] or None,
                "idp": int(row["idp"]) if row["idp"] else None,
                "descriere": row["descriere"],
                "doc_pdf_url": row["doc_pdf_url"] or None,
                "ozitm": int(row["ozitm"]) if row["ozitm"] else None,
                "docs": [],
                "entities": {},
            }
            items_by_id[item_id] = item
            items_by_session[row["sesiune_id"]].append((int(row["item_index"]), item))

    # Load docs
    docs_by_item = defaultdict(list)
    with open(docs_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = {
                "data": row["data"],
                "titlu": row["titlu"],
                "pdf_url": row["pdf_url"],
                "sursa": row["sursa"],
            }
            docs_by_item[row["item_id"]].append(doc)

    # Load entities
    with open(entities_file) as f:
        entities_dict = json.load(f)

    # Link docs and entities to items
    for item_id, item in items_by_id.items():
        item["docs"] = docs_by_item.get(item_id, [])
        item["entities"] = entities_dict.get(item_id, {})

    # Build sessions with items
    for session_id, items_with_index in items_by_session.items():
        # Sort by item_index
        items_with_index.sort(key=lambda x: x[0])
        sessions_by_id[session_id]["items"] = [item for _, item in items_with_index]

    # Build output
    output = {
        "meta": {
            "generated_at": "2026-06-03T00:00:00.000000Z",
            "source_url": "https://www.cdep.ro/ords/pls/caseta/ecaseta2015.OrdineZi (leg=2024)",
            "scraper_version": "0.1.0",
            "count": len(sessions_by_id),
        },
        "data": list(sessions_by_id.values()),
    }

    # Write output
    output_file = output_dir / "legislatura-2024-merged.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Verify roundtrip
    total_items = sum(len(s["items"]) for s in output["data"])
    total_docs = sum(len(item["docs"]) for s in output["data"] for item in s["items"])
    total_entities = sum(1 for s in output["data"] for item in s["items"] if item.get("entities"))

    print(f"✓ Merged split files")
    print(f"  Sessions: {len(sessions_by_id)}")
    print(f"  Items: {total_items}")
    print(f"  Docs: {total_docs}")
    print(f"  Entities: {total_entities}")
    print(f"  Output: {output_file}")
    print()

    size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"  {output_file.name:30s} {size_mb:8.2f} MB")


if __name__ == "__main__":
    main()
