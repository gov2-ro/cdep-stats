"""Raport jurnalistic — averile parsate ale deputaților.

Top-uri utile pentru investigație:
- Cele mai mari creșteri de conturi în mandat
- Cele mai mari scăderi
- Deputați cu cele mai multe imobile noi
- Median conturi per partid
- Outliers per partid

Utilizare:
    python scripts/raport_avere.py
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = ROOT / "data" / "v1" / "declaratii-avere" / "legislatura-2024.json"


def main() -> int:
    if not INDEX_FILE.exists():
        print(f"Lipsește {INDEX_FILE}. Rulează întâi build_declaratii_avere.py")
        return 1

    data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))["data"]
    # Filtrăm doar pe cei cu text extras (deci sume valide)
    valid = [d for d in data if d.get("n_declaratii", 0) > 0]
    print(f"Date: {len(valid)} deputați cu cel puțin o declarație parsată")
    print()

    # === Top 10 — Creștere conturi în mandat ===
    print("=" * 80)
    print("TOP 10 — CREȘTERE conturi RON între prima și ultima declarație")
    print("=" * 80)
    top_grow = sorted(valid, key=lambda d: d.get("delta_conturi_ron", 0), reverse=True)[:10]
    for d in top_grow:
        delta = d.get("delta_conturi_ron", 0)
        if delta <= 0:
            continue
        n = d.get("n_declaratii", 0)
        print(
            f"  {(d.get('partid_short') or '-'):<6} {d['deputat_nume']:<35} "
            f"+{delta:>15,.0f} RON  ({n} decl.)"
        )

    # === Top 10 — Scădere conturi ===
    print()
    print("=" * 80)
    print("TOP 10 — SCĂDERE conturi RON între prima și ultima declarație")
    print("=" * 80)
    top_drop = sorted(valid, key=lambda d: d.get("delta_conturi_ron", 0))[:10]
    for d in top_drop:
        delta = d.get("delta_conturi_ron", 0)
        if delta >= 0:
            continue
        n = d.get("n_declaratii", 0)
        print(
            f"  {(d.get('partid_short') or '-'):<6} {d['deputat_nume']:<35} "
            f"{delta:>16,.0f} RON  ({n} decl.)"
        )

    # === Top 10 — Mai multe imobile în mandat ===
    print()
    print("=" * 80)
    print("TOP 10 — MAI MULTE imobile la ultima declarație vs prima")
    print("=" * 80)
    top_imob = sorted(valid, key=lambda d: d.get("delta_imobile", 0), reverse=True)[:10]
    for d in top_imob:
        delta = d.get("delta_imobile", 0)
        if delta <= 0:
            continue
        print(
            f"  {(d.get('partid_short') or '-'):<6} {d['deputat_nume']:<35} "
            f"+{delta} imobile (acum: {d.get('ultima_imobile_count', 0)})"
        )

    # === Top 10 — Cele mai mari conturi ===
    print()
    print("=" * 80)
    print("TOP 10 — Cele mai MARI conturi (ultima declarație)")
    print("=" * 80)
    top_rich = sorted(valid, key=lambda d: d.get("ultima_conturi_ron", 0), reverse=True)[:10]
    for d in top_rich:
        ron = d.get("ultima_conturi_ron", 0)
        print(
            f"  {(d.get('partid_short') or '-'):<6} {d['deputat_nume']:<35} "
            f"{ron:>15,.0f} RON conturi"
        )

    # === Top 10 — Cele mai mari venituri anuale ===
    print()
    print("=" * 80)
    print("TOP 10 — Cele mai MARI venituri anuale (ultima declarație)")
    print("=" * 80)
    top_vens = sorted(valid, key=lambda d: d.get("ultima_venituri_ron", 0), reverse=True)[:10]
    for d in top_vens:
        ron = d.get("ultima_venituri_ron", 0)
        print(
            f"  {(d.get('partid_short') or '-'):<6} {d['deputat_nume']:<35} "
            f"{ron:>15,.0f} RON/an"
        )

    # === Median/medie per partid ===
    print()
    print("=" * 80)
    print("STATISTICI PER PARTID")
    print("=" * 80)
    by_partid: dict[str, list[dict]] = defaultdict(list)
    for d in valid:
        p = d.get("partid_short") or "(neafiliat)"
        by_partid[p].append(d)

    print(
        f"{'Partid':<14} {'N':>4} {'Median conturi':>16} {'Median venituri':>17} "
        f"{'Total imob':>11}"
    )
    print("-" * 80)
    for partid in sorted(by_partid.keys(), key=lambda p: -len(by_partid[p])):
        items = by_partid[partid]
        if len(items) < 3:
            continue
        m_conturi = statistics.median(d.get("ultima_conturi_ron", 0) for d in items)
        m_venituri = statistics.median(d.get("ultima_venituri_ron", 0) for d in items)
        total_imob = sum(d.get("ultima_imobile_count", 0) for d in items)
        print(
            f"{partid:<14} {len(items):>4} {m_conturi:>16,.0f} {m_venituri:>17,.0f} "
            f"{total_imob:>11}"
        )

    print()
    print("Notă: median, NU medie — outliers nu trag rezultatele.")
    print()
    print("Detalii per deputat: data/v1/declaratii-avere/legislatura-2024/<idm>.json")
    print("Index complet:       data/v1/declaratii-avere/legislatura-2024.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
