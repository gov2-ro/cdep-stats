"""Verifică starea bootstrap-ului pentru legislatura 2016."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v1"

print("Status legislatura 2016 (perioada 2016-12-21 → 2020-12-20):")
print()

# Deputați
f = DATA / "deputati" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  deputati:    {n:>5} ({f.stat().st_size / 1024:.1f} KB)")
else:
    print("  deputati:    LIPSĂ")

# Sancțiuni
f = DATA / "sanctiuni" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  sanctiuni:   {n:>5}")
else:
    print("  sanctiuni:   LIPSĂ")

# Comisii
f = DATA / "comisii" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  comisii:     {n:>5}")
else:
    print("  comisii:     LIPSĂ")

# Voturi
f = DATA / "voturi" / "2016" / "_index.json"
if f.exists():
    items = json.loads(f.read_text(encoding="utf-8"))["data"]
    n = len(items)
    if items:
        first = items[-1]["timestamp"][:10]
        last = items[0]["timestamp"][:10]
        print(f"  voturi:      {n:>5}  ({first} → {last})")
else:
    print("  voturi:      LIPSĂ")

# Interpelari
f = DATA / "interpelari" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  interpelari: {n:>5} ({f.stat().st_size / 1024 / 1024:.1f} MB)")
else:
    print("  interpelari: LIPSĂ")

# Proiecte
f = DATA / "proiecte" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  proiecte:    {n:>5} ({f.stat().st_size / 1024 / 1024:.1f} MB)")
else:
    print("  proiecte:    LIPSĂ")

# Motiuni
f = DATA / "motiuni" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  motiuni:     {n:>5}")
else:
    print("  motiuni:     LIPSĂ")

# Amendamente
f = DATA / "amendamente" / "legislatura-2016.json"
if f.exists():
    n = len(json.loads(f.read_text(encoding="utf-8"))["data"])
    print(f"  amendamente: {n:>5}")
else:
    print("  amendamente: LIPSĂ (build după proiecte)")
