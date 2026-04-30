"""Verifică datele de moțiuni din toate legislaturile."""

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for leg in [2024, 2020, 2016]:
    f = ROOT / "data" / "v1" / "motiuni" / f"legislatura-{leg}.json"
    if not f.exists():
        continue
    d = json.loads(f.read_text(encoding="utf-8"))
    items = d["data"]
    print(f"\n=== Legislatura {leg}: {len(items)} moțiuni ===")

    by_tip = Counter(m.get("tip", "?") for m in items)
    by_rez = Counter(m.get("rezultat", "?") for m in items)
    print(f"  Pe tip: {dict(by_tip)}")
    print(f"  Pe rezultat: {dict(by_rez)}")

    print("\n  Top 5 cele mai recente:")
    for m in items[:5]:
        print(
            f"    {m.get('data_inregistrare', '?')} | "
            f"{m.get('tip', '?'):8s} | "
            f"{m.get('rezultat', '?'):14s} | "
            f"{m.get('titlu', '?')[:75]}"
        )
