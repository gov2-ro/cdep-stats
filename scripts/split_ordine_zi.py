#!/usr/bin/env python3
"""
Split legislatura-2024.json into modular CSV + JSON files:
- sesiuni.csv: session metadata (id, dates, legislature, chamber, title, approval_date, pdf_url)
- items.csv: agenda items (sesiune_id, item_index, pozitie, nr_inregistrare, idp, descriere, doc_pdf_url, ozitm, num_docs)
- docs.csv: document references (item_id, data, titlu, pdf_url, sursa)
- entities.json: keyed by item_id (item_type, flags, referenced_acts, commissions, commission_slugs, subject, institutions)

Item IDs are: {session_id}_{item_index:03d} for cross-linking docs and entities.
Sessions are deduplicated by ID (original JSON has ~60 duplicates).
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def main():
    input_file = Path("data/v1/ordine-zi/legislatura-2024.json")
    output_dir = Path("data/v1/ordine-zi")

    if not input_file.exists():
        print(f"Error: {input_file} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_file) as f:
        data = json.load(f)

    meta = data["meta"]
    sessions = data["data"]

    # Merge duplicate sessions (combine items, keep session metadata from first occurrence)
    sessions_by_id = {}
    for session in sessions:
        sid = session["id"]
        if sid not in sessions_by_id:
            sessions_by_id[sid] = session
        else:
            # Merge items from duplicate sessions
            sessions_by_id[sid]["items"].extend(session["items"])

    unique_sessions = list(sessions_by_id.values())

    # Open output files with context managers
    sesiuni_file = output_dir / "sesiuni.csv"
    items_file = output_dir / "items.csv"
    docs_file = output_dir / "docs.csv"
    entities_file = output_dir / "entities.json"

    entities_dict: dict = {}

    with open(sesiuni_file, "w", newline="") as f_sesiuni, \
         open(items_file, "w", newline="") as f_items, \
         open(docs_file, "w", newline="") as f_docs:

        sesiuni_writer = csv.writer(f_sesiuni)
        items_writer = csv.writer(f_items)
        docs_writer = csv.writer(f_docs)

        # Write headers
        sesiuni_writer.writerow(
            ["id", "session_date", "session_date_end", "legislatura", "cam", "titlu", "data_aprobare", "pdf_url"]
        )
        items_writer.writerow(
            ["sesiune_id", "item_index", "pozitie", "nr_inregistrare", "idp", "descriere", "doc_pdf_url", "ozitm", "num_docs"]
        )
        docs_writer.writerow(["item_id", "data", "titlu", "pdf_url", "sursa"])

        # Process sessions
        for session in unique_sessions:
            session_id = session["id"]

            # Write session metadata
            sesiuni_writer.writerow(
                [
                    session_id,
                    session["session_date"],
                    session["session_date_end"],
                    session["legislatura"],
                    session["cam"],
                    session["titlu"],
                    session["data_aprobare"],
                    session.get("pdf_url") or "",
                ]
            )

            # Process items
            for item_index, item in enumerate(session["items"]):
                # Create item ID: sesiune_id + index
                item_id = f"{session_id}_{item_index:03d}"

                # Write item (without entities)
                items_writer.writerow(
                    [
                        session_id,
                        item_index,
                        item.get("pozitie") or "",
                        item.get("nr_inregistrare") or "",
                        item.get("idp") or "",
                        item.get("descriere") or "",
                        item.get("doc_pdf_url") or "",
                        item.get("ozitm") or "",
                        len(item.get("docs", [])),
                    ]
                )

                # Write docs for this item
                for doc in item.get("docs", []):
                    docs_writer.writerow(
                        [
                            item_id,
                            doc.get("data") or "",
                            doc.get("titlu") or "",
                            doc.get("pdf_url") or "",
                            doc.get("sursa") or "",
                        ]
                    )

                # Store entities
                entities_dict[item_id] = item.get("entities", {})

    # Write entities as JSON
    with open(entities_file, "w") as f:
        json.dump(entities_dict, f, indent=2, ensure_ascii=False)

    # Print stats
    total_items = sum(len(s["items"]) for s in unique_sessions)
    total_docs = sum(len(doc) for s in unique_sessions for item in s["items"] for doc in [item.get("docs", [])])
    deduped = len(sessions) - len(unique_sessions)

    print(f"✓ Split {input_file.name}")
    print(f"  Sessions: {len(sessions)} (deduplicated {deduped}) → {sesiuni_file.name}")
    print(f"  Items: {total_items} → {items_file.name}")
    print(f"  Docs: {total_docs} → {docs_file.name}")
    print(f"  Entities: {len(entities_dict)} → {entities_file.name}")
    print()

    # Show file sizes
    for f in [sesiuni_file, items_file, docs_file, entities_file]:
        size_mb = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:20s} {size_mb:8.2f} MB")

    orig_size = input_file.stat().st_size / (1024 * 1024)
    new_size = sum(f.stat().st_size for f in [sesiuni_file, items_file, docs_file, entities_file]) / (1024 * 1024)
    reduction = (1 - new_size / orig_size) * 100

    print()
    print(f"Original:  {orig_size:.2f} MB")
    print(f"Split:     {new_size:.2f} MB")
    print(f"Reduction: {reduction:.1f}%")


if __name__ == "__main__":
    main()
