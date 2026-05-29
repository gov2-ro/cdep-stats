"""Build agregat /stats/interpelari — statistici pentru dashboard-ul de interpelări.

Output: data/v1/stats/interpelari-{leg}.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020]
TOP_N = 15


def _clean_grup(g: str | None) -> str:
    if not g:
        return "Neafiliat"
    g = re.sub(r"\s*Destinatar[i]?:?\s*$", "", g.strip())
    g = re.sub(r"\s*Textul\s*$", "", g.strip())
    g = g.replace("Neafiliaţi", "Neafiliat").replace("Neafiliați", "Neafiliat").strip()
    return g or "Neafiliat"


def _clean_dest(dest: str | None) -> str:
    if not dest:
        return "Necunoscut"
    m = re.match(
        r"^(Ministerul [^î(]+?|Guvernul României|Preşedinţia|Curtea [^î]+?)"
        r"(?:\s+în atenţia|\s+\(|$)",
        dest,
    )
    if m:
        return m.group(1).strip()
    return dest[:70].strip()


def _response_days(row: dict) -> int | None:
    try:
        if row.get("raspuns_primit") and row.get("data_inregistrare") and row.get("raspuns_data"):
            delta = (
                date.fromisoformat(row["raspuns_data"])
                - date.fromisoformat(row["data_inregistrare"])
            ).days
            return delta if 0 < delta < 730 else None
    except (ValueError, TypeError):
        pass
    return None


def build_leg(leg: int, root: Path = ROOT) -> int:
    src = root / "data" / "v1" / "interpelari" / f"legislatura-{leg}.json"
    if not src.exists():
        print(f"Lipsește {src}.", file=sys.stderr)
        return 1

    rows: list[dict] = json.loads(src.read_text(encoding="utf-8"))["data"]
    total = len(rows)

    # ── Response stats ──────────────────────────────────────────────────
    answered = sum(1 for r in rows if r.get("raspuns_primit"))
    resp_times = [t for r in rows if (t := _response_days(r)) is not None]
    avg_days = round(sum(resp_times) / len(resp_times)) if resp_times else None
    median_days = sorted(resp_times)[len(resp_times) // 2] if resp_times else None

    # ── By party ────────────────────────────────────────────────────────
    by_grup: dict[str, dict] = defaultdict(lambda: {"total": 0, "answered": 0})
    for r in rows:
        g = _clean_grup(r.get("adresant_grup"))
        if g == "Neafiliat":
            continue
        by_grup[g]["total"] += 1
        if r.get("raspuns_primit"):
            by_grup[g]["answered"] += 1

    per_partid = [
        {
            "partid": p,
            "total": v["total"],
            "answered": v["answered"],
            "rate": round(v["answered"] / v["total"] * 100, 1) if v["total"] else 0,
        }
        for p, v in sorted(by_grup.items(), key=lambda kv: -kv[1]["total"])
        if v["total"] >= 5
    ]

    # ── Top askers ──────────────────────────────────────────────────────
    asker_counts: Counter = Counter()
    asker_names: dict[str, str] = {}
    asker_partids: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        cid = r.get("adresant_canonical_id")
        name = r.get("adresant_nume") or ""
        if not cid or not name:
            continue
        asker_counts[cid] += 1
        asker_names.setdefault(cid, name)
        g = _clean_grup(r.get("adresant_grup"))
        if g != "Neafiliat":
            asker_partids[cid][g] += 1

    def _best_partid(cid: str) -> str:
        counts = asker_partids.get(cid)
        if counts:
            return counts.most_common(1)[0][0]
        # Fallback: extract from name string e.g. "Ion Popescu - deputat PSD"
        name = asker_names.get(cid, "")
        m = re.search(r"-\s*(?:deputat|senator)\s+([A-ZĂÎȘȚŞŢ]{2,})", name)
        if m:
            return m.group(1)
        return "Neafiliat"

    top_askers = [
        {
            "canonical_id": cid,
            "name": asker_names[cid],
            "partid": _best_partid(cid),
            "total": cnt,
        }
        for cid, cnt in asker_counts.most_common(TOP_N)
    ]

    # ── Top ministries ──────────────────────────────────────────────────
    by_dest: dict[str, dict] = defaultdict(lambda: {"total": 0, "answered": 0})
    for r in rows:
        dest = _clean_dest(r.get("destinatar"))
        by_dest[dest]["total"] += 1
        if r.get("raspuns_primit"):
            by_dest[dest]["answered"] += 1

    top_dest = [
        {
            "destinatar": dest,
            "total": v["total"],
            "answered": v["answered"],
            "rate": round(v["answered"] / v["total"] * 100, 1) if v["total"] else 0,
        }
        for dest, v in sorted(by_dest.items(), key=lambda kv: -kv[1]["total"])
        if v["total"] >= 10
    ][:TOP_N]

    # ── Monthly trend ───────────────────────────────────────────────────
    by_month: dict[str, int] = defaultdict(int)
    for r in rows:
        if r.get("data_inregistrare"):
            by_month[r["data_inregistrare"][:7]] += 1

    monthly = [{"month": m, "count": c} for m, c in sorted(by_month.items())]

    # ── Output ──────────────────────────────────────────────────────────
    payload = {
        "meta": {
            **Meta(
                generated_at=datetime.now(UTC),
                source_url=(
                    f"https://endimion2k.github.io/cdep-api-poc/"
                    f"data/v1/interpelari/legislatura-{leg}.json"
                ),
                scraper_version="0.1.0",
                count=total,
            ).model_dump(mode="json"),
            "legislatura": leg,
        },
        "cards": {
            "total": total,
            "answered": answered,
            "answer_rate": round(answered / total * 100, 1) if total else 0,
            "avg_response_days": avg_days,
            "median_response_days": median_days,
        },
        "per_partid": per_partid,
        "top_askers": top_askers,
        "top_destinations": top_dest,
        "monthly": monthly,
    }

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"interpelari-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"OK leg {leg}: {total} interpelări · {answered} răspunsuri "
        f"({payload['cards']['answer_rate']}%) → {out_path}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    legs = ALL_LEGS if args.all else [args.leg]
    ret = 0
    for leg in legs:
        r = build_leg(leg)
        if r != 0 and not args.all:
            return r
        ret = ret or r
    return ret


if __name__ == "__main__":
    sys.exit(main())
