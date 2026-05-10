"""Test rapid pentru parser-ul nou de interpelări, folosind fișierul tmp.html local.

Utilizare:
    curl -s "https://www.cdep.ro/ords/pls/parlam/interpelari2015.detalii?idi=82665&idl=1" -o tmp.html
    python scripts/test_interpelari_parser.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass


def main() -> int:
    html_path = ROOT / "tmp.html"
    if not html_path.exists():
        print(f"Fișierul {html_path} nu există. Rulează întâi curl ca să-l salvezi.")
        return 1

    html = html_path.read_text(encoding="utf-8")
    print(f"Loaded {len(html)} bytes from tmp.html")

    from scrapers.interpelari import parse_detail

    with patch("scrapers.interpelari.get", return_value=_FakeResponse(html)):
        result = parse_detail(idi=82665, legislatura=2024)

    if result is None:
        print("FAIL: parse_detail returned None")
        return 1

    print()
    print("=" * 70)
    print("OK — parse_detail a returnat un obiect")
    print("=" * 70)
    d = result.model_dump(mode="json", exclude_none=False)
    for k, v in d.items():
        if isinstance(v, str) and len(v) > 100:
            v = v[:97] + "..."
        print(f"  {k:<25} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
