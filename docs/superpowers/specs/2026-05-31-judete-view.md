# Design Spec: Județe Comparison View (`judete.html`)

**Date:** 2026-05-31
**Status:** Approved (auto-designed, unsupervised)

---

## Context

A new visualization page where each circle (or table row) = a județ. Lets users compare counties by deputy count, activity, and wealth at a glance. Pattern mirrors `deputati-avere.html` and `deputati-activitate.html`.

---

## Data Sources

All loaded in parallel; joined client-side on `cdep_idm`:

| File | Used for |
|---|---|
| `data/v1/deputati/legislatura-{leg}.json` | judet, party, cdep_idm per deputy |
| `data/v1/stats/avere-deputies-{leg}.json` | wealth metrics per deputy |
| `data/v1/stats/activitate-deputies-{leg}.json` | activity metrics per deputy |

### Client-side aggregation

After join, group by `judet`. Normalize the long diaspora string `"- Circumscriptia Electorala…"` → `"Diaspora"`. Compute per-judet:

```
n               — number of deputies
dominant_party  — party code with most deputies in this judet
parties_map     — {partid: count} for party chips
med_sedinte     — median activitate_sedinte
med_propuneri   — median activitate_propuneri_legislative
med_venituri    — median venituri_ron (deputies with avere data only)
med_conturi     — median conturi_ron (deputies with avere data only)
```

Median computed only over non-null values; fallback 0.

---

## Metrics & Metric Buttons

5 metric buttons, same `.metric-btns` CSS as avere/activitate pages:

| Button | Label | Value |
|---|---|---|
| `n` | N dep. | county deputy count |
| `med_sedinte` | Ședințe | median ședințe |
| `med_propuneri` | Propuneri | median propuneri |
| `med_venituri` | Venituri | median venituri RON |
| `med_conturi` | Conturi | median conturi RON |

Default metric: `n` (deputy count).

---

## Toolbar

Left → right:
```
[⬤ Cercuri | ≡ Tabel]  [N dep.|Ședințe|Propuneri|Venituri|Conturi]  N județe  [2024|2020]
```

No party filter (judete page shows all deputies). No search.

---

## Circle View

Same `.circle-grid` layout used in deputati pages. One circle per județ.

- **Size**: proportional to selected metric value (same `circleSize(v, maxV)` formula; min 24px, max 90px for readability at 44 items)
- **Color**: `partyColor(judet.dominant_party)` — dominant party's hex
- **Label**: județ name, truncated to 12 chars (most fit; "Bistriţa-Năs." etc.)
- **Value line**: formatted value for selected metric (e.g., "29 dep.", "10 șed.", "332K RON")
- **No magnitude breaks** (judete page doesn't need them)

Click on a circle → navigates to `judete.html?judet={name}&leg={leg}` — same page with judet filter, showing a deputies panel (see Deputy Detail Panel below).

### URL State

Params: `metric`, `view`, `leg`, `judet` (selected judet for panel).
- `pushState` / `applyURLState` — same pattern as avere/activitate pages.

---

## Table View

Sortable table. Columns:

| Column | Class | Notes |
|---|---|---|
| Județ | sticky left | Name + dominant party color dot |
| N dep. | sortable | integer |
| Partid dom. | — | party code pill with color |
| Ședințe | sortable | median, integer |
| Propuneri | sortable | median, integer |
| Venituri | sortable | median RON, formatted |
| Conturi | sortable | median RON, formatted |

Same `.dep-table`, `.dep-table-wrap`, `.dep-table-th`, `.dep-table-td` CSS. Active sort column highlighted blue. Click `Județ` header → sort alphabetically.

Row click → same judet panel behavior as circle click.

---

## Deputy Detail Panel

When a județ is selected (via circle click, row click, or `?judet=` URL param):

A panel renders below the grid/table (not a modal):
```
── Suceava — 10 deputați ─────────────────────────────
[PSD ×3] [AUR ×4] [USR ×1] [PNL ×2]
┌────────────────────────────────────────────────────┐
│ [photo] Nume Deputat       PSD   10 șed.  276K RON │
│ [photo] Nume Deputat       AUR    4 șed.  215K RON │
│ …                                                   │
└────────────────────────────────────────────────────┘
```

Implementation: `<div id="judet-panel">` rendered below `#circle-grid`. Shows:
- Section heading: judet name + count
- Party breakdown pills (same style as party-dd chips in toolbar)
- List of deputies: photo circle, name (link → deputat.html), party pill, ședințe, venituri
- Deputies sorted by ședințe desc
- "×" close button top-right; also closes on clicking another judet or clicking the same judet again

Panel is part of the same `<div class="main">` container. No z-index overlay needed.

---

## No-Data Cases

- Deputies without judet: grouped as `"Diaspora"` (19 deputies in 2024)
- Deputies without avere data: excluded from median wealth calculations; `—` shown in table
- Leg 2020: same page works; different data files

---

## Page Structure

```html
<header> … nav … </header>
<div class="toolbar">
  <div class="toolbar-inner">
    [view-toggle] [metric-btns] [count-badge "N județe"] [leg-toggle]
  </div>
</div>
<div class="main">
  <h1>Județe — Camera Deputaților</h1>
  <p class="sub" id="page-sub">…</p>
  <div id="circle-grid" class="circle-grid">…</div>
  <div id="judet-panel" style="display:none">…</div>
</div>
<footer> … </footer>
```

---

## Navigation

Add "Județe" link to nav in `judete.html` itself and update nav in all existing pages to include it:
- `avere.html`, `deputati-avere.html`, `deputati-activitate.html`, `interpelari-stats.html`, `proiecte-stats.html`, `index.html`, `deputat.html`

---

## Verification

1. Page loads, 44 circles render (or 43 if Diaspora merged), sizes proportional to N dep.
2. Click "Ședințe" metric → circles resize by median ședințe
3. Click "Venituri" → circles resize, Diaspora stays small (low median)
4. Click circle "Cluj" → deputy panel opens below with Cluj deputies
5. Click same circle again → panel closes
6. Switch to table view → sortable table with all 7 columns
7. Sort by Venituri → table re-sorts
8. URL `?metric=med_venituri&view=table` → loads in that state
9. Leg 2020 toggle → reloads with 2020 data
