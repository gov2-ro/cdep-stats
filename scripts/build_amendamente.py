"""Construiește endpoint-ul /amendamente.json — view derivat din /proiecte.

NU este un scraper — agregă proiectele care au amendamente (admise sau respinse)
într-un fișier dedicat, sortat după număr de amendamente admise descrescător.

Util pentru jurnaliști: „care sunt cele mai disputate proiecte legislative?"

Output: `data/v1/amendamente/legislatura-{leg}.json`

Utilizare:
    python scripts/build_amendamente.py                # toate legislaturile cu date
    python scripts/build_amendamente.py --leg 2024     # doar legislatura specifică
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

BUILDER_VERSION = "0.1.0"


def build_legislatura(leg: int) -> int:
    """Construiește lista de proiecte cu amendamente. Returnează numărul de records."""
    src = ROOT / "data" / "v1" / "proiecte" / f"legislatura-{leg}.json"
    if not src.exists():
        logging.warning(f"Nu există fișier proiecte pentru legislatura {leg}: {src}")
        return 0

    proiecte = json.loads(src.read_text(encoding="utf-8"))["data"]

    # Filter: doar proiectele care au amendamente (admise sau respinse) sau termen depus
    cu_amend = [
        p
        for p in proiecte
        if (p.get("amendamente_admise") or 0) > 0 or (p.get("amendamente_respinse") or 0) > 0
    ]

    # Sortez după total amendamente admise descrescător
    def sort_key(p: dict) -> int:
        return (p.get("amendamente_admise") or 0) + (p.get("amendamente_respinse") or 0)

    cu_amend.sort(key=sort_key, reverse=True)

    # Slim view — extrag doar câmpurile relevante pentru amendamente
    slim = []
    for p in cu_amend:
        slim.append(
            {
                "proiect_id": p["id"],
                "cdep_idp": p["cdep_idp"],
                "cam": p["cam"],
                "legislatura": p["legislatura"],
                "nr_inregistrare": p.get("nr_inregistrare"),
                "titlu": p.get("titlu"),
                "initiator": p.get("initiator"),
                "stadiu": p.get("stadiu"),
                "lege_nr": p.get("lege_nr"),
                "amendamente_termen_depunere": p.get("amendamente_termen_depunere"),
                "amendamente_admise": p.get("amendamente_admise") or 0,
                "amendamente_respinse": p.get("amendamente_respinse") or 0,
                "amendamente_total": (p.get("amendamente_admise") or 0)
                + (p.get("amendamente_respinse") or 0),
                "raport_comisie_pdf": p.get("raport_comisie_pdf"),
                "source_url": p.get("source_url"),
            }
        )

    out = ROOT / "data" / "v1" / "amendamente" / f"legislatura-{leg}.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    meta = Meta(
        generated_at=datetime.now(UTC),
        source_url=f"derived from /v1/proiecte/legislatura-{leg}.json",
        scraper_version=BUILDER_VERSION,
        count=len(slim),
    )
    payload = {
        "meta": meta.model_dump(mode="json"),
        "data": slim,
    }
    out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total_admise = sum(p["amendamente_admise"] for p in slim)
    total_respinse = sum(p["amendamente_respinse"] for p in slim)
    print(f"  legislatura {leg}: {len(slim)} proiecte cu amendamente")
    print(f"    {total_admise} amendamente admise, {total_respinse} respinse")
    print(f"  → {out}")
    return len(slim)


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

    print(f"\nTotal: {total} proiecte cu amendamente agregate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
