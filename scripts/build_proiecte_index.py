"""Build compact proiecte lookup indexes for client-side bill cross-linking.

Reads all proiecte year files (including necunoscut.json) and emits:

  data/v1/stats/proiecte-index-{leg}.json   — thin bill index (846 KB for 2024)
      {cdep_idp, nr_inregistrare, nr_camera_deputati, titlu, stadiu, tip, source_url}
      Used by vot.html to resolve bill title/link from a vote's descriere.

  data/v1/stats/bill-vote-map-{leg}.json    — tiny bill→vote join (~10 KB)
      { "<cdep_idp>": {cdep_idv, descriere, counts} }
      Used by proiect.html detail view to show/link the matching vote
      without loading the full 200 KB voturi index.

Usage:
    python scripts/build_proiecte_index.py --leg 2024
    python scripts/build_proiecte_index.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

ALL_LEGS = [2024, 2020]

KEEP = ("cdep_idp", "nr_inregistrare", "nr_camera_deputati", "titlu", "stadiu", "tip", "source_url")


def _extract_key(text: str | None) -> str | None:
    """Return 'NNN/YYYY' from a bill number or vote description string."""
    m = re.search(r"(\d{2,4}/\d{4})", text or "")
    return m.group(1) if m else None


def _build_vote_lookup(base: Path, leg: int) -> dict[str, dict]:
    """Return {bill_key: {cdep_idv, descriere, counts}} from voturi/_index."""
    idx_path = base / f"voturi/{leg}/_index.json"
    if not idx_path.is_file():
        return {}
    try:
        votes = json.loads(idx_path.read_text(encoding="utf-8")).get("data", [])
    except (OSError, json.JSONDecodeError):
        return {}
    lookup: dict[str, dict] = {}
    for v in votes:
        key = _extract_key(v.get("descriere"))
        if key and key not in lookup:
            lookup[key] = {
                "cdep_idv": v.get("cdep_idv"),
                "descriere": v.get("descriere"),
                "counts": v.get("counts"),
            }
    return lookup


def build_leg(leg: int, root: Path = ROOT) -> int:
    src_dir = root / "data" / "v1" / "proiecte" / f"legislatura-{leg}"
    if not src_dir.is_dir():
        print(f"SKIP leg {leg}: {src_dir} not found")
        return 0

    base = root / "data" / "v1"
    vote_lookup = _build_vote_lookup(base, leg)

    items: list[dict] = []
    bill_vote_map: dict[str, dict] = {}  # cdep_idp (str) → vote info

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
            # Try to match a vote by bill number
            key = _extract_key(p.get("nr_inregistrare")) or _extract_key(p.get("nr_camera_deputati"))
            if key and key in vote_lookup:
                idp_str = str(p["cdep_idp"])
                bill_vote_map[idp_str] = vote_lookup[key]
            items.append(slim)

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Thin bill index
    idx_path = out_dir / f"proiecte-index-{leg}.json"
    payload = {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "legislatura": leg,
            "count": len(items),
        },
        "data": items,
    }
    idx_path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK leg {leg}: {len(items)} proiecte → {idx_path} ({idx_path.stat().st_size // 1024} KB)")

    # 2. Tiny bill→vote map
    map_path = out_dir / f"bill-vote-map-{leg}.json"
    map_path.write_text(json.dumps(bill_vote_map, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"   bill-vote-map: {len(bill_vote_map)} matched → {map_path} ({map_path.stat().st_size // 1024} KB)")

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
