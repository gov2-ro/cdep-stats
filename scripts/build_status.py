"""Generează `data/v1/status.json` cu metadate despre starea API-ului.

Util pentru jurnaliști / dezvoltatori care vor să știe:
- Când a rulat ultima dată cron-ul?
- Cât timp a durat?
- Câte records sunt în fiecare endpoint?
- Care e prospețimea datelor (max generated_at)?

Output: `data/v1/status.json` cu:
{
  "generated_at": "...",
  "build_version": "0.2.0",
  "endpoints": {
    "deputati": {"records": 689, "files": 2, "size_mb": 1.4, "freshness": "..."},
    ...
  },
  "totals": {"records": 38000, "files": 4500, "size_mb": 220},
  "scraper_versions": {...}
}
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v1"

BUILD_VERSION = "0.2.0"


def collect_endpoint_status(name: str, pattern: str) -> dict:
    """Adună statistici pentru un endpoint din toate fișierele care match pattern-ul."""
    files = list(DATA.glob(pattern))
    if not files:
        return {"records": 0, "files": 0, "size_mb": 0.0, "freshness": None}

    total_records = 0
    total_size = 0
    freshness: str | None = None
    scraper_versions: set[str] = set()

    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, KeyError):
            continue
        items = d.get("data", [])
        total_records += len(items) if isinstance(items, list) else 0
        total_size += f.stat().st_size

        meta = d.get("meta", {})
        gen_at = meta.get("generated_at")
        if gen_at and (freshness is None or gen_at > freshness):
            freshness = gen_at
        sv = meta.get("scraper_version")
        if sv:
            scraper_versions.add(sv)

    return {
        "records": total_records,
        "files": len(files),
        "size_mb": round(total_size / 1024 / 1024, 2),
        "freshness": freshness,
        "scraper_versions": sorted(scraper_versions),
    }


def main() -> int:
    print("Generating status.json...")

    endpoints = {
        "deputati": collect_endpoint_status("deputati", "deputati/legislatura-*.json"),
        "voturi_index": collect_endpoint_status("voturi_index", "voturi/*/_index.json"),
        "voturi_per_vot": collect_endpoint_status("voturi_per_vot", "voturi/*/[0-9]*.json"),
        "sanctiuni": collect_endpoint_status("sanctiuni", "sanctiuni/legislatura-*.json"),
        "interpelari": collect_endpoint_status("interpelari", "interpelari/legislatura-*.json"),
        "comisii": collect_endpoint_status("comisii", "comisii/legislatura-*.json"),
        "proiecte": collect_endpoint_status("proiecte", "proiecte/legislatura-*.json"),
        "amendamente": collect_endpoint_status("amendamente", "amendamente/legislatura-*.json"),
        "motiuni": collect_endpoint_status("motiuni", "motiuni/legislatura-*.json"),
        "ordine_zi": collect_endpoint_status("ordine_zi", "ordine-zi/legislatura-*.json"),
        "declaratii": collect_endpoint_status("declaratii", "declaratii/legislatura-*.json"),
        "stenograme": collect_endpoint_status("stenograme", "stenograme/legislatura-*/_index.json"),
        "doc_comisii": collect_endpoint_status("doc_comisii", "doc-comisii/all.json"),
    }

    # Totals
    total_records = sum(e["records"] for e in endpoints.values())
    total_files = sum(e["files"] for e in endpoints.values())
    total_size = sum(e["size_mb"] for e in endpoints.values())

    # Max freshness across all endpoints
    all_freshness = [e["freshness"] for e in endpoints.values() if e["freshness"]]
    max_freshness = max(all_freshness) if all_freshness else None

    status = {
        "generated_at": datetime.now(UTC).isoformat(),
        "build_version": BUILD_VERSION,
        "data_freshness": max_freshness,
        "totals": {
            "records": total_records,
            "files": total_files,
            "size_mb": round(total_size, 2),
        },
        "endpoints": endpoints,
        "infrastructure": {
            "host": "GitHub Pages",
            "scraper": "self-hosted runner (Windows, RO)",
            "schedule": "daily 04:00 UTC",
            "encoding_handling": "ISO-8859-2 + truststore SSL legacy adapter",
        },
        "links": {
            "repo": "https://github.com/Endimion2k/cdep-api-poc",
            "swagger": "https://endimion2k.github.io/cdep-api-poc/docs/swagger.html",
            "search": "https://endimion2k.github.io/cdep-api-poc/search.html",
            "feed_atom": "https://endimion2k.github.io/cdep-api-poc/data/v1/feed.atom",
        },
    }

    out_path = DATA / "status.json"
    out_path.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  → {out_path} ({out_path.stat().st_size:,} bytes)")
    print(f"  Total: {total_records:,} records · {total_files:,} files · {total_size:.1f} MB")
    print(f"  Freshness: {max_freshness}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
