"""Build agregat /stats/home — numărători per legislatură pentru bara de statistici de pe pagina principală.

Pagina principală (``index.html``) afișează 9 numărători (deputați, voturi, proiecte,
interpelări, comisii, moțiuni, ședințe plen, declarații avere, sancțiuni). Înainte ca
acest fișier să existe, ``index.html`` descărca fișierul brut al fiecărui endpoint doar
ca să citească ``meta.count`` — inclusiv ``interpelari/legislatura-2024.json`` (~11 MB) și
``proiecte/legislatura-2024.json`` (~6 MB). Acest build precalculează numărătorile într-un
singur fișier mic, ca pagina să nu mai tragă megabytes pentru câteva cifre.

Output: ``data/v1/stats/home-{leg}.json``

Utilizare:
    python scripts/build_home_stats.py              # legislatura 2024
    python scripts/build_home_stats.py --leg 2020
    python scripts/build_home_stats.py --all        # 2024 + 2020 + 2016
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020, 2016]

# cheie afișată în counts → path relativ (sub data/v1/) al fișierului-sursă, cu {leg}.
# Voturile sunt stocate pe an, indexul fiind în voturi/{leg}/_index.json.
SOURCES: dict[str, str] = {
    "deputati": "deputati/legislatura-{leg}.json",
    "voturi": "voturi/{leg}/_index.json",
    "proiecte": "proiecte/legislatura-{leg}.json",
    "interpelari": "interpelari/legislatura-{leg}.json",
    "comisii": "comisii/legislatura-{leg}.json",
    "motiuni": "motiuni/legislatura-{leg}.json",
    "ordine_zi": "ordine-zi/legislatura-{leg}.json",
    "declaratii_avere": "declaratii-avere/legislatura-{leg}.json",
    "sanctiuni": "sanctiuni/legislatura-{leg}.json",
}


def _count(path: Path) -> int | None:
    """Numărul de înregistrări dintr-un fișier endpoint (meta.count, fallback len(data))."""
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    meta = doc.get("meta") or {}
    if isinstance(meta.get("count"), int):
        return meta["count"]
    data = doc.get("data")
    return len(data) if isinstance(data, list) else None


def _voturi_adoptate_pct(base: Path, leg: int) -> float | None:
    """% voturi unde pentru > contra, din indexul voturi/{leg}/_index.json."""
    idx_path = base / f"voturi/{leg}/_index.json"
    if not idx_path.is_file():
        return None
    try:
        votes = json.loads(idx_path.read_text(encoding="utf-8")).get("data", [])
    except (OSError, json.JSONDecodeError):
        return None
    if not votes:
        return None
    adopted = sum(1 for v in votes if v.get("counts", {}).get("pentru", 0) > v.get("counts", {}).get("contra", 0))
    return round(adopted / len(votes) * 100, 1)


def build_leg(leg: int, root: Path = ROOT) -> int:
    base = root / "data" / "v1"
    counts: dict[str, int] = {}
    missing: list[str] = []
    for key, tmpl in SOURCES.items():
        n = _count(base / tmpl.format(leg=leg))
        if n is None:
            missing.append(key)
        else:
            counts[key] = n

    if not counts:
        print(f"WARN leg {leg}: niciun fișier-sursă găsit (sărit)")
        return 0

    indicators: dict[str, float] = {}
    pct = _voturi_adoptate_pct(base, leg)
    if pct is not None:
        indicators["voturi_adoptate_pct"] = pct

    payload = {
        "meta": {
            **Meta(
                generated_at=datetime.now(UTC),
                source_url=(
                    "https://endimion2k.github.io/cdep-api-poc/"
                    f"data/v1/stats/home-{leg}.json"
                ),
                scraper_version="0.1.0",
                count=sum(counts.values()),
            ).model_dump(mode="json"),
            "legislatura": leg,
        },
        "counts": counts,
        **({"indicators": indicators} if indicators else {}),
    }

    out_dir = base / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"home-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    miss = f" · lipsă: {', '.join(missing)}" if missing else ""
    print(f"OK leg {leg}: {len(counts)} numărători → {out_path}{miss}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true", help="Build 2024 + 2020 + 2016")
    args = parser.parse_args()

    legs = ALL_LEGS if args.all else [args.leg]
    ret = 0
    for leg in legs:
        ret = build_leg(leg) or ret
    return ret


if __name__ == "__main__":
    raise SystemExit(main())
