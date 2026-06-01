"""Build a compact proiecte lookup index for client-side bill cross-linking.

Reads all proiecte year files (including necunoscut.json) and emits a thin
index with just the fields needed to look up a bill by nr_inregistrare and
link to proiect.html or cdep.ro.

Output: data/v1/stats/proiecte-index-{leg}.json

Usage:
    python scripts/build_proiecte_index.py --leg 2024
    python scripts/build_proiecte_index.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ALL_LEGS = [2024, 2020]

KEEP = ("cdep_idp", "nr_inregistrare", "nr_camera_deputati", "titlu", "stadiu", "tip", "source_url")


def build_leg(leg: int, root: Path = ROOT) -> int:
    src_dir = root / "data" / "v1" / "proiecte" / f"legislatura-{leg}"
    if not src_dir.is_dir():
        print(f"SKIP leg {leg}: {src_dir} not found")
        return 0

    items: list[dict] = []
    for path in sorted(src_dir.glob("*.json")):
        if path.name == "_index.json":
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"  WARN {path.name}: {e}")
            continue
        data = doc.get("data", doc) if isinstance(doc, dict) else doc
        if not isinstance(data, list):
            continue
        for p in data:
            slim = {k: p.get(k) for k in KEEP}
            items.append(slim)

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"proiecte-index-{leg}.json"
    payload = {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "legislatura": leg,
            "count": len(items),
        },
        "data": items,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"OK leg {leg}: {len(items)} proiecte → {out_path} ({size_kb} KB)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    legs = ALL_LEGS if args.all else [args.leg]
    for leg in legs:
        build_leg(leg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
