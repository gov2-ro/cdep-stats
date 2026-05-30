# Avere Ranking on Deputy Profile — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show percentile-bar wealth rankings on every deputy profile page (`deputat.html`), comparing each deputy against all peers nationally and within their party, age cohort, and județ.

**Architecture:** `build_avere_stats.py` gains two new helpers — `_load_deputati_lookup()` (reads the deputati index for birth_date + județ) and `_build_context()` (computes per-deputy percentile ranks across 5 metrics × 4 comparison groups) — and emits a second output file `avere-context-{leg}.json`. `deputat.html` fetches this file alongside the existing per-deputy detail JSON and renders a new `renderAvereRanking()` section inserted after the existing stat cards.

**Tech Stack:** Python 3.11+, pytest, vanilla JS, no new dependencies.

---

## File Map

| File | Change |
|---|---|
| `scripts/build_avere_stats.py` | Add `_load_deputati_lookup()`, `_age_cohort()`, `_pct_from_bottom()`, `_rank_from_top()`, `_build_context()`; wire into `build_leg()` |
| `tests/test_avere_context.py` | New — unit tests for all helpers and `_build_context()` |
| `deputat.html` | Add `renderAvereRanking()`, CSS, update Promise.all fetch, update `renderAvere()` call |
| `docs/activity-log.md` | New entry |

---

### Task 1: Helper functions + unit tests in `build_avere_stats.py`

**Files:**
- Modify: `scripts/build_avere_stats.py`
- Create: `tests/test_avere_context.py`

- [ ] **Step 1: Add four pure helper functions to `build_avere_stats.py`**

Insert after the `_board()` function (line ~118), before `build_leg()`:

```python
from datetime import date as _date  # add to top-level imports block


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


def _pct_from_bottom(val: float, sorted_vals: list[float]) -> int:
    """Percentile rank 0-100. Higher = wealthier. Count of values strictly below val."""
    if not sorted_vals:
        return 0
    return round(sum(1 for v in sorted_vals if v < val) / len(sorted_vals) * 100)


def _rank_from_top(val: float, all_vals: list[float]) -> int:
    """1-indexed rank from top. Ties share the same rank."""
    return sum(1 for v in all_vals if v > val) + 1


def _load_deputati_lookup(leg: int) -> dict[str, dict]:
    """Returns {canonical_id: {birth_date, judet}} from deputati index."""
    dep_file = ROOT / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not dep_file.exists():
        return {}
    deps = json.loads(dep_file.read_text(encoding="utf-8"))["data"]
    return {
        d["id"]: {"birth_date": d.get("birth_date"), "judet": d.get("judet")}
        for d in deps
        if d.get("id")
    }
```

Note: `date` is already imported as `from datetime import UTC, datetime` — add `date` to that import: `from datetime import UTC, date as _date, datetime`.

- [ ] **Step 2: Write unit tests in `tests/test_avere_context.py`**

```python
"""Tests for avere context helpers in build_avere_stats."""

from __future__ import annotations

import importlib.util
import json
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
```

- [ ] **Step 3: Run tests to confirm they pass**

```bash
PYTHONPATH=. pytest tests/test_avere_context.py -v
```

Expected: all 11 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_avere_stats.py tests/test_avere_context.py
git commit -m "feat(avere-context): add ranking helper functions with tests"
```

---

### Task 2: `_build_context()` function + tests

**Files:**
- Modify: `scripts/build_avere_stats.py`
- Modify: `tests/test_avere_context.py`

- [ ] **Step 1: Add `_build_context()` to `build_avere_stats.py`**

Insert after `_load_deputati_lookup()`:

```python
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
        ("datorii", "_datorii"),
    ]

    # National sorted lists for percentile computation
    nat_sorted: dict[str, list[float]] = {
        key: sorted(float(r.get(field) or 0) for r in valid)
        for key, field in METRICS
    }
    # Datorii: only non-zero deputies participate in datorii ranking
    datorii_nonzero = sorted(v for v in nat_sorted["datorii"] if v > 0)

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
            if key == "datorii":
                national["datorii_pct"] = (
                    _pct_from_bottom(val, datorii_nonzero) if val > 0 else None
                )
            else:
                national[f"{key}_pct"] = _pct_from_bottom(val, nat_sorted[key])
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
```

- [ ] **Step 2: Add `_build_context()` integration tests to `tests/test_avere_context.py`**

Append to the existing test file:

```python
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
    # aaa and ccc both born ~1974 → cohort "50-54" in 2024
    assert result["1"]["age"]["cohort"] == "50–54"
    assert result["3"]["age"]["cohort"] == "50–54"
    # bbb born 1980 → cohort "40-44"
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
```

- [ ] **Step 3: Run all tests**

```bash
PYTHONPATH=. pytest tests/test_avere_context.py -v
```

Expected: all 22 tests PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_avere_stats.py tests/test_avere_context.py
git commit -m "feat(avere-context): add _build_context() with full test coverage"
```

---

### Task 3: Wire into `build_leg()` + emit `avere-context-{leg}.json`

**Files:**
- Modify: `scripts/build_avere_stats.py`

- [ ] **Step 1: Add deputati lookup and context emission to `build_leg()`**

In `build_leg()`, after the existing `extras` loop (after line ~136 where `d["_auto"]` is set), add:

```python
    # === Avere context (ranking per deputy) ===
    dep_lookup = _load_deputati_lookup(leg)
    context_deputies = _build_context(valid, dep_lookup)

    context_payload = {
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
            "legislatura": leg,
        },
        "deputies": context_deputies,
    }

    ctx_path = out_dir / f"avere-context-{leg}.json"
    ctx_path.write_text(
        json.dumps(context_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"OK context leg {leg}: {len(context_deputies)} deputies → {ctx_path}")
```

Place this block right before the existing `print(f"OK leg {leg}: ...")` line. Also ensure `out_dir` is accessible at this point — it is, as `out_dir` is defined earlier in `build_leg()`.

- [ ] **Step 2: Run the build and spot-check output**

```bash
PYTHONPATH=. python scripts/build_avere_stats.py --leg 2024
```

Expected output includes two lines:
```
OK leg 2024: 332 deputați · N partide → data/v1/stats/avere-2024.json
OK context leg 2024: 332 deputies → data/v1/stats/avere-context-2024.json
```

Then spot-check Iordache Ion (cdep_idm=153):
```bash
python3 -c "
import json
d = json.load(open('data/v1/stats/avere-context-2024.json'))['deputies']['153']
print('national active_rank:', d['national']['active_rank'])
print('judet:', d['judet'])
print('party:', d['party']['name'])
print('age cohort:', d['age']['cohort'] if d['age'] else None)
"
```

Expected: `active_rank` is a low number (top ~10 given ~2M RON active); `judet.name` = "Ilfov" (or similar); `party.name` = "PNL".

- [ ] **Step 3: Run full test suite to confirm nothing broken**

```bash
PYTHONPATH=. pytest -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add scripts/build_avere_stats.py data/v1/stats/avere-context-2024.json
git commit -m "feat(avere-context): emit avere-context-{leg}.json from build_avere_stats"
```

---

### Task 4: `deputat.html` — fetch, render, CSS

**Files:**
- Modify: `deputat.html`

- [ ] **Step 1: Add CSS for ranking section**

In `deputat.html`, append inside the `<style>` block (before the closing `</style>` tag at line ~79):

```css
.rank-bar-row{margin-bottom:14px}
.rank-bar-header{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:5px}
.rank-bar-label{font-size:13px;color:var(--text)}
.rank-bar-value{font-size:12px;font-weight:600}
.rank-bar-track{background:var(--bg3);border-radius:4px;height:7px;position:relative}
.rank-bar-fill{height:100%;border-radius:4px;opacity:0.75}
.rank-bar-median{position:absolute;top:-3px;left:50%;width:1.5px;height:13px;background:var(--border2);border-radius:1px}
.rank-chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px;padding-top:14px;border-top:1px solid var(--border)}
.rank-chip{background:var(--bg2);border-radius:var(--radius-sm);padding:8px 12px}
.rank-chip-label{font-size:10px;color:var(--text3);margin-bottom:3px;text-transform:uppercase;letter-spacing:0.4px}
.rank-chip-vals{font-size:12px;color:var(--text)}
```

- [ ] **Step 2: Add `renderAvereRanking()` function**

In `deputat.html`, insert the following function before the existing `function renderAvere(avere)` (i.e., before line 139):

```javascript
function renderAvereRanking(ctx) {
  if (!ctx) return '';
  const n = ctx.national.n;
  const METRICS = [
    { key: 'active',    label: 'Active lichide totale', color: 'var(--blue)' },
    { key: 'venituri',  label: 'Venituri anuale',       color: 'var(--green)' },
    { key: 'imobile',   label: 'Nr. imobile',           color: 'var(--text2)' },
    { key: 'suprafata', label: 'Suprafață totală',       color: 'var(--text2)' },
    { key: 'datorii',   label: 'Datorii',               color: 'var(--text2)' },
  ];

  const bars = METRICS.map(({ key, label, color }) => {
    const pct = ctx.national[`${key}_pct`];
    const rank = key === 'active' ? ctx.national.active_rank
               : key === 'venituri' ? ctx.national.venituri_rank : null;

    if (pct === null || pct === undefined) {
      return `<div class="rank-bar-row">
        <div class="rank-bar-header">
          <span class="rank-bar-label">${label}</span>
          <span class="rank-bar-value" style="color:var(--text3);font-style:italic">${key === 'datorii' ? 'nu figurează' : '—'}</span>
        </div>
        <div class="rank-bar-track"><div class="rank-bar-fill" style="width:0%"></div><div class="rank-bar-median"></div></div>
      </div>`;
    }

    const topPct = Math.max(1, 100 - pct);
    const rankText = rank ? ` · #${rank} din ${n}` : '';
    return `<div class="rank-bar-row">
      <div class="rank-bar-header">
        <span class="rank-bar-label">${label}</span>
        <span class="rank-bar-value" style="color:${color}">top ${topPct}%${rankText}</span>
      </div>
      <div class="rank-bar-track">
        <div class="rank-bar-fill" style="width:${pct}%;background:${color}"></div>
        <div class="rank-bar-median"></div>
      </div>
    </div>`;
  }).join('');

  const chips = [
    ctx.party && ctx.party.n >= 3
      ? `<div class="rank-chip"><div class="rank-chip-label">față de ${ctx.party.name} (${ctx.party.n} dep.)</div><div class="rank-chip-vals">active: top ${Math.max(1, 100 - ctx.party.active_pct)}% · venituri: top ${Math.max(1, 100 - ctx.party.venituri_pct)}%</div></div>`
      : '',
    ctx.age && ctx.age.n >= 3
      ? `<div class="rank-chip"><div class="rank-chip-label">față de ${ctx.age.cohort} ani (${ctx.age.n} dep.)</div><div class="rank-chip-vals">active: top ${Math.max(1, 100 - ctx.age.active_pct)}% · venituri: top ${Math.max(1, 100 - ctx.age.venituri_pct)}%</div></div>`
      : '',
    ctx.judet && ctx.judet.n >= 3
      ? `<div class="rank-chip"><div class="rank-chip-label">față de ${ctx.judet.name} (${ctx.judet.n} dep.)</div><div class="rank-chip-vals">active: top ${Math.max(1, 100 - ctx.judet.active_pct)}% · venituri: top ${Math.max(1, 100 - ctx.judet.venituri_pct)}%</div></div>`
      : '',
  ].filter(Boolean).join('');

  return `<div class="section">
    <h2>Ranking național <span style="font-weight:400;color:var(--text3);font-size:13px">· ${n} deputați cu declarație</span></h2>
    <div>${bars}</div>
    ${chips ? `<div class="rank-chips">${chips}</div>` : ''}
  </div>`;
}
```

- [ ] **Step 3: Update `renderAvere()` signature and inject ranking**

Change the function signature on line 139:
```javascript
// before:
function renderAvere(avere) {
// after:
function renderAvere(avere, ctx = null) {
```

Change the return statement at the end of `renderAvere()` (line ~256):
```javascript
// before:
  return sec1 + sec2 + sec3 + sec4 + sec5;
// after:
  return sec1 + renderAvereRanking(ctx) + sec2 + sec3 + sec4 + sec5;
```

- [ ] **Step 4: Update `loadDeputat()` to fetch avere-context and pass it through**

In `loadDeputat()`, locate the variable declaration on line ~276:
```javascript
// before:
  let dep, allInterpelari, allMotiuni, avereResp;
  try {
    const [depResp, intResp, motResp, avereJson] = await Promise.all([
      fetch(jsonUrl).then(r => r.json()),
      fetch(`data/v1/interpelari/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/motiuni/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/declaratii-avere/legislatura-${leg}/${parseInt(id)}.json`).then(r => r.json()).catch(() => null),
    ]);
    avereResp = avereJson;
```

Replace with:
```javascript
  let dep, allInterpelari, allMotiuni, avereResp, avereCtx = null;
  try {
    const [depResp, intResp, motResp, avereJson, ctxJson] = await Promise.all([
      fetch(jsonUrl).then(r => r.json()),
      fetch(`data/v1/interpelari/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/motiuni/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/declaratii-avere/legislatura-${leg}/${parseInt(id)}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/stats/avere-context-${leg}.json`).then(r => r.json()).catch(() => null),
    ]);
    avereResp = avereJson;
    avereCtx = ctxJson?.deputies?.[String(parseInt(id))] ?? null;
```

- [ ] **Step 5: Pass `avereCtx` to `renderAvere()` at the call site**

Find line ~384:
```javascript
// before:
    ${renderAvere(avereResp)}
// after:
    ${renderAvere(avereResp, avereCtx)}
```

- [ ] **Step 6: Commit**

```bash
git add deputat.html
git commit -m "feat(deputat): add avere ranking section with percentile bars"
```

---

### Task 5: Smoke test + activity log

**Files:**
- Modify: `docs/activity-log.md`

- [ ] **Step 1: Serve and open a deputy with rich avere data**

```bash
python -m http.server 8000
```

Open: `http://localhost:8000/deputat.html?id=153&leg=2024`

Verify:
- After the 8 stat cards, a "Ranking național" section appears
- 5 bars render with colored fills (active and venituri in blue/green, others grey)
- National median marker (vertical tick) is visible at midpoint of each bar
- "top X%" labels appear top-right of each bar
- active and venituri bars also show "#N din 332"
- 3 group chips appear below (party / age / județ)
- Zero-datorii shows "nu figurează" italic, empty bar
- No console errors (open DevTools → Console)

- [ ] **Step 2: Test a deputy from a small județ**

Check a deputy whose județ has fewer than 3 deputies with avere data. The județ chip should be absent. To find one:

```bash
python3 -c "
import json
ctx = json.load(open('data/v1/stats/avere-context-2024.json'))['deputies']
small = [(k, v['judet']) for k, v in ctx.items() if v.get('judet') and v['judet']['n'] < 3]
print(small[:3])
"
```

Open that deputy's profile and confirm no județ chip appears.

- [ ] **Step 3: Test dark mode**

Open the profile page and toggle dark mode (system preference or browser DevTools). Verify the bars, chips, and labels are readable against the dark background.

- [ ] **Step 4: Add activity log entry**

In `docs/activity-log.md`, under the existing most-recent entry, add:

```markdown
### 2026-05-30 — Avere ranking section on deputy profile pages

**What was done**
- Extended `scripts/build_avere_stats.py` with four new helpers: `_load_deputati_lookup()`, `_age_cohort()`, `_pct_from_bottom()`, `_rank_from_top()`, and the main `_build_context()` function.
- New output `data/v1/stats/avere-context-{leg}.json`: per-deputy percentile ranks across 5 metrics (active, venituri, imobile, suprafata, datorii) × 4 comparison groups (national, party, age cohort, județ).
- `deputat.html` now fetches `avere-context-{leg}.json` and renders a ranking section between the stat cards and detail lists: 5 percentile bars (with national median marker) + group comparison chips.
- 22 unit tests added in `tests/test_avere_context.py`.

**Decisions**
- Zero-datorii deputies excluded from datorii ranking (0 = no debt, not last place).
- Group chips hidden when N < 3 (too small to be statistically meaningful).
- `avere-context-{leg}.json` is a separate file from `avere-{leg}.json` to keep both files small and focused.
- Age cohorts are 5-year brackets computed at December 31 of the legislature's opening year.
```

- [ ] **Step 5: Final commit**

```bash
git add docs/activity-log.md
git commit -m "docs: activity log entry for avere ranking feature"
```
