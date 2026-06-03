"""Refresh toate endpointurile la zi cu suport pentru cadență.

Rulează scrape-urile + derivate încadrate după frecvență: daily, weekly, full.

Utilizare:
    python scripts/refresh_all.py                      # weekly (default)
    python scripts/refresh_all.py --cadence daily      # fast daily run (~10-15 min)
    python scripts/refresh_all.py --cadence weekly     # weekly (default + slow)
    python scripts/refresh_all.py --cadence full       # full refetch + PDFs + HTML (slowest)
    python scripts/refresh_all.py --full               # alias for --cadence full (backward compat)
    python scripts/refresh_all.py --skip-voturi        # sare peste voturi (cel mai greu)
    python scripts/refresh_all.py --only deputati interpelari
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CURRENT_YEAR = str(datetime.now().year)

# Stadii — ORDINEA contează (derivate la urmă!)
# (nume, comandă base, cadență)
# cadență: "daily" < "weekly" < "full" (inclusiv)
STAGES = [
    # DAILY — fast incremental scrapers
    ("voturi", ["python3", "scripts/run_voturi.py", "--days", "7", "--verbose"], "daily"),
    ("interpelari", ["python3", "scripts/run_interpelari.py", "--year", CURRENT_YEAR, "--leg", "2024", "--verbose"], "daily"),
    ("proiecte", ["python3", "scripts/run_proiecte.py", "--year", CURRENT_YEAR, "--leg", "2024", "--verbose"], "daily"),
    ("ordine-zi", ["python3", "scripts/run_ordine_zi.py", "--year", CURRENT_YEAR, "--leg", "2024", "--verbose"], "daily"),
    ("motiuni", ["python3", "scripts/run_motiuni.py", "--leg", "2024", "--verbose"], "daily"),
    # DAILY — fast derives
    ("proiecte-index", ["python3", "scripts/build_proiecte_index.py", "--leg", "2024"], "daily"),
    ("comisii", ["python3", "scripts/build_comisii.py", "--leg", "2024"], "daily"),
    ("home-stats", ["python3", "scripts/build_home_stats.py", "--leg", "2024"], "daily"),
    ("amendamente", ["python3", "scripts/build_amendamente.py", "--leg", "2024"], "daily"),
    ("feeds", ["python3", "scripts/build_feeds.py", "--leg", "2024", "--per-type", "15"], "daily"),
    ("split_files", ["python3", "scripts/split_by_year.py", "--leg", "2024"], "daily"),
    ("interpelari-stats", ["python3", "scripts/build_interpelari_stats.py", "--leg", "2024"], "daily"),
    ("proiecte-stats", ["python3", "scripts/build_proiecte_stats.py", "--leg", "2024"], "daily"),
    ("status", ["python3", "scripts/build_status.py"], "daily"),
    # WEEKLY — slower scrapers
    ("deputati", ["python3", "scripts/run_deputati.py", "--leg", "2024", "--verbose"], "weekly"),
    ("sanctiuni", ["python3", "scripts/run_sanctiuni.py", "--leg", "2024", "--verbose"], "weekly"),
    ("declaratii", ["python3", "scripts/run_declaratii.py", "--leg", "2024", "--verbose"], "weekly"),
    ("stenograme", ["python3", "scripts/run_stenograme.py", "--year", CURRENT_YEAR, "--leg", "2024", "--verbose"], "weekly"),
    ("doc-comisii", ["python3", "scripts/run_doc_comisii.py", "--pages", "10", "--verbose"], "weekly"),
    ("activitate-deputies", ["python3", "scripts/build_activitate_deputies.py", "--leg", "2024"], "weekly"),
    # FULL — slow PDFs + generation
    ("declaratii-avere", ["python3", "scripts/build_declaratii_avere.py", "--leg", "2024", "--verbose"], "full"),
    ("declaratii-interese", ["python3", "scripts/build_declaratii_intereses.py", "--leg", "2024", "--verbose"], "full"),
    ("avere-stats", ["python3", "scripts/build_avere_stats.py", "--leg", "2024"], "full"),
    ("generate-html", ["python3", "scripts/generate_html.py"], "full"),
    ("sitemap", ["python3", "scripts/build_sitemap_xml.py"], "full"),
]

# Stages that accept --full flag for deep refetch
REFETCH_STAGES = {
    "deputati": "--full",
    "proiecte": "--full",
    "motiuni": "--full",
    "ordine-zi": "--full",
}


def run_stage(name: str, cmd: list[str], apply_refetch: bool) -> bool:
    """Run a single stage. apply_refetch adds --full flag if stage supports it."""
    if apply_refetch and name in REFETCH_STAGES:
        cmd = [*cmd, REFETCH_STAGES[name]]
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


def write_last_updated(cadence: str, failed: list[str]) -> None:
    """Write data/v1/last_updated.json with run metadata."""
    data = {
        "updated_at": datetime.now(UTC).isoformat(),
        "cadence": cadence,
        "failed": failed,
    }
    out = ROOT / "data" / "v1" / "last_updated.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[WROTE] {out}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cadence",
        choices=["daily", "weekly", "full"],
        default="weekly",
        help="Stadiile de rulat: daily < weekly < full (default: weekly)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Alias pentru --cadence full (backward compat)",
    )
    parser.add_argument(
        "--skip-voturi", action="store_true", help="Sare peste voturi (cel mai greu)"
    )
    parser.add_argument("--only", nargs="+", help="Rulează doar stadiile specificate (nume scurt)")
    args = parser.parse_args()

    # --full is backward-compat alias for --cadence full
    cadence = "full" if args.full else args.cadence

    # Filter stages by cadence
    cadence_order = {"daily": 1, "weekly": 2, "full": 3}
    cadence_threshold = cadence_order[cadence]
    eligible = [name for name, _, sc in STAGES if cadence_order[sc] <= cadence_threshold]

    # Apply --only filter (must be subset of eligible)
    selected = args.only or eligible
    if args.skip_voturi and "voturi" in selected:
        selected.remove("voturi")

    failed: list[str] = []
    print(f"Cadence: {cadence}")
    print(f"Selected stages: {', '.join(selected)}")

    for name, cmd, _stage_cadence in STAGES:
        if name not in selected:
            continue
        apply_refetch = cadence == "full"
        if not run_stage(name, cmd, apply_refetch):
            failed.append(name)

    print(f"\n{'=' * 70}")
    write_last_updated(cadence, failed)
    if failed:
        print(f"[REZULTAT] Eșuate: {', '.join(failed)}")
        return 1
    print("[REZULTAT] Toate stadiile OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
