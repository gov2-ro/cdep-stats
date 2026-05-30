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
