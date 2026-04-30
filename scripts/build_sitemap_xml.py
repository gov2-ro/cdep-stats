"""Generează `sitemap.xml` pentru SEO + crawlere.

Listează toate paginile HTML statice + un sample din endpoint-urile JSON principale.
Output: `sitemap.xml` în root-ul repo-ului (servit la `/sitemap.xml` pe Pages).

Crawlere ca Google, Bing, DuckDuckGo folosesc sitemap-ul pentru a descoperi
paginile fără a parcurge link-uri inline.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://endimion2k.github.io/cdep-api-poc"


def main() -> int:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    urls: list[tuple[str, str, str]] = []  # (loc, lastmod, priority)

    # Pagini principale
    static_pages = [
        ("/", "1.0"),
        ("/index.html", "1.0"),
        ("/search.html", "0.9"),
        ("/status.html", "0.7"),
        ("/docs/swagger.html", "0.6"),
        ("/deputat.html", "0.5"),
        ("/proiect.html", "0.5"),
        ("/vot.html", "0.5"),
        ("/motiune.html", "0.5"),
        ("/sanctiune.html", "0.5"),
    ]
    for path, prio in static_pages:
        urls.append((BASE_URL + path, today, prio))

    # Profile pages — top 50 deputați (cel mai probabil căutați)
    dep_file = ROOT / "data" / "v1" / "deputati" / "legislatura-2024.json"
    if dep_file.exists():
        try:
            data = json.loads(dep_file.read_text(encoding="utf-8"))
            for d in data.get("data", [])[:50]:
                idm = d.get("cdep_idm")
                if idm:
                    urls.append((f"{BASE_URL}/deputat.html?id={idm}", today, "0.4"))
        except (json.JSONDecodeError, KeyError):
            pass

    # Top 30 proiecte cu cele mai multe amendamente (cele mai vizibile public)
    am_file = ROOT / "data" / "v1" / "amendamente" / "legislatura-2024.json"
    if am_file.exists():
        try:
            data = json.loads(am_file.read_text(encoding="utf-8"))
            for p in data.get("data", [])[:30]:
                idp = p.get("cdep_idp")
                if idp:
                    urls.append((f"{BASE_URL}/proiect.html?idp={idp}", today, "0.4"))
        except (json.JSONDecodeError, KeyError):
            pass

    # Endpoint-uri JSON principale
    json_endpoints = [
        "/data/v1/deputati/legislatura-2024.json",
        "/data/v1/voturi/2024/_index.json",
        "/data/v1/sanctiuni/legislatura-2024.json",
        "/data/v1/interpelari/legislatura-2024.json",
        "/data/v1/comisii/legislatura-2024.json",
        "/data/v1/proiecte/legislatura-2024.json",
        "/data/v1/amendamente/legislatura-2024.json",
        "/data/v1/motiuni/legislatura-2024.json",
        "/data/v1/feed.atom",
        "/data/v1/feed.json",
        "/data/v1/status.json",
        "/api/openapi.yaml",
    ]
    for path in json_endpoints:
        urls.append((BASE_URL + path, today, "0.3"))

    # Build XML
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, lastmod, prio in urls:
        # Escape & în URL-uri (ex. ?idp=N&leg=2024 nu e cazul aici, dar de siguranță)
        loc_escaped = loc.replace("&", "&amp;")
        lines.append(
            f"  <url>\n"
            f"    <loc>{loc_escaped}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <priority>{prio}</priority>\n"
            f"  </url>"
        )
    lines.append("</urlset>")

    out_path = ROOT / "sitemap.xml"
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"OK: {len(urls)} URL-uri în sitemap.xml")
    print(f"   {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
