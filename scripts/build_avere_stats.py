"""Build agregat /stats/avere — statistici pentru dashboard-ul de averi.

Citește indexul deja construit de ``build_declaratii_avere.py`` și emite un singur
JSON cu top-uri jurnalistice + agregate per partid + distribuții, gata de consumat
client-side de ``avere.html``.

Output: ``data/v1/stats/avere-{leg}.json``

Utilizare:
    python scripts/build_avere_stats.py              # legislatura 2024
    python scripts/build_avere_stats.py --leg 2020
    python scripts/build_avere_stats.py --all        # 2024 + 2020 + 2016

NOTĂ onestitate: avem valori monetare măsurate (conturi, venituri, datorii) dar doar
NUMĂRĂTORI pentru imobile/auto (fără valori). De aceea NU inventăm un "net worth" unic;
clasăm pe câmpurile reale măsurate și arătăm portofoliul de imobile ca număr.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from datetime import UTC, date as _date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020, 2016]
TOP_N = 15
MIN_PARTY_N = 3  # praguri sub care un partid nu e raportat (eșantion prea mic)

# Aliniat cu RATES_TO_RON din build_declaratii_avere.py — pentru nota de metodologie.
CAVEATS = (
    "Cifre extrase automat din PDF-urile ANI cu pdfplumber; pot conține erori de parsare. "
    "Sumele în valută sunt normalizate la RON la cursuri fixe (EUR 5.05, USD 4.50). "
    "Imobilele și autovehiculele sunt NUMĂRĂTORI (nu valori). "
    "Nu calculăm un 'net worth' unic — clasăm pe câmpurile reale măsurate."
)


def _quartiles(values: list[float]) -> dict[str, float]:
    """q1 / median / q3 / p90 pentru o listă de valori (gol → zerouri)."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {"q1": 0.0, "median": 0.0, "q3": 0.0, "p90": 0.0}
    n = len(vals)

    def pct(p: float) -> float:
        if n == 1:
            return vals[0]
        idx = p * (n - 1)
        lo = int(idx)
        frac = idx - lo
        hi = min(lo + 1, n - 1)
        return vals[lo] + (vals[hi] - vals[lo]) * frac

    return {
        "q1": round(pct(0.25), 2),
        "median": round(statistics.median(vals), 2),
        "q3": round(pct(0.75), 2),
        "p90": round(pct(0.90), 2),
    }


def _load_detail_extras(leg: int) -> dict[int, dict]:
    """Citește fișierele detaliu pentru câmpurile lipsă din index (datorii, suprafață, auto).

    Returnează ``{cdep_idm: {datorii, suprafata_mp, auto_count}}`` din ultima declarație.
    """
    detail_dir = ROOT / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}"
    extras: dict[int, dict] = {}
    if not detail_dir.is_dir():
        return extras
    for fpath in detail_dir.glob("*.json"):
        try:
            d = json.loads(fpath.read_text(encoding="utf-8"))["data"]
            declaratii = d.get("declaratii") or []
            if not declaratii:
                continue
            last = declaratii[-1]
            extras[d["cdep_idm"]] = {
                "datorii": last.get("datorii_total_ron", 0.0),
                "suprafata_mp": last.get("suprafata_total_mp", 0.0),
                "auto_count": last.get("auto_count", 0),
            }
        except (KeyError, json.JSONDecodeError):
            continue
    return extras


def _row(d: dict, value: float | int, extra: dict | None = None) -> dict:
    """Un rând standard de leaderboard."""
    row = {
        "cdep_idm": d["cdep_idm"],
        "nume": d["deputat_nume"],
        "partid": d.get("partid_short") or "Neafiliat",
        "value": round(value, 2) if isinstance(value, float) else value,
        "n_declaratii": d.get("n_declaratii", 0),
        "detail_url": d.get("detail_url")
        or f"declaratii-avere/legislatura-{d.get('legislatura')}/{d['cdep_idm']}.json",
    }
    if extra:
        row.update(extra)
    return row


def _board(rows: list[dict], reverse: bool, predicate=None) -> list[dict]:
    """Sortează rândurile (deja cu 'value') după value, filtrează, păstrează TOP_N."""
    items = sorted(rows, key=lambda r: r["value"], reverse=reverse)
    if predicate:
        items = [r for r in items if predicate(r)]
    return items[:TOP_N]


def _age_cohort(birth_date_str: str | None, ref_year: int) -> str | None:
    """Returns '50–54' bracket for age on Dec 31 of ref_year. None if missing."""
    if not birth_date_str:
        return None
    try:
        birth = _date.fromisoformat(birth_date_str)
        ref = _date(ref_year, 12, 31)
        # Year arithmetic avoids the leap-year drift of (ref - birth).days // 365
        age = ref.year - birth.year - ((ref.month, ref.day) < (birth.month, birth.day))
        start = (age // 5) * 5
        return f"{start}–{start + 4}"
    except (ValueError, TypeError):
        return None


def _pct_from_bottom(val: float, all_vals: list[float]) -> int:
    """Percentile rank 0-100. Higher = wealthier. Count of values strictly below val."""
    if not all_vals:
        return 0
    return round(sum(1 for v in all_vals if v < val) / len(all_vals) * 100)


def _rank_from_top(val: float, all_vals: list[float]) -> int:
    """1-indexed rank from top. Ties share the same rank."""
    return sum(1 for v in all_vals if v > val) + 1


def _load_deputati_lookup(leg: int) -> dict[str, dict]:
    """Returns {canonical_id: {birth_date, judet}} from deputati index."""
    dep_file = ROOT / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not dep_file.exists():
        return {}
    deps = json.loads(dep_file.read_text(encoding="utf-8")).get("data", [])
    return {
        d["id"]: {"birth_date": d.get("birth_date"), "judet": d.get("judet")}
        for d in deps
        if d.get("id")
    }


def _build_context(
    valid: list[dict],
    dep_lookup: dict[str, dict],
) -> dict[str, dict]:
    """Per-deputy ranking context for deputat.html.

    Records must already have ``_suprafata`` and ``_datorii`` attached
    (done by ``build_leg()`` before calling this).
    Mutates records in-place to add ``_birth_date``, ``_judet``, ``_age_cohort``.

    Returns ``{str(cdep_idm): {national, party, age, judet}}``.
    """
    # Attach deputati metadata
    leg_year: int = valid[0].get("legislatura", 2024) if valid else 2024
    for r in valid:
        info = dep_lookup.get(r.get("id", ""), {})
        r["_birth_date"] = info.get("birth_date")
        r["_judet"] = info.get("judet")
        r["_age_cohort"] = _age_cohort(r["_birth_date"], leg_year)

    METRICS: list[tuple[str, str]] = [
        ("active", "ultima_total_active_ron"),
        ("venituri", "ultima_venituri_ron"),
        ("imobile", "ultima_imobile_count"),
        ("suprafata", "_suprafata"),
    ]

    # National sorted lists for percentile computation (excludes datorii — handled separately)
    nat_sorted: dict[str, list[float]] = {
        key: sorted(float(r.get(field) or 0) for r in valid)
        for key, field in METRICS
    }
    # Datorii: only non-zero deputies participate in datorii ranking
    datorii_nonzero = sorted(float(r.get("_datorii") or 0) for r in valid if (r.get("_datorii") or 0) > 0)

    # All values for rank_from_top (active + venituri only)
    all_active = [float(r.get("ultima_total_active_ron") or 0) for r in valid]
    all_venituri = [float(r.get("ultima_venituri_ron") or 0) for r in valid]

    # Group records by party / age cohort / județ
    by_party: dict[str, list[dict]] = defaultdict(list)
    by_age: dict[str, list[dict]] = defaultdict(list)
    by_judet: dict[str, list[dict]] = defaultdict(list)
    for r in valid:
        by_party[r.get("partid_short") or "Neafiliat"].append(r)
        if r["_age_cohort"]:
            by_age[r["_age_cohort"]].append(r)
        if r["_judet"]:
            by_judet[r["_judet"]].append(r)

    def _group_pcts(group: list[dict], cdep_idm: int) -> dict:
        a_sorted = sorted(float(rec.get("ultima_total_active_ron") or 0) for rec in group)
        v_sorted = sorted(float(rec.get("ultima_venituri_ron") or 0) for rec in group)
        rec = next(x for x in group if x["cdep_idm"] == cdep_idm)
        return {
            "n": len(group),
            "active_pct": _pct_from_bottom(float(rec.get("ultima_total_active_ron") or 0), a_sorted),
            "venituri_pct": _pct_from_bottom(float(rec.get("ultima_venituri_ron") or 0), v_sorted),
        }

    result: dict[str, dict] = {}
    for r in valid:
        cdep_idm = r["cdep_idm"]

        # National percentiles
        national: dict = {"n": len(valid)}
        for key, field in METRICS:
            val = float(r.get(field) or 0)
            national[f"{key}_pct"] = _pct_from_bottom(val, nat_sorted[key])
        # Datorii ranked separately — zero debt is excluded from the ranking
        datorii_val = float(r.get("_datorii") or 0)
        national["datorii_pct"] = (
            _pct_from_bottom(datorii_val, datorii_nonzero) if datorii_val > 0 else None
        )
        national["active_rank"] = _rank_from_top(float(r.get("ultima_total_active_ron") or 0), all_active)
        national["venituri_rank"] = _rank_from_top(float(r.get("ultima_venituri_ron") or 0), all_venituri)

        # Group comparisons
        partid = r.get("partid_short") or "Neafiliat"
        party_data = {"name": partid, **_group_pcts(by_party[partid], cdep_idm)}

        cohort = r.get("_age_cohort")
        age_data = (
            {"cohort": cohort, **_group_pcts(by_age[cohort], cdep_idm)} if cohort else None
        )

        judet = r.get("_judet")
        judet_data = (
            {"name": judet, **_group_pcts(by_judet[judet], cdep_idm)} if judet else None
        )

        result[str(cdep_idm)] = {
            "national": national,
            "party": party_data,
            "age": age_data,
            "judet": judet_data,
        }

    return result


def build_leg(leg: int) -> int:
    index_file = ROOT / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}.json"
    if not index_file.exists():
        print(f"Lipsește {index_file}. Rulează întâi build_declaratii_avere.py --leg {leg}")
        return 1

    data = json.loads(index_file.read_text(encoding="utf-8"))["data"]
    valid = [d for d in data if d.get("n_declaratii", 0) > 0]
    extras = _load_detail_extras(leg)

    # Atașăm datorii/suprafață/auto din detalii (proxy 0 dacă lipsesc).
    for d in valid:
        ex = extras.get(d["cdep_idm"], {})
        d["_datorii"] = ex.get("datorii", 0.0)
        d["_suprafata"] = ex.get("suprafata_mp", 0.0)
        d["_auto"] = ex.get("auto_count", 0)

    # === Leaderboards (unghi jurnalistic) ===
    pos = lambda r: r["value"] > 0  # noqa: E731
    neg = lambda r: r["value"] < 0  # noqa: E731
    multi = lambda r: r["n_declaratii"] > 1  # noqa: E731
    leaderboards = {
        "top_conturi": _board(
            [_row(d, d.get("ultima_conturi_ron", 0.0)) for d in valid], True, pos
        ),
        "top_venituri": _board(
            [_row(d, d.get("ultima_venituri_ron", 0.0)) for d in valid], True, pos
        ),
        "top_datorii": _board([_row(d, d["_datorii"]) for d in valid], True, pos),
        "top_imobile": _board(
            [
                _row(
                    d,
                    d.get("ultima_imobile_count", 0),
                    {"suprafata_mp": round(d["_suprafata"], 1)},
                )
                for d in valid
            ],
            True,
            pos,
        ),
        "delta_crestere": _board(
            [_row(d, d.get("delta_conturi_ron", 0.0)) for d in valid],
            True,
            lambda r: pos(r) and multi(r),
        ),
        "delta_scadere": _board(
            [_row(d, d.get("delta_conturi_ron", 0.0)) for d in valid],
            False,
            lambda r: neg(r) and multi(r),
        ),
        "delta_imobile": _board(
            [_row(d, d.get("delta_imobile", 0)) for d in valid], True, pos
        ),
    }

    # === Agregate per partid (unghi cercetare) ===
    by_partid: dict[str, list[dict]] = defaultdict(list)
    for d in valid:
        by_partid[d.get("partid_short") or "Neafiliat"].append(d)

    per_partid = []
    for partid, items in sorted(by_partid.items(), key=lambda kv: -len(kv[1])):
        if len(items) < MIN_PARTY_N:
            continue
        conturi = [d.get("ultima_conturi_ron", 0.0) for d in items]
        venituri = [d.get("ultima_venituri_ron", 0.0) for d in items]
        datorii = [d["_datorii"] for d in items]
        per_partid.append(
            {
                "partid": partid,
                "n": len(items),
                "median_conturi": round(statistics.median(conturi), 2),
                "mean_conturi": round(statistics.mean(conturi), 2),
                "median_venituri": round(statistics.median(venituri), 2),
                "median_datorii": round(statistics.median(datorii), 2),
                "total_imobile": sum(d.get("ultima_imobile_count", 0) for d in items),
                "total_suprafata_mp": round(sum(d["_suprafata"] for d in items), 1),
                # Array brut pentru box-plot client-side.
                "conturi_values": [round(c, 2) for c in conturi],
            }
        )

    # === Distribuție generală ===
    distributie = {
        "conturi": _quartiles([d.get("ultima_conturi_ron", 0.0) for d in valid]),
        "venituri": _quartiles([d.get("ultima_venituri_ron", 0.0) for d in valid]),
    }

    # === Stat cards ===
    n_redflag = len(leaderboards["delta_scadere"]) + sum(
        1 for d in valid if d.get("delta_conturi_ron", 0.0) > 0 and d.get("n_declaratii", 0) > 1
    )
    cards = {
        "n_deputati": len(valid),
        "median_conturi": distributie["conturi"]["median"],
        "median_venituri": distributie["venituri"]["median"],
        "n_cu_evolutie": sum(1 for d in valid if d.get("n_declaratii", 0) > 1),
    }

    payload = {
        "meta": {
            **Meta(
                generated_at=datetime.now(UTC),
                source_url=(
                    "https://endimion2k.github.io/cdep-api-poc/"
                    f"data/v1/declaratii-avere/legislatura-{leg}.json"
                ),
                scraper_version="0.1.0",
                count=len(valid),
            ).model_dump(mode="json"),
            "caveats": CAVEATS,
            "legislatura": leg,
        },
        "cards": cards,
        "leaderboards": leaderboards,
        "per_partid": per_partid,
        "distributie": distributie,
    }

    out_dir = ROOT / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"avere-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK leg {leg}: {len(valid)} deputați · {len(per_partid)} partide → {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true", help="Build 2024 + 2020 + 2016")
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
