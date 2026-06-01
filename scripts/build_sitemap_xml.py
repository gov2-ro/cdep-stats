"""Generează `web/sitemap.xml` pentru SEO + crawlere.

Listează toate paginile HTML + profiluri individuale (deputați, partide, voturi recente).
Output: `web/sitemap.xml` (inclusă în deploy via build_web.py).

Rulare:
    python scripts/build_sitemap_xml.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://lab.gov2.ro/cdep"


def main() -> int:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    urls: list[tuple[str, str, str]] = []  # (loc, lastmod, priority)

    # Static pages — all HTML files in web/
    static_pages = [
        ("index.html",               "1.0"),
        ("avere.html",               "0.9"),
        ("deputati-activitate.html", "0.9"),
        ("comisii.html",             "0.9"),
        ("interpelari-stats.html",   "0.9"),
        ("voturi.html",              "0.9"),
        ("proiecte-stats.html",      "0.9"),
        ("proiect.html",             "0.8"),
        ("motiuni.html",             "0.8"),
        ("ordine-zi.html",           "0.8"),
        ("interese.html",            "0.8"),
        ("partide.html",             "0.9"),
        ("judete.html",              "0.8"),
        ("deputati-avere.html",      "0.8"),
    ]
    for path, prio in static_pages:
        urls.append((f"{BASE_URL}/{path}", today, prio))

    # All deputy profiles
    dep_file = ROOT / "data" / "v1" / "deputati" / "legislatura-2024.json"
    if dep_file.exists():
        try:
            data = json.loads(dep_file.read_text(encoding="utf-8"))
            for d in data.get("data", []):
                idm = d.get("cdep_idm")
                if idm:
                    urls.append((f"{BASE_URL}/deputat.html?id={idm}&leg=2024", today, "0.6"))
        except (json.JSONDecodeError, KeyError):
            pass

    # All party profiles
    parties = set()
    dep_file2 = ROOT / "data" / "v1" / "deputati" / "legislatura-2024.json"
    if dep_file2.exists():
        try:
            data = json.loads(dep_file2.read_text(encoding="utf-8"))
            PARTY_MAP = [
                ("social democrat", "PSD"), ("national liberal", "PNL"),
                ("salvati romania", "USR"), ("unirea romanilor", "AUR"),
                ("democrata maghiara", "UDMR"), ("s.o.s", "SOS RO"),
                ("oamenilor tineri", "POT"),
            ]
            for d in data.get("data", []):
                name = (d.get("current_party") or "").lower()
                for test, short in PARTY_MAP:
                    if test in name:
                        parties.add(short)
                        break
        except (json.JSONDecodeError, KeyError):
            pass
    for p in sorted(parties):
        urls.append((f"{BASE_URL}/partid.html?id={p}&leg=2024", today, "0.7"))

    # Recent votes (final votes only)
    vot_file = ROOT / "data" / "v1" / "voturi" / "2024" / "_index.json"
    if vot_file.exists():
        try:
            data = json.loads(vot_file.read_text(encoding="utf-8"))
            final = [v for v in data.get("data", []) if "final" in (v.get("descriere") or "").lower()]
            for v in final[:100]:
                idv = v.get("cdep_idv")
                if idv:
                    urls.append((f"{BASE_URL}/vot.html?id={idv}&leg=2024", today, "0.5"))
        except (json.JSONDecodeError, KeyError):
            pass

    # Bills with known registration date
    for year in ["2024", "2025", "2026"]:
        bill_file = ROOT / "data" / "v1" / "proiecte" / "legislatura-2024" / f"{year}.json"
        if bill_file.exists():
            try:
                data = json.loads(bill_file.read_text(encoding="utf-8"))
                for p in data.get("data", data) if isinstance(data, dict) else data:
                    idp = p.get("cdep_idp")
                    if idp:
                        urls.append((f"{BASE_URL}/proiect.html?idp={idp}&leg=2024", today, "0.5"))
            except (json.JSONDecodeError, KeyError):
                pass

    # Build XML
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for loc, lastmod, prio in urls:
        loc_escaped = loc.replace("&", "&amp;")
        lines.append(
            f"  <url>\n"
            f"    <loc>{loc_escaped}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <priority>{prio}</priority>\n"
            f"  </url>"
        )
    lines.append("</urlset>")

    out_path = ROOT / "web" / "sitemap.xml"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK: {len(urls)} URL-uri → {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
