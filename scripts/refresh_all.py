"""Refresh toate endpointurile la zi.

Rulează scrape-urile incremental pentru toate endpointurile + regenerează derivate
(comisii, amendamente, status). Folosit pentru a aduce toate datele la zi după
o perioadă de inactivitate.

Utilizare:
    python scripts/refresh_all.py                    # incremental (rapid, ~5-10 min)
    python scripts/refresh_all.py --full             # refetch toate (deputati + proiecte + motiuni)
    python scripts/refresh_all.py --skip-voturi      # sare peste voturi (cel mai greu)
    python scripts/refresh_all.py --only deputati interpelari proiecte
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Stadii — ORDINEA contează (derivate la urmă!)
STAGES = [
    # (nume, comandă base, e_derivat)
    ("deputati", ["python", "scripts/run_deputati.py", "--leg", "2024", "--verbose"], False),
    ("sanctiuni", ["python", "scripts/run_sanctiuni.py", "--leg", "2024", "--verbose"], False),
    ("voturi", ["python", "scripts/run_voturi.py", "--days", "14", "--verbose"], False),
    (
        "interpelari",
        ["python", "scripts/run_interpelari.py", "--year", "2026", "--leg", "2024", "--verbose"],
        False,
    ),
    (
        "proiecte",
        ["python", "scripts/run_proiecte.py", "--year", "2026", "--leg", "2024", "--verbose"],
        False,
    ),
    ("motiuni", ["python", "scripts/run_motiuni.py", "--leg", "2024", "--verbose"], False),
    (
        "ordine-zi",
        ["python", "scripts/run_ordine_zi.py", "--year", "2026", "--leg", "2024", "--verbose"],
        False,
    ),
    ("declaratii", ["python", "scripts/run_declaratii.py", "--leg", "2024", "--verbose"], False),
    ("declaratii-avere", ["python", "scripts/build_declaratii_avere.py", "--leg", "2024", "--verbose"], True),
    (
        "stenograme",
        ["python", "scripts/run_stenograme.py", "--year", "2026", "--leg", "2024", "--verbose"],
        False,
    ),
    ("doc-comisii", ["python", "scripts/run_doc_comisii.py", "--pages", "5", "--verbose"], False),
    # Derivate — rulate la urmă
    ("comisii", ["python", "scripts/build_comisii.py", "--leg", "2024"], True),
    ("avere-stats", ["python", "scripts/build_avere_stats.py", "--leg", "2024"], True),
    ("amendamente", ["python", "scripts/build_amendamente.py", "--leg", "2024"], True),
    ("feeds", ["python", "scripts/build_feeds.py", "--leg", "2024", "--per-type", "15"], True),
    ("split_files", ["python", "scripts/split_by_year.py", "--leg", "2024"], True),
    ("status", ["python", "scripts/build_status.py"], True),
]

FULL_FLAGS = {
    "deputati": "--full",
    "proiecte": "--full",
    "motiuni": "--full",
    "ordine-zi": "--full",
}


def run_stage(name: str, cmd: list[str], use_full: bool) -> bool:
    if use_full and name in FULL_FLAGS:
        cmd = [*cmd, FULL_FLAGS[name]]
    print(f"\n{'=' * 70}")
    print(f"[START] {name}  {' '.join(cmd)}")
    print("=" * 70)
    t0 = time.time()
    res = subprocess.run(cmd, cwd=ROOT)
    dt = time.time() - t0
    if res.returncode != 0:
        print(f"[FAIL] {name} (exit {res.returncode}, {dt:.1f}s)")
        return False
    print(f"[OK] {name} terminat în {dt:.1f}s")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full", action="store_true", help="Pasează --full către scraperele care suportă"
    )
    parser.add_argument(
        "--skip-voturi", action="store_true", help="Sare peste voturi (cel mai greu)"
    )
    parser.add_argument("--only", nargs="+", help="Rulează doar stadiile specificate (nume scurt)")
    args = parser.parse_args()

    selected = args.only or [name for name, _, _ in STAGES]
    if args.skip_voturi and "voturi" in selected:
        selected.remove("voturi")

    failed: list[str] = []
    print(f"Refresh stages: {', '.join(selected)}")
    print(f"Full mode: {args.full}")

    for name, cmd, _is_derivat in STAGES:
        if name not in selected:
            continue
        if not run_stage(name, cmd, args.full):
            failed.append(name)

    print(f"\n{'=' * 70}")
    if failed:
        print(f"[REZULTAT] Eșuate: {', '.join(failed)}")
        return 1
    print("[REZULTAT] Toate stadiile OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
