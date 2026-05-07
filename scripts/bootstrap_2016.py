"""Bootstrap legislatura 2016 — rulează toate scraperele pe perioada 2016-12-21 → 2020-12-20.

Folosit pentru a aduce datele istorice ale legislaturii 2016 în paritate cu 2020 și 2024.

Utilizare:
    python scripts/bootstrap_2016.py                     # toate (sărind cele deja existente)
    python scripts/bootstrap_2016.py --only voturi       # doar voturi
    python scripts/bootstrap_2016.py --only proiecte interpelari
    python scripts/bootstrap_2016.py --force             # re-rulează inclusiv ce există deja

Recomandare: rulează etape separat (ex. --only voturi) ca să poți relua de unde ai rămas
dacă cdep.ro picătură. Voturile sunt cele mai grele (~3.000-5.000 fișiere individuale).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LEG = 2016
START = "2016-12-21"
END = "2020-12-20"
YEARS = [2016, 2017, 2018, 2019, 2020]

# Stadii ordonate după dependențe + cost
STAGES = {
    "deputati": {
        "cmd": ["python", "scripts/run_deputati.py", "--leg", "2016"],
        "out": ROOT / "data" / "v1" / "deputati" / "legislatura-2016.json",
        "desc": "361 deputați cu profile complete",
    },
    "sanctiuni": {
        "cmd": ["python", "scripts/run_sanctiuni.py", "--leg", "2016"],
        "out": ROOT / "data" / "v1" / "sanctiuni" / "legislatura-2016.json",
        "desc": "Sancțiuni disciplinare",
    },
    "comisii": {
        "cmd": ["python", "scripts/build_comisii.py", "--leg", "2016"],
        "out": ROOT / "data" / "v1" / "comisii" / "legislatura-2016.json",
        "desc": "Comisii (derivate din deputați)",
    },
    "voturi": {
        "cmd": [
            "python",
            "scripts/run_voturi.py",
            "--from",
            START,
            "--to",
            END,
            "--verbose",
        ],
        "out": ROOT / "data" / "v1" / "voturi" / "2016" / "_index.json",
        "desc": "~3.000-5.000 voturi nominale (foarte mare, durează 1-3 ore)",
    },
    "interpelari": {
        "cmd": [
            "python",
            "scripts/run_interpelari.py",
            "--years",
            *[str(y) for y in YEARS],
            "--leg",
            "2016",
        ],
        "out": ROOT / "data" / "v1" / "interpelari" / "legislatura-2016.json",
        "desc": "Interpelări 2016-2020 (durează 30-60 min)",
    },
    "proiecte": {
        "cmd": [
            "python",
            "scripts/run_proiecte.py",
            "--years",
            *[str(y) for y in YEARS],
            "--leg",
            "2016",
        ],
        "out": ROOT / "data" / "v1" / "proiecte" / "legislatura-2016.json",
        "desc": "Proiecte legislative 2016-2020 cu timeline",
    },
    "motiuni": {
        "cmd": ["python", "scripts/run_motiuni.py", "--leg", "2016"],
        "out": ROOT / "data" / "v1" / "motiuni" / "legislatura-2016.json",
        "desc": "Moțiuni simple + cenzură",
    },
    "amendamente": {
        "cmd": ["python", "scripts/build_amendamente.py", "--leg", "2016"],
        "out": ROOT / "data" / "v1" / "amendamente" / "legislatura-2016.json",
        "desc": "View derivat din proiecte (necesită proiecte deja scrapped)",
    },
}


def run_stage(name: str, force: bool) -> bool:
    stage = STAGES[name]
    if stage["out"].exists() and not force:
        size_kb = stage["out"].stat().st_size / 1024
        print(f"[SKIP] {name}: există deja ({size_kb:.0f} KB). Folosește --force ca să re-rulezi.")
        return True

    print(f"\n{'=' * 70}")
    print(f"[START] {name} — {stage['desc']}")
    print(f"        cmd: {' '.join(stage['cmd'])}")
    print(f"{'=' * 70}\n")

    t0 = time.time()
    res = subprocess.run(stage["cmd"], cwd=ROOT)  # noqa: S603
    dt = time.time() - t0

    if res.returncode != 0:
        print(f"\n[FAIL] {name} (exit code {res.returncode}, {dt:.1f}s)")
        return False
    print(f"\n[OK] {name} terminat în {dt:.1f}s")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        nargs="+",
        choices=list(STAGES.keys()),
        help="Rulează doar stadiile specificate",
    )
    parser.add_argument(
        "--force", action="store_true", help="Re-rulează inclusiv stadiile cu output existent"
    )
    args = parser.parse_args()

    stages_to_run = args.only or list(STAGES.keys())

    print(f"Bootstrap legislatura {LEG} ({START} → {END})")
    print(f"Stadii: {', '.join(stages_to_run)}")
    print(f"Force re-run: {args.force}")

    failed = []
    for name in stages_to_run:
        if not run_stage(name, args.force):
            failed.append(name)

    print(f"\n{'=' * 70}")
    if failed:
        print(f"[REZULTAT] Eșuate: {', '.join(failed)}")
        return 1
    print("[REZULTAT] Toate stadiile OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
