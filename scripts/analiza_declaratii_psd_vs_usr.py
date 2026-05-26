"""Demo analiză comparativă PSD vs USR — declarații de avere.

Folosește API-ul cdep-api-poc pentru a obține lista deputaților + declarațiile lor.
Asta e o ANALIZĂ DE METADATE — nu intră în PDF-uri să citească sume.

Pentru analiză propriu-zisă pe sume (case, mașini, conturi bancare) trebuie
parsare PDF cu pdfplumber + heuristică pe formularul ANI standardizat.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent

# Sursă: API-ul nostru live (sau fișier local pentru test offline)
DEPUTATI_URL = "https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json"
DECLARATII_URL = (
    "https://endimion2k.github.io/cdep-api-poc/data/v1/declaratii/legislatura-2024.json"
)


def fetch_or_local(url: str, local_path: Path) -> dict:
    """Încearcă local întâi, fallback la URL live."""
    if local_path.exists():
        return json.loads(local_path.read_text(encoding="utf-8"))
    print(f"Fetching {url}...")
    return requests.get(url, timeout=30).json()


def main() -> int:
    print("Comparație declarații avere PSD vs USR — Legislatura 2024")
    print("=" * 70)

    declaratii = fetch_or_local(
        DECLARATII_URL, ROOT / "data" / "v1" / "declaratii" / "legislatura-2024.json"
    )["data"]

    # Filtrare după partid
    psd = [d for d in declaratii if d.get("partid_short") == "PSD"]
    usr = [d for d in declaratii if d.get("partid_short") == "USR"]

    print(
        f"\n{'Partid':<8} | {'Deputați':>9} | {'Decl. avere':>12} | {'Decl. interese':>14} | {'Modif.':>7}"
    )
    print("-" * 70)
    for label, group in [("PSD", psd), ("USR", usr)]:
        n_dep = len(group)
        n_avere = sum(len(d.get("avere", [])) for d in group)
        n_interese = sum(len(d.get("interese", [])) for d in group)
        # "Modificări" = deputați care au mai mult de 1 declarație de avere
        # (declarația inițială + corecturi/actualizări)
        modif = sum(1 for d in group if len(d.get("avere", [])) > 1)
        print(f"{label:<8} | {n_dep:>9} | {n_avere:>12} | {n_interese:>14} | {modif:>7}")

    print("\n--- Deputați cu CELE MAI MULTE actualizări declarații (avere) ---")
    print("Asta poate sugera o averea care s-a schimbat în timpul mandatului.\n")
    by_modif = sorted(
        psd + usr,
        key=lambda d: len(d.get("avere", [])),
        reverse=True,
    )
    print(f"{'Partid':<8} {'Deputat':<35} {'Decl. avere':>12} {'Ultima':>12}")
    print("-" * 70)
    for d in by_modif[:15]:
        n = len(d.get("avere", []))
        if n <= 1:
            continue
        ultima = max((x.get("data") for x in d.get("avere", []) if x.get("data")), default="?")
        print(
            f"{(d.get('partid_short') or 'N/A'):<8} "
            f"{d['deputat_nume']:<35} "
            f"{n:>12} "
            f"{ultima:>12}"
        )

    print("\n--- Pentru analiză propriu-zisă pe SUME (case, conturi, etc.) ---")
    print("Trebuie parsare PDF cu pdfplumber:")
    print("  pip install pdfplumber")
    print("  Pentru fiecare deputat: descarcă cel mai recent PDF avere, extrage tabelele,")
    print("  identifică câmpurile standardizate ANI (imobile, conturi, salarii, etc.)")
    print()
    print("Sume comparabile între 2020 și 2024 = real wealth growth tracking.")
    print("Asta e o investiție de 4-8 ore pentru un script robust de PDF mining.")

    return 0


if __name__ == "__main__":
    main()
