"""Construiește endpoint-ul /comisii din datele de deputați.

NU este un scraper — agregă datele care există deja în `data/v1/deputati/legislatura-*.json`
într-un fișier dedicat per legislatură.

Output: `data/v1/comisii/legislatura-{leg}.json`

Utilizare:
    python scripts/build_comisii.py                # toate legislaturile cu date
    python scripts/build_comisii.py --leg 2024     # doar legislatura specifică
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.comisie import Comisie, ComisieMembru, TipComisie  # noqa: E402
from schemas.common import Meta  # noqa: E402

BUILDER_VERSION = "0.1.0"


def slug(s: str) -> str:
    """Generează slug ASCII pentru ID-ul comisiei."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


def normalize_name(nume: str) -> str:
    """Curăță numele comisiei de variante temporale și artefacte parser.

    Exemple curate:
        'Comisia X (din feb. 2025)' → 'Comisia X'
        'Comisia X (până în sep. 2025)' → 'Comisia X'
        'Comisia X Alte comisii' → 'Comisia X'
    """
    # Strip artefact „Alte comisii" la final
    nume = re.sub(r"\s+Alte\s+comisii\s*$", "", nume, flags=re.IGNORECASE)
    # Strip orice paranteză care conține o lună abreviată sau un an (variantele temporale)
    luni = r"(?:ian|feb|mar|apr|mai|iun|iul|aug|sep|oct|noi|dec)"
    nume = re.sub(rf"\s*\([^)]*(?:{luni}|\b20\d{{2}}\b)[^)]*\)\s*", " ", nume, flags=re.IGNORECASE)
    # Whitespace normalization
    nume = re.sub(r"\s+", " ", nume).strip()
    return nume


def comisie_id(legislatura: int, nume: str, tip: str) -> str:
    """ID stabil hash pe (leg, nume, tip)."""
    return hashlib.sha256(f"{legislatura}|{nume}|{tip}".encode()).hexdigest()[:16]


def build_legislatura(leg: int) -> int:
    """Construiește comisii pentru o legislatură. Returnează numărul de comisii."""
    src = ROOT / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not src.exists():
        logging.warning(f"Nu există fișier deputați pentru legislatura {leg}: {src}")
        return 0

    deputati = json.loads(src.read_text(encoding="utf-8"))["data"]

    # (nume, tip) → list[ComisieMembru]
    grouped: dict[tuple[str, str], list[ComisieMembru]] = defaultdict(list)

    seen_per_dep: dict[tuple[str, tuple[str, str]], None] = {}

    for dep in deputati:
        for c in dep.get("comisii") or []:
            nume_raw = (c.get("comisia") or "").strip()
            if not nume_raw:
                continue
            nume = normalize_name(nume_raw)
            if not nume or len(nume) < 5:  # filtrez numele degenerate
                continue
            tip = (c.get("tip") or "permanenta").strip()
            rol = (c.get("rol") or "Membru").strip() or "Membru"

            # Deduplicate per (deputat, comisie) — evit dublarea când același deputat apare
            # cu variante temporale diferite
            dedup_key = (dep["id"], (nume, tip))
            if dedup_key in seen_per_dep:
                continue
            seen_per_dep[dedup_key] = None

            membru = ComisieMembru(
                deputat_canonical_id=dep["id"],
                deputat_nume=dep["name"],
                deputat_cdep_idm=dep["cdep_idm"],
                partid=dep.get("current_party"),
                rol=rol,
            )
            grouped[(nume, tip)].append(membru)

    # Construiesc Comisie per grup
    comisii: list[Comisie] = []
    for (nume, tip), membri in grouped.items():
        try:
            tip_enum = TipComisie(tip)
        except ValueError:
            tip_enum = TipComisie.PERMANENTA

        # Extrag conducerea
        presedinte = None
        vicepresedinti = []
        secretari = []
        for m in membri:
            rol_lc = m.rol.lower()
            if "preşedinte" in rol_lc or "președinte" in rol_lc or rol_lc == "president":
                if "vice" in rol_lc:
                    vicepresedinti.append(m.deputat_nume)
                else:
                    presedinte = m.deputat_nume
            elif "secretar" in rol_lc:
                secretari.append(m.deputat_nume)

        comisii.append(
            Comisie(
                id=comisie_id(leg, nume, tip),
                nume=nume,
                tip=tip_enum,
                legislatura=leg,
                nr_membri=len(membri),
                presedinte=presedinte,
                vicepresedinti=vicepresedinti,
                secretari=secretari,
                membri=sorted(membri, key=lambda x: x.deputat_nume),
            )
        )

    # Sortez alfabetic, cu permanente înaintea speciale
    comisii.sort(key=lambda c: (c.tip.value, c.nume))

    out = ROOT / "data" / "v1" / "comisii" / f"legislatura-{leg}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"derived from /v1/deputati/legislatura-{leg}.json",
        scraper_version=BUILDER_VERSION,
        count=len(comisii),
    )
    payload = {
        "meta": meta.model_dump(mode="json"),
        "data": [c.model_dump(mode="json") for c in comisii],
    }
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"  legislatura {leg}: {len(comisii)} comisii → {out}")
    return len(comisii)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=None, help="Legislatură specifică")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    legislaturi = [args.leg] if args.leg else [2016, 2020, 2024]
    total = 0
    for leg in legislaturi:
        total += build_legislatura(leg)

    print(f"\nTotal: {total} comisii agregate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
