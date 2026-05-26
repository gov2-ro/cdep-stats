"""Debug extragerea unui PDF de declarație — arată ce găsește pdfplumber.

Utilizare:
    python scripts/debug_pdf_extract.py                 # primul PDF din cache
    python scripts/debug_pdf_extract.py data/analize/_pdfs/189.pdf
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
PDF_CACHE = ROOT / "data" / "analize" / "_pdfs"


def main() -> int:
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
    else:
        pdfs = sorted(PDF_CACHE.glob("*.pdf"))
        if not pdfs:
            print(f"Nu există PDF-uri în {PDF_CACHE}")
            return 1
        pdf_path = pdfs[0]

    print(f"Debug: {pdf_path}")
    print("=" * 70)

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    print(f"Text total: {len(full_text)} caractere")
    print(f"Pagini: {len(pdfplumber.open(pdf_path).pages)}")
    print()

    # Markeri pe care îi căutăm
    print("--- Markeri secțiuni găsiți în text ---")
    markeri_test = [
        "BUNURI IMOBILE",
        "Bunuri imobile",
        "BUNURI MOBILE",
        "Bunuri mobile",
        "ACTIVE FINANCIARE",
        "Active financiare",
        "DATORII",
        "Datorii",
        "VENITURI",
        "Venituri",
        "DECLARAȚIE",
        "I. ",
        "II. ",
        "III. ",
        "IV. ",
        "V. ",
        "VI. ",
        "TERENURI",
        "CLĂDIRI",
        "Clădiri",
        "Terenuri",
        "Conturi",
        "AUTOVEHICUL",
        "Autovehicul",
        "Salariu",
        "salariu",
        "RON",
        "EUR",
    ]
    for m in markeri_test:
        pos = full_text.find(m)
        if pos >= 0:
            # Arată contextul
            snippet = full_text[pos : pos + 80].replace("\n", " ")
            print(f"  '{m}' la pozitia {pos}: ...{snippet}...")
        else:
            print(f"  '{m}' — NU GĂSIT")

    print()
    print("--- Sume detectate cu regex ---")
    re_amount = re.compile(
        r"(\d[\d\s.,]*?\d|\d)\s*(RON|EUR|EURO|USD|GBP|CHF|lei|euro|dolari)\b",
        re.IGNORECASE,
    )
    matches = list(re_amount.finditer(full_text))
    print(f"Total potriviri cu regex sume+valută: {len(matches)}")
    for m in matches[:15]:
        print(f"  '{m.group(0)}'")

    print()
    print("--- Numere mari (>1000) fără valută ---")
    re_big_num = re.compile(r"\b\d[\d.,]{4,}\b")
    big_nums = list(re_big_num.finditer(full_text))
    print(f"Total numere >=5 cifre: {len(big_nums)}")
    for m in big_nums[:20]:
        # Context: 30 chars înainte și după
        start = max(0, m.start() - 30)
        end = min(len(full_text), m.end() + 30)
        ctx = full_text[start:end].replace("\n", " ")
        print(f"  '{m.group(0)}'   în: ...{ctx}...")

    print()
    print("--- Primele 1500 caractere ale textului extras ---")
    print(full_text[:1500])
    print()
    print("...")
    print(full_text[-500:])

    return 0


if __name__ == "__main__":
    sys.exit(main())
