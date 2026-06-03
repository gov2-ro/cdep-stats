#!/usr/bin/env python3
"""Build lightweight slims for home page — avoid loading 35+ MB on index.html."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEG = "2024"


def build_deputati_slim() -> None:
    """Extract {id, current_party, activitate_*} from full deputati file."""
    src = ROOT / "data" / "v1" / "deputati" / f"legislatura-{LEG}.json"
    if not src.exists():
        print(f"  ⚠ {src.name} not found")
        return

    with open(src) as f:
        data = json.load(f)

    # Extract only fields needed for home page: party bars + indicators
    slim = [
        {
            "id": d.get("cdep_idm"),
            "current_party": d.get("current_party"),
            "activitate_legi_promulgate": d.get("activitate_legi_promulgate", 0),
            "activitate_intrebari_interpelari": d.get("activitate_intrebari_interpelari", 0),
            "activitate_propuneri_legislative": d.get("activitate_propuneri_legislative", 0),
        }
        for d in (data.get("data") or [])
        if d.get("cdep_idm")
    ]

    out = ROOT / "data" / "v1" / "stats" / f"home-deputati-slim-{LEG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump({"data": slim, "meta": {"generated_at": datetime.now(UTC).isoformat()}}, f, indent=2)
    print(f"  → {out.name} ({len(slim)} deputies, {out.stat().st_size / 1024:.1f} KB)")


def build_agenda_latest() -> None:
    """Extract latest session + top 7 items from full ordine-zi file."""
    src = ROOT / "data" / "v1" / "ordine-zi" / f"legislatura-{LEG}.json"
    if not src.exists():
        print(f"  ⚠ {src.name} not found")
        return

    with open(src) as f:
        data = json.load(f)

    sessions = data.get("data") or []
    if not sessions:
        print("  ⚠ No sessions found in ordine-zi")
        return

    # Sort by session_date descending to get latest
    sorted_sessions = sorted(sessions, key=lambda s: (s.get("session_date") or ""), reverse=True)
    latest = sorted_sessions[0]

    # Extract top 7 items
    items = (latest.get("items") or [])[:7]

    slim = {
        "session_date": latest.get("session_date"),
        "session_date_end": latest.get("session_date_end"),
        "titlu": latest.get("titlu"),
        "items": [
            {
                "pozitie": it.get("pozitie"),
                "descriere": it.get("descriere"),
            }
            for it in items
        ],
    }

    out = ROOT / "data" / "v1" / "stats" / f"home-agenda-latest-{LEG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump({"data": slim, "meta": {"generated_at": datetime.now(UTC).isoformat()}}, f, indent=2)
    print(f"  → {out.name} ({len(items)} items, {out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    print("Building home page slims...")
    build_deputati_slim()
    build_agenda_latest()
    print("Done.")
