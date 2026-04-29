"""Verificare rapidă a feed-urilor generate."""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# JSON Feed
jf = json.loads((ROOT / "data" / "v1" / "feed.json").read_text(encoding="utf-8"))
print(f'JSON Feed: {len(jf["items"])} items')
print(f'  version: {jf["version"]}')
print(f'  title: {jf["title"]}')
print()
print("Primele 10 evenimente:")
for i in jf["items"][:10]:
    tag = i["tags"][0] if i.get("tags") else "?"
    print(f'  {i["date_published"][:10]} | {tag:12s} | {i["title"][:80]}')

# Atom XML validity
try:
    ET.parse(ROOT / "data" / "v1" / "feed.atom")
    print("\nAtom XML: VALID")
except ET.ParseError as e:
    print(f"\nAtom XML: INVALID — {e}")
    sys.exit(1)
