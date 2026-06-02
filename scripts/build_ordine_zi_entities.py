"""Enrich ordine-zi data with extracted entities.

Reads data/v1/ordine-zi/legislatura-{leg}.json, adds an `entities` field
to every item in-place, and writes the file back.

Usage:
    python scripts/build_ordine_zi_entities.py --leg 2024
    python scripts/build_ordine_zi_entities.py --leg 2024 --dry-run
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.entities_ordine_zi import extract_entities


def _enrich_file(path: Path, dry_run: bool, sample: int | None) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    sessions = data.get("data", [])

    if sample:
        sessions_to_show = random.sample(sessions, min(sample, len(sessions)))
    else:
        sessions_to_show = sessions

    total_items = 0
    unknown_type = 0

    for session in sessions:
        for item in session.get("items", []):
            descriere = item.get("descriere", "")
            entities = extract_entities(descriere)
            total_items += 1
            if entities.item_type is None:
                unknown_type += 1
            item["entities"] = entities.model_dump(mode="json", exclude_none=True)

    if dry_run:
        print(f"\n=== DRY RUN — {path.name} ===")
        print(f"Total items: {total_items}  |  Unknown type: {unknown_type} ({unknown_type/total_items:.1%})")
        print()
        for session in sessions_to_show:
            print(f"── {session['session_date']}  {session.get('titlu', '')[:70]}")
            for item in session.get("items", [])[:5]:
                ent = item.get("entities", {})
                print(
                    f"   [{ent.get('item_type', '?'):25s}] "
                    f"action={ent.get('action', '-'):28s} "
                    f"law={ent.get('law_category', '-'):15s} "
                    f"flags={ent.get('flags', [])}"
                )
                if ent.get("referenced_acts"):
                    for act in ent["referenced_acts"]:
                        print(f"      act: {act['act_type']} nr.{act['nr']}/{act.get('year', '?')}")
                if ent.get("commissions"):
                    print(f"      commissions: {ent['commissions']}")
                if ent.get("subject"):
                    print(f"      subject: {ent['subject'][:100]}")
            print()
        return

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"Wrote {path}  ({total_items} items enriched, "
        f"{unknown_type} unknown type = {unknown_type/total_items:.1%})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich ordine-zi items with extracted entities.")
    parser.add_argument("--leg", type=int, default=2024, help="Legislature year (default: 2024)")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing")
    parser.add_argument("--sample", type=int, default=10, help="Sessions to show in dry-run (default: 10)")
    args = parser.parse_args()

    path = Path("data/v1/ordine-zi") / f"legislatura-{args.leg}.json"
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    _enrich_file(path, dry_run=args.dry_run, sample=args.sample if args.dry_run else None)


if __name__ == "__main__":
    main()
