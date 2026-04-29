"""Verificare rapidă a fișierului interpelari (count, distribuție ani, statistici)."""

import json
import sys
from collections import Counter
from pathlib import Path

f = Path("data/v1/interpelari/legislatura-2024.json")
if not f.exists():
    print(f"Nu există: {f}")
    sys.exit(1)

print(f"File size: {f.stat().st_size / 1024 / 1024:.2f} MB")

data = json.loads(f.read_text(encoding="utf-8"))
items = data["data"]
print(f"Total interpelări: {len(items):,}")

years = Counter()
for i in items:
    dt = i.get("data_inregistrare") or ""
    if dt:
        years[dt[:4]] += 1

print("\nPe ani:")
for y in sorted(years):
    print(f"  {y}: {years[y]:,}")

with_resp = sum(1 for i in items if i.get("raspuns_primit"))
print(f"\nCu raspuns primit: {with_resp:,} ({100 * with_resp / len(items):.1f}%)")

dest = Counter(i.get("destinatar", "?") for i in items)
print("\nTop 10 destinatari:")
for d, n in dest.most_common(10):
    print(f"  {n:5d}  {d[:70]}")
