# Design Spec: Party Profile Page (`partid.html`)

**Date:** 2026-05-31
**Status:** Approved (auto-designed, unsupervised)

---

## Context

`deputat.html` shows a profile for one deputy. This page does the same for a party: aggregate stats, wealth summary, a sortable grid of all party deputies. URL pattern mirrors `deputat.html`: `partid.html?id=PSD&leg=2024`.

---

## Data Sources

All loaded in parallel on page load:

| File | Used for |
|---|---|
| `data/v1/stats/avere-deputies-{leg}.json` | Per-deputy wealth, `PARTIES` logo map |
| `data/v1/stats/activitate-deputies-{leg}.json` | Per-deputy activity |
| `data/v1/stats/avere-{leg}.json` | `per_partid` aggregate stats (medians, box plot) |
| `data/v1/deputati/legislatura-{leg}.json` | Full party name via `current_party` field |

---

## URL & Navigation

- URL: `partid.html?id=PSD&leg=2024`
- `id` is the short party code (PSD, PNL, USR, AUR, UDMR, SOS RO, UPR, Minoritati, Neafiliat)
- `leg` defaults to `2024`; leg-toggle causes full page reload (same as `deputat.html`)
- Navigation links: same header nav as all other pages; no active link
- Linking: `deputati-avere.html` and `deputati-activitate.html` can link here from party badges (future; not in scope)

---

## Page Sections

### 1. Profile Header

Grid: 120×120 logo | info column.

**Logo block**: `<img src="data/assets/imagini/partide/{logo}" onerror="…">` where `logo` comes from `PARTIES[partid]`. Fallback: a colored square with the party code initials.

**Info column**:
- `<h1>` — full party name (from deputati data, first match of `current_party` for this `partid`)
- Tags: `[PSD]` (blue pill, party code), `[N deputați]` (green pill), `[2024]` (gray pill)
- Bio row: "Grup parlamentar: …" (from `current_group` field of any matching deputy)

### 2. Activity Aggregate Cards

6 cards in `repeat(auto-fit, minmax(140px, 1fr))` grid. Computed by **summing** all activity fields across party deputies from `activitate-deputies`.

| Card | Value |
|---|---|
| Ședințe | sum `activitate_sedinte` |
| Luări cuvânt | sum `activitate_luari_cuvant` |
| Propuneri | sum `activitate_propuneri_legislative` |
| Legi | sum `activitate_legi_promulgate` |
| Întrebări | sum `activitate_intrebari_interpelari` |
| Declarații | sum `activitate_declaratii_politice` |

### 3. Wealth Summary Cards

From `avere-{leg}.json` `per_partid` entry matching this `partid`. If no entry found (e.g., party not in avere data), skip section.

| Card | Value |
|---|---|
| Median conturi | `median_conturi` RON |
| Median venituri | `median_venituri` RON |
| Median datorii | `median_datorii` RON |
| Total imobile | `total_imobile` |
| Total suprafată | `total_suprafata_mp` m² |

### 4. Deputies Grid

A sortable grid of all party deputies. Each deputy shown as a mini card:
- Photo (40×40 circle) or colored initials
- Name (link → `deputat.html?id={cdep_idm}&leg={leg}`)
- Judet tag (small green pill)
- Value label (the currently sorted metric)

**Sort buttons** (metric-btns style, same CSS):
- Avere: Ședințe · Propuneri · Legi · Venituri · Conturi
- Default sort: Ședințe desc

**Implementation**: merge `avere-deputies` and `activitate-deputies` on `cdep_idm`, filter to party, sort by selected metric.

Deputies with no avere data show `—` for wealth fields.

### 5. Wealth Distribution

Only shown if `conturi_values` array exists in `per_partid` entry and has ≥ 5 values.

Simple horizontal box plot: Q1–Q3 bar + median tick. Same `.bar-cell-track` / `.bar-cell-fill` pattern used in table view.

Show: min, Q1, median, Q3, max values as text labels below the bar. Label: "Distribuție conturi bancare (N deputați cu declarație)".

---

## Error Handling

- Unknown `id`: show error div "Partidul «{id}» nu a fost găsit."
- No deputies for party in selected leg: show "Niciun deputat găsit pentru {id} în legislatura {leg}."
- Missing avere-{leg}.json `per_partid` entry: skip sections 3 and 5 silently.

---

## CSS

Reuse all existing classes from `deputat.html` (`.profile`, `.photo`, `.tag`, `.act-card`, `.section`, etc.). No new CSS classes needed except:
- `.dep-mini-card` — flex row card for the deputies grid
- `.dep-mini-photo` — 40×40 circle

---

## Verification

1. `partid.html?id=PSD` — shows "Partidul Social Democrat", 92 deputies
2. `partid.html?id=USR` — shows USR logo, correct activity sums
3. Sort by Venituri — deputies re-sort, value labels update
4. Click a deputy card — navigates to `deputat.html?id=...`
5. `?id=UNKNOWN` — shows error
6. Leg toggle (2024/2020) — page reloads, data changes
