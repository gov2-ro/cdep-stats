# Design Spec: Avere Comparison & Ranking on Deputy Profile

**Date:** 2026-05-30  
**Status:** Approved

---

## Context

The deputy profile page (`deputat.html`) already shows the full wealth declaration in detail. This feature adds a **ranking section** right after the existing stat cards that answers: *"Is this deputy unusually wealthy compared to their peers?"*

Audience: journalists and researchers who need context, not just raw numbers.

---

## Visual Design

**Format:** Percentile bars — horizontal fill bars (0 → max) with a national median marker. Each bar shows `top X% · #N din 332` in the top-right corner. Color: blue for monetary metrics, muted grey for counts.

**Position:** Immediately after the existing 8-card stat grid, before the imobile/vehicule detail lists.

**5 metrics shown:**
1. Active lichide totale (`ultima_total_active_ron`)
2. Venituri anuale (`ultima_venituri_ron`)
3. Nr. imobile (`ultima_imobile_count`)
4. Suprafață totală (`suprafata_total_mp` — from detail file)
5. Datorii (`ultima_datorii_ron`) — zero case shows "0 RON · nu figurează", bar empty

**Group comparison badges** below the bars (3 chips):
- "față de {partid} ({N} dep.)" — active: top X% · venituri: top Y%
- "față de {cohortă} ani ({N} dep.)" — active: top X% · venituri: top Y%
- "față de {județ} ({N} dep.)" — active: top X% · venituri: top Y%

Badge for a group with N < 3 is omitted (too small to be meaningful).

---

## Data Architecture

### New file: `data/v1/stats/avere-context-{leg}.json`

Built by extending `scripts/build_avere_stats.py`. Structure:

```json
{
  "meta": { "generated_at": "...", "leg": 2024, "n": 332 },
  "deputies": {
    "153": {
      "national": {
        "n": 332,
        "active_pct": 96,
        "venituri_pct": 92,
        "imobile_pct": 82,
        "suprafata_pct": 79,
        "datorii_pct": 0,
        "active_rank": 13,
        "venituri_rank": 26
      },
      "party": { "name": "PNL", "n": 65, "active_pct": 94, "venituri_pct": 91 },
      "age":   { "cohort": "50–54", "n": 44, "active_pct": 93, "venituri_pct": 89 },
      "judet": { "name": "Ilfov", "n": 8, "active_pct": 98, "venituri_pct": 99 }
    }
  }
}
```

Key in `deputies` is `cdep_idm` as a string.

**Percentile definition:** `pct = round((rank_asc - 1) / n * 100)` where rank_asc=1 is lowest. "top X%" displayed as `100 - pct`. Ties get the same rank. Deputies with a null value for a metric get `pct = null` (bar omitted). **Exception for datorii:** value=0 is also treated as null ("nu figurează") since zero debt is not a bottom-of-ranking reading — only deputies with positive debt participate in the datorii ranking.

**Age cohorts:** 5-year brackets by age on December 31st of the legislature's opening year (e.g., 2024 legislature → age at 2024-12-31). Bracket labels: "45–49", "50–54", etc. Needs join with `deputati/legislatura-{leg}.json` on `id` (both files use `id` as the canonical deputy identifier) to get `birth_date`.

**Group comparisons (party/age/județ):** Only `active_pct` and `venituri_pct` are shown in badges — the two most interpretable monetary metrics. Percentile is within the group, not national.

---

## Build Script Changes (`scripts/build_avere_stats.py`)

1. **Import** `deputati/legislatura-{leg}.json` and build a lookup `{canonical_id → {birth_date, judet}}`. The avere summary has `id` (= `deputat_canonical_id`) which maps to `id` in the deputati index.

2. **Extend `_load_detail_extras()`** — already returns `{cdep_idm: {datorii, suprafata_mp, auto_count}}`. No change needed here; this data is already available when building the main stats.

3. **New function `_build_context(records, deputati_lookup, extras)`** — takes the full list of avere summary records enriched with extras, returns the `deputies` dict. For each of the 5 metrics:
   - Compute sorted ranking nationally
   - Compute sorted ranking per party, per age cohort, per județ
   - Emit percentile values per deputy

4. **Write** `data/v1/stats/avere-context-{leg}.json` alongside the existing `avere-{leg}.json`.

5. **No schema changes** — all fields are derived from existing data.

---

## `deputat.html` Changes

1. **Fetch `avere-context-{leg}.json`** in the existing `Promise.all(...)` chain. Key the result by `cdep_idm` (string) to get the current deputy's entry.

2. **Pass `context` to `renderAvere(avere, context)`** — second parameter, nullable. If missing or null, the ranking section is simply not rendered (graceful degradation).

3. **New `renderAvereRanking(context)` helper** — returns the HTML string for the ranking section:
   - A titled card container (`.avere-ranking-card`)
   - 5 bar rows using the existing `.activitate` / `.act-card` style vocabulary
   - Group comparison chip row below

4. **CSS additions** (inline in `deputat.html`'s `<style>` block):
   - `.rank-bar-track` — grey background track
   - `.rank-bar-fill` — colored fill, width set via inline style `width: {pct}%`
   - `.rank-bar-median` — 1.5px vertical tick at `left: 50%`
   - `.rank-chip` — small badge for group comparisons (matches existing `.tag` pattern)

---

## i18n

New keys to add to `i18n.js`:
- `rank_section_title`: "Ranking național · {n} deputați" / "National ranking · {n} deputies"
- `rank_vs_party`: "față de {partid}" / "vs. {party}"
- `rank_vs_age`: "față de {cohort} ani" / "vs. age {cohort}"
- `rank_vs_judet`: "față de {judet}" / "vs. {judet} county"
- `rank_top`: "top {pct}%" / "top {pct}%"
- `rank_nodatorii`: "nu figurează" / "not declared"

---

## Validation / `validate_data.py`

Register `data/v1/stats/avere-context-{leg}.json` as an expected output path.

---

## Out of Scope

- Suprafata/imobile/datorii rankings within groups (badges show active + venituri only; national bars show all 5)
- Trend/delta percentiles (e.g., "biggest grower")
- 2020 context (only 2024 for now; build script supports `--leg`)
- Gender breakdown

---

## Verification

1. `PYTHONPATH=. python scripts/build_avere_stats.py --leg 2024` → both `avere-2024.json` and `avere-context-2024.json` emitted
2. `avere-context-2024.json`: spot-check Iordache Ion (idm=153) — `active_rank` should be near top given known ~2M RON; `judet` = "Ilfov"
3. `PYTHONPATH=. python scripts/validate_data.py` passes
4. `ruff check scripts/build_avere_stats.py && ruff format --check`
5. Serve locally → open `deputat.html?id=153&leg=2024` → ranking section visible after stat cards, 5 bars render, 3 group chips appear, no console errors
6. Open a deputy with zero datorii → datorii bar shows "nu figurează" gracefully
7. Open a deputy from a small județ (N<3) → that chip is absent
