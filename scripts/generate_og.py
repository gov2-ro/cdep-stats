#!/usr/bin/env python3
"""Generate OG screenshot images for all main pages.

Usage:
    python scripts/generate_og.py

Requires: pip install playwright && playwright install chromium
Output:  data/assets/og/{page}.png  (1200×630 px)
"""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "assets" / "og"
PORT = 9998

PAGES = [
    ("deputati-avere", "deputati-avere.html", ".dep-item"),
    ("deputati-activitate", "deputati-activitate.html", ".dep-item"),
    ("avere", "avere.html", ".section"),
    ("interpelari-stats", "interpelari-stats.html", ".section"),
    ("proiecte-stats", "proiecte-stats.html", ".section"),
    ("index", "index.html", "body"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            for name, path, selector in PAGES:
                url = f"http://localhost:{PORT}/{path}"
                print(f"  {url} → {name}.png", end=" ", flush=True)
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(selector, timeout=15_000)
                out = OUT / f"{name}.png"
                page.screenshot(
                    path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 630}
                )
                print("✓")
            browser.close()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
