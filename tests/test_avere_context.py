"""Tests for avere context helpers in build_avere_stats."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "build_avere_stats", ROOT / "scripts" / "build_avere_stats.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_module()


# ── _age_cohort ────────────────────────────────────────────────────────────────

def test_age_cohort_basic(mod):
    assert mod._age_cohort("1974-01-01", 2024) == "50–54"


def test_age_cohort_boundary(mod):
    # born Dec 31 1979 → turns 45 exactly on Dec 31 2024 → cohort 45-49
    assert mod._age_cohort("1979-12-31", 2024) == "45–49"


def test_age_cohort_none_if_missing(mod):
    assert mod._age_cohort(None, 2024) is None
    assert mod._age_cohort("", 2024) is None


# ── _pct_from_bottom ──────────────────────────────────────────────────────────

def test_pct_lowest(mod):
    assert mod._pct_from_bottom(50.0, [50.0, 100.0, 300.0]) == 0


def test_pct_middle(mod):
    assert mod._pct_from_bottom(100.0, [50.0, 100.0, 300.0]) == 33


def test_pct_highest(mod):
    assert mod._pct_from_bottom(300.0, [50.0, 100.0, 300.0]) == 67


def test_pct_empty(mod):
    assert mod._pct_from_bottom(100.0, []) == 0


# ── _rank_from_top ────────────────────────────────────────────────────────────

def test_rank_top(mod):
    assert mod._rank_from_top(300.0, [50.0, 100.0, 300.0]) == 1


def test_rank_middle(mod):
    assert mod._rank_from_top(100.0, [50.0, 100.0, 300.0]) == 2


def test_rank_last(mod):
    assert mod._rank_from_top(50.0, [50.0, 100.0, 300.0]) == 3


def test_rank_tie(mod):
    # Both 100.0 values share rank 1
    assert mod._rank_from_top(100.0, [100.0, 100.0, 50.0]) == 1


# ── _build_context ────────────────────────────────────────────────────────────

def _make_records(overrides=None):
    """Minimal valid records for _build_context. _suprafata and _datorii pre-attached."""
    base = [
        {
            "cdep_idm": 1, "id": "aaa", "legislatura": 2024,
            "partid_short": "PSD", "n_declaratii": 1,
            "ultima_total_active_ron": 300.0, "ultima_venituri_ron": 150.0,
            "ultima_imobile_count": 5, "_suprafata": 400.0, "_datorii": 50000.0,
        },
        {
            "cdep_idm": 2, "id": "bbb", "legislatura": 2024,
            "partid_short": "PSD", "n_declaratii": 1,
            "ultima_total_active_ron": 100.0, "ultima_venituri_ron": 50.0,
            "ultima_imobile_count": 2, "_suprafata": 200.0, "_datorii": 0.0,
        },
        {
            "cdep_idm": 3, "id": "ccc", "legislatura": 2024,
            "partid_short": "PNL", "n_declaratii": 1,
            "ultima_total_active_ron": 50.0, "ultima_venituri_ron": 200.0,
            "ultima_imobile_count": 1, "_suprafata": 100.0, "_datorii": 0.0,
        },
    ]
    if overrides:
        for i, o in enumerate(overrides):
            base[i].update(o)
    return base


def _make_dep_lookup():
    return {
        "aaa": {"birth_date": "1974-01-01", "judet": "Ilfov"},
        "bbb": {"birth_date": "1980-06-15", "judet": "Cluj"},
        "ccc": {"birth_date": "1974-05-20", "judet": "Ilfov"},
    }


def test_build_context_keys_are_str_cdep_idm(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    assert set(result.keys()) == {"1", "2", "3"}


def test_build_context_national_n(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    assert result["1"]["national"]["n"] == 3


def test_build_context_national_active_rank(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # cdep_idm=1 has highest active (300) → rank 1
    assert result["1"]["national"]["active_rank"] == 1
    # cdep_idm=3 has lowest active (50) → rank 3
    assert result["3"]["national"]["active_rank"] == 3


def test_build_context_datorii_zero_is_null(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # cdep_idm=2 and cdep_idm=3 have _datorii=0 → datorii_pct must be None
    assert result["2"]["national"]["datorii_pct"] is None
    assert result["3"]["national"]["datorii_pct"] is None


def test_build_context_datorii_nonzero_ranked(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # cdep_idm=1 has only non-zero datorii → pct_from_bottom in [50000] = 0
    assert result["1"]["national"]["datorii_pct"] == 0


def test_build_context_party_grouping(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # PSD has 2 members; PNL has 1
    assert result["1"]["party"]["name"] == "PSD"
    assert result["1"]["party"]["n"] == 2
    assert result["3"]["party"]["name"] == "PNL"
    assert result["3"]["party"]["n"] == 1


def test_build_context_age_cohort_attached(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # aaa and ccc both born ~1974 → cohort "50–54" in 2024
    assert result["1"]["age"]["cohort"] == "50–54"
    assert result["3"]["age"]["cohort"] == "50–54"
    # bbb born 1980-06-15 → age 44 → cohort "40–44"
    assert result["2"]["age"]["cohort"] == "40–44"


def test_build_context_judet_grouping(mod):
    result = mod._build_context(_make_records(), _make_dep_lookup())
    # aaa and ccc are in Ilfov (n=2); bbb in Cluj (n=1)
    assert result["1"]["judet"]["name"] == "Ilfov"
    assert result["1"]["judet"]["n"] == 2
    assert result["2"]["judet"]["name"] == "Cluj"
    assert result["2"]["judet"]["n"] == 1


def test_build_context_missing_dep_lookup(mod):
    # Deputy with no match in dep_lookup → age=None, judet=None
    records = _make_records()
    result = mod._build_context(records, {})  # empty lookup
    assert result["1"]["age"] is None
    assert result["1"]["judet"] is None
