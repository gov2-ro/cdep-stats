"""Test offline pentru parser-ul de ordine de zi.

Utilizare:
    curl -s "https://www.cdep.ro/ords/pls/caseta/ecaseta2015.OrdineZi?dat=20260526" -o tmp_ordine.html
    python scripts/test_ordine_zi_parser.py
"""

from __future__ import annotations

import sys
from datetime import date
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
    html_path = ROOT / "tmp_discovery" / "ordine_home.html"
    if not html_path.exists():
        html_path = ROOT / "tmp_ordine.html"
    if not html_path.exists():
        print(f"Fișierul nu există: {html_path}. Rulează curl întâi.")
        return 1

    html = html_path.read_text(encoding="utf-8")
    print(f"Loaded {len(html)} bytes din {html_path}")

    from scrapers.ordine_zi import parse_session

    with patch("scrapers.ordine_zi.get", return_value=_FakeResponse(html)):
        result = parse_session(session_date=date(2026, 5, 26), legislatura=2024)

    if result is None:
        print("FAIL: parse_session returned None")
        return 1

    d = result.model_dump(mode="json", exclude_none=False)
    print()
    print("=" * 70)
    print("OK — parse_session a returnat OrdineZi cu", len(d["items"]), "puncte")
    print("=" * 70)
    print(f"  titlu: {d['titlu']}")
    print(f"  session_date: {d['session_date']}")
    print(f"  session_date_end: {d['session_date_end']}")
    print(f"  data_aprobare: {d['data_aprobare']}")
    print(f"  pdf_url: {d['pdf_url']}")
    print(f"  items: {len(d['items'])}")
    print()
    print("Primele 5 puncte:")
    for it in d["items"][:5]:
        desc_short = (it["descriere"][:80] + "...") if len(it["descriere"]) > 80 else it["descriere"]
        print(f"  [{it['pozitie']}] {it['nr_inregistrare'] or '-'} (idp={it['idp']}) — {desc_short}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
