"""Debug pe deputații cu cifre suspect de mari — validare manuală.

Pentru fiecare outlier:
1. Localizează PDF-ul în cache
2. Re-parsează cu context (text înainte/după fiecare sumă)
3. Listează top 20 sume detectate ca să poți filtra fals positives (IBAN, CNP, ani)

Utilizare:
    python scripts/debug_avere_outliers.py                          # outliers default (Becali, etc.)
    python scripts/debug_avere_outliers.py --idm 189                 # debug un anumit deputat
    python scripts/debug_avere_outliers.py --nume Becali             # caută după nume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

INDEX_FILE = ROOT / "data" / "v1" / "declaratii-avere" / "legislatura-2024.json"
DECL_FILE = ROOT / "data" / "v1" / "declaratii" / "legislatura-2024.json"
PDF_CACHE = ROOT / "data" / "analize" / "_pdfs"

RE_AMOUNT = re.compile(
    r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
    r"\s*(RON|EUR|EURO|USD|GBP|CHF|lei|euro|dolari)\b",
    re.IGNORECASE,
)

DEFAULT_OUTLIERS = ["Becali", "Iordache Ion", "Cruşoveanu", "Crusoveanu", "Tuşa", "Cîrligea"]


def debug_pdf(pdf_path: Path, deputat_nume: str, partid: str) -> None:
    print()
    print("=" * 90)
    print(f"DEBUG: {deputat_nume} ({partid})")
    print(f"PDF: {pdf_path.name}")
    print("=" * 90)

    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    print(f"Text total: {len(full_text)} caractere, {len(pdfplumber.open(pdf_path).pages)} pagini")
    print()

    # Localizează secțiunea IV. Active financiare
    start = full_text.find("IV. Active financiare")
    end_v = full_text.find("V. Datorii", start) if start > 0 else -1
    end_vi = full_text.find("VI. Cadouri", start) if start > 0 else -1
    end = max(end_v, end_vi) if end_v > 0 or end_vi > 0 else len(full_text)

    if start > 0:
        sec_conturi = full_text[start:end]
        print(f"--- Secțiunea IV. Active financiare ({len(sec_conturi)} chars) ---")
        print(sec_conturi[:2000])
        if len(sec_conturi) > 2000:
            print(f"... [+{len(sec_conturi) - 2000} chars]")
    else:
        print("⚠️ Nu am găsit secțiunea IV. Active financiare")

    print()
    print("--- Top 25 sume detectate de regex în întregul text (cu context) ---")
    matches = list(RE_AMOUNT.finditer(full_text))
    # Sortează după mărimea sumei detectate
    parsed = []
    for m in matches:
        num_str = m.group(1).replace(" ", "")
        if "." in num_str and "," in num_str:
            if num_str.rindex(",") > num_str.rindex("."):
                num_str = num_str.replace(".", "").replace(",", ".")
            else:
                num_str = num_str.replace(",", "")
        elif "," in num_str and len(num_str.split(",")[-1]) > 2:
            num_str = num_str.replace(",", "")
        elif "." in num_str:
            parts = num_str.split(".")
            if len(parts[-1]) == 3:
                num_str = num_str.replace(".", "")
        try:
            n = float(num_str)
        except ValueError:
            continue
        parsed.append((n, m))

    parsed.sort(key=lambda x: x[0], reverse=True)
    for n, m in parsed[:25]:
        start_pos = max(0, m.start() - 50)
        end_pos = min(len(full_text), m.end() + 50)
        ctx = full_text[start_pos:end_pos].replace("\n", " ")
        print(f"  {n:>15,.0f} {m.group(2):<5}  ... {ctx[:120]} ...")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--idm", type=int, help="cdep_idm specific")
    parser.add_argument("--nume", type=str, help="Caută după nume parțial")
    args = parser.parse_args()

    if not DECL_FILE.exists():
        print(f"Lipsește {DECL_FILE}")
        return 1

    declaratii = json.loads(DECL_FILE.read_text(encoding="utf-8"))["data"]

    if args.idm:
        targets = [d for d in declaratii if d["cdep_idm"] == args.idm]
    elif args.nume:
        targets = [d for d in declaratii if args.nume.lower() in d["deputat_nume"].lower()]
    else:
        # Default: outliers din raportul nostru
        targets = []
        for nume_pattern in DEFAULT_OUTLIERS:
            for d in declaratii:
                if nume_pattern.lower() in d["deputat_nume"].lower() and d not in targets:
                    targets.append(d)
                    break  # primul match pentru fiecare pattern

    if not targets:
        print("Niciun deputat găsit.")
        return 1

    print(f"Debug pentru {len(targets)} deputați:")
    for t in targets:
        print(
            f"  • {t['deputat_nume']} (idm={t['cdep_idm']}, partid={t.get('partid_short') or '-'})"
        )

    for d in targets:
        avere_pdfs = d.get("avere") or []
        if not avere_pdfs:
            print(f"⚠️  {d['deputat_nume']}: fără PDF avere")
            continue
        # Iau cel mai recent
        ultima = sorted(avere_pdfs, key=lambda x: x.get("data") or "", reverse=True)[0]
        url = ultima["url"]
        pdf_name = hashlib.sha1(url.encode()).hexdigest()[:12] + ".pdf"
        pdf_path = PDF_CACHE / pdf_name
        if not pdf_path.exists():
            print(f"⚠️  {d['deputat_nume']}: PDF lipsă în cache ({pdf_path})")
            continue
        debug_pdf(pdf_path, d["deputat_nume"], d.get("partid_short") or "-")

    return 0


if __name__ == "__main__":
    sys.exit(main())
