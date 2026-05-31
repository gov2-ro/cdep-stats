#!/usr/bin/env python3
"""Build deploy.zip for shared hosting deployment — no intermediate copies."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
WEB = ROOT / "web"
ARCHIVE = ROOT / "deploy.zip"


def create_archive():
    print("Building deploy.zip...")
    if ARCHIVE.exists():
        ARCHIVE.unlink()

    # Root HTML + JS files from web/ land at archive root (strip web/ prefix)
    root_files = sorted(WEB.glob("*.html")) + sorted(WEB.glob("*.js"))
    if root_files:
        subprocess.run(
            ["zip", "-j", str(ARCHIVE)] + [str(f) for f in root_files],
            cwd=ROOT, check=True,
        )

    # assets/, data/v1/ — straight from source, exclude unused data folders
    subprocess.run(
        ["zip", "-r", str(ARCHIVE), "assets/", "data/v1/",
         "-x", "data/v1/voturi/*",
         "-x", "data/v1/proiecte/*",
         "-x", "data/v1/amendamente/*"],
        cwd=ROOT, check=True,
    )

    # data/assets/ merges into assets/ in the archive
    if (DATA / "assets").exists():
        subprocess.run(
            ["zip", "-r", str(ARCHIVE), "assets/"],
            cwd=DATA, check=True,
        )


def report():
    result = subprocess.run(["du", "-sh", str(ARCHIVE)], capture_output=True, text=True)
    print(f"✓ deploy.zip ready: {result.stdout.strip()}")
    print("\nTo deploy:")
    print("  $ scp deploy.zip user@host:/path/to/public_html/")
    print("  $ unzip -o deploy.zip")


def main():
    create_archive()
    report()


if __name__ == "__main__":
    main()
