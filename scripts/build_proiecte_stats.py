"""Build agregat /stats/proiecte — statistici pentru dashboard-ul de proiecte legislative.

Output: data/v1/stats/proiecte-{leg}.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020]


def _extract_parties(initiator: str | None) -> list[str]:
    """Extract party short names from the initiator string."""
    if not initiator:
        return ["Neidentificat"]
    if "Guvern" in initiator:
        return ["Guvern"]
    found: list[str] = []
    for m in re.finditer(r"(?:deputati|senatori)\s+-\s+([A-ZĂÎȘŢŞȚRO ]{2,20}):", initiator):
        p = m.group(1).strip()
        if p not in found:
            found.append(p)
    return found or ["Neidentificat"]


def _norm_stadiu(row: dict) -> str:
    if row.get("lege_nr"):
        return "promulgat"
    s = (row.get("stadiu") or "").lower()
    if "respinge" in s or "încetat" in s or "incetat" in s:
        return "respins"
    if row.get("data_adoptare_cd") or row.get("data_adoptare_senat"):
        return "adoptat"
    return "in_lucru"


def build_leg(leg: int, root: Path = ROOT) -> int:
    src = root / "data" / "v1" / "proiecte" / f"legislatura-{leg}.json"
    if not src.exists():
        print(f"Lipsește {src}.", file=sys.stderr)
        return 1

    rows: list[dict] = json.loads(src.read_text(encoding="utf-8"))["data"]
    total = len(rows)

    # ── Stadiu overview ─────────────────────────────────────────────────
    by_stadiu: Counter = Counter(_norm_stadiu(r) for r in rows)
    by_tip: Counter = Counter(r.get("tip") or "necunoscut" for r in rows)

    # ── By party ────────────────────────────────────────────────────────
    party_stats: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "promulgate": 0, "adoptate": 0, "respinse": 0, "in_lucru": 0}
    )
    for r in rows:
        stadiu = _norm_stadiu(r)
        for p in _extract_parties(r.get("initiator")):
            ps = party_stats[p]
            ps["total"] += 1
            if stadiu == "promulgat":
                ps["promulgate"] += 1
            elif stadiu == "adoptat":
                ps["adoptate"] += 1
            elif stadiu == "respins":
                ps["respinse"] += 1
            else:
                ps["in_lucru"] += 1

    per_partid = [
        {
            "partid": p,
            **v,
            "rate_promulgate": round(v["promulgate"] / v["total"] * 100, 1) if v["total"] else 0,
        }
        for p, v in sorted(party_stats.items(), key=lambda kv: -kv[1]["total"])
        if v["total"] >= 5 and p not in ("Neidentificat",)
    ]

    # ── Monthly trend (by data_inregistrare_cd) ─────────────────────────
    by_month: dict[str, dict] = defaultdict(lambda: {"total": 0, "promulgate": 0})
    for r in rows:
        date_key = (r.get("data_inregistrare_cd") or r.get("data_prezentare") or "")[:7]
        if not date_key:
            continue
        by_month[date_key]["total"] += 1
        if _norm_stadiu(r) == "promulgat":
            by_month[date_key]["promulgate"] += 1

    monthly = [{"month": m, **v} for m, v in sorted(by_month.items())]

    # ── Top legislative domains (by urgency + camera_decizionala) ───────
    urgent = sum(1 for r in rows if r.get("procedura_urgenta"))
    camera_cd = Counter(r.get("camera_decizionala") or "Necunoscut" for r in rows)

    # ── Output ──────────────────────────────────────────────────────────
    payload = {
        "meta": {
            **Meta(
                generated_at=datetime.now(UTC),
                source_url=(
                    f"https://endimion2k.github.io/cdep-api-poc/"
                    f"data/v1/proiecte/legislatura-{leg}.json"
                ),
                scraper_version="0.1.0",
                count=total,
            ).model_dump(mode="json"),
            "legislatura": leg,
        },
        "cards": {
            "total": total,
            "promulgate": by_stadiu["promulgat"],
            "adoptate": by_stadiu["adoptat"],
            "respinse": by_stadiu["respins"],
            "in_lucru": by_stadiu["in_lucru"],
            "urgente": urgent,
            "rate_promulgate": round(by_stadiu["promulgat"] / total * 100, 1) if total else 0,
        },
        "by_tip": dict(by_tip),
        "per_partid": per_partid,
        "camera_decizionala": [
            {"camera": k, "total": v} for k, v in camera_cd.most_common()
        ],
        "monthly": monthly,
    }

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"proiecte-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"OK leg {leg}: {total} proiecte · {by_stadiu['promulgat']} promulgate "
        f"({payload['cards']['rate_promulgate']}%) → {out_path}"
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
