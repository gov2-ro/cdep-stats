#!/usr/bin/env python3
"""Build the deployment web/ folder with all assets needed for shared hosting."""

import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
WEB = ROOT / "web"
DATA = ROOT / "data"


def clean_web():
    """Remove existing web folder."""
    if WEB.exists():
        print("Cleaning web/ folder...")
        shutil.rmtree(WEB)


def create_structure():
    """Create web folder structure."""
    print("Creating web/ folder structure...")
    (WEB / "data" / "v1").mkdir(parents=True, exist_ok=True)
    (WEB / "assets").mkdir(parents=True, exist_ok=True)
    (WEB / "pages").mkdir(parents=True, exist_ok=True)
    (WEB / "pagefind").mkdir(parents=True, exist_ok=True)


def copy_root_files():
    """Copy root HTML, favicon, and i18n.js."""
    print("Copying root HTML files...")
    for file in ROOT.glob("*.html"):
        shutil.copy2(file, WEB / file.name)

    for file in ["favicon.svg", "i18n.js"]:
        src = ROOT / file
        if src.exists():
            shutil.copy2(src, WEB / file)


def copy_assets():
    """Copy assets from root/assets and data/assets."""
    print("Copying assets...")
    src_assets = ROOT / "assets"
    if src_assets.exists():
        for file in src_assets.glob("*.js"):
            shutil.copy2(file, WEB / "assets" / file.name)

    data_assets = DATA / "assets"
    if data_assets.exists():
        for item in data_assets.iterdir():
            if item.is_dir():
                dest = WEB / "assets" / item.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, WEB / "assets" / item.name)


def copy_data():
    """Copy data/v1 API files."""
    print("Copying data/v1...")
    src = DATA / "v1"
    if src.exists():
        for item in src.iterdir():
            dest = WEB / "data" / "v1" / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)


def copy_pages():
    """Copy generated HTML pages."""
    print("Copying pages/...")
    src = ROOT / "pages"
    if src.exists():
        for item in src.iterdir():
            dest = WEB / "pages" / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)


def copy_pagefind():
    """Copy search index."""
    print("Copying pagefind/...")
    src = ROOT / "pagefind"
    if src.exists():
        dest = WEB / "pagefind"
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)


def report():
    """Show final size and structure."""
    print("\n" + "=" * 60)
    result = subprocess.run(["du", "-sh", str(WEB)], capture_output=True, text=True)
    print(f"✓ web/ folder ready: {result.stdout.strip()}")

    html_count = len(list(WEB.glob("*.html")))
    print(f"  - {html_count} HTML pages")
    print(f"  - assets/")
    print(f"  - pages/")
    print(f"  - pagefind/")
    print(f"  - data/v1/")
    print("\nTo deploy:")
    print("  $ zip -r deploy.zip web/")
    print("  $ scp deploy.zip user@host:/path/to/public_html/")
    print("=" * 60)


def main():
    """Build the deployment folder."""
    clean_web()
    create_structure()
    copy_root_files()
    copy_assets()
    copy_data()
    copy_pages()
    copy_pagefind()
    report()


if __name__ == "__main__":
    main()
