# Design Spec: Deputies Avere Dashboard (`deputati-avere.html`)

**Date:** 2026-05-28  
**Status:** Approved

---

## Context

The existing `avere.html` is an aggregate dashboard (leaderboards, party-level stats). This new page adds a per-deputy visual view: every deputy rendered as a circle sized by a selected wealth metric, with their portrait photo and party badge. Goal is journalistic impact — inequality and party distribution visible at a glance.

---

## Architecture

### Data pipeline (new build step)

**Script:** `scripts/build_avere_deputies.py`  
**Output:** `data/v1/stats/avere-deputies-{leg}.json`

Joins three sources:
1. `data/v1/declaratii-avere/legislatura-{leg}.json` — avere index (cdep_idm, deputat_nume, partid_short, ultima_conturi_ron, ultima_venituri_ron, ultima_imobile_count)
2. `data/v1/declaratii-avere/legislatura-{leg}/{cdep_idm}.json` — individual files for suprafata_total_mp, auto_count, datorii_total_ron (from latest declaratie)
3. `data/v1/deputati/legislatura-{leg}.json` — joined on cdep_idm for `image` URL

Per-deputy record shape:
```json
{
  "cdep_idm": 115,
  "name": "Gavrilescu Grațiela",
  "partid": "PSD",
  "image": "https://www.cdep.ro/parlamentari/l2024/GavrilescuGratiela.JPG",
  "venituri_ron": 421513,
  "conturi_ron": 225060,
  "imobile_count": 4,
  "suprafata_mp": 36802,
  "auto_count": 7,
  "datorii_ron": 48508
}
```

Null values are preserved as `null` (deputy filed no declaration or field not parsed).

**Party icon mapping:** `data/assets/legenda-partide.csv` is read at build time. The mapping `partid_short → logo filename` is emitted as a top-level `parties` dict in the JSON output:
```json
{
  "parties": { "PSD": "PSD.jpg", "PNL": "PNL.jpg", "USR": "USR.jpg", … },
  "deputies": [ … ]
}
```
Icons are served at `data/assets/imagini/partide/{logo}`. The page builds `<img src="data/assets/imagini/partide/${PARTIES[d.partid]}">` for each badge.

---

## Page: `deputati-avere.html`

Standalone page, same header/footer pattern as other pages. Vanilla HTML/CSS/JS, no framework. Loads one JSON file: `data/v1/stats/avere-deputies-2024.json`.

### Toolbar (sticky)

| Control | Detail |
|---|---|
| View toggle | `○ Cercuri` (active) · `▦ Liste` (disabled, future) |
| Metric select | Dropdown: Venituri anuale · Conturi bancare · Nr. imobile · Suprafață terenuri (mp) · Nr. autovehicule · Datorii |
| Party filter | Chip per party, each showing logo + short name; click toggles inclusion; all active by default |
| Search | Text input, filters by deputy name client-side |
| Count badge | `N deputați` (updates with filter) |

### Circle grid

Layout: `display:flex; flex-wrap:wrap; align-items:center; gap:10px; padding:16px`  
Deputies sorted descending by selected metric (null values at end).

**Per-deputy item:**
```
┌─────────────┐
│  [photo or  │  ← circle, border-radius:50%
│  initials]  │     size = f(metric value)
│  ┌─[PSD]──┐ │  ← party badge: overlaid bottom-center
│  └────────┘ │     colored bg + party logo (14px) + short name
└─────────────┘
  Popescu A.    ← name, always visible, 9px, truncated
  421k RON      ← formatted value, always visible, 8px muted
```

**Circle sizing:** radius proportional to `√(value)`, clamped to `[12px, 68px]` diameter. Square-root scale ensures area is proportional to value (perceptually correct).

**Photo:** `<img src="{image}" onerror="…">` — on error falls back to 2-letter initials centered in circle, background tinted with party color.

**Party badge:** absolute-positioned at circle bottom-center. Background = party hex color. Contains 14×14px party logo img + short name text. Hidden if circle diameter < 14px.

**Name label:** always shown below circle. Max-width = circle diameter + 8px. Overflow ellipsis.

**Value label:** formatted with `Intl.NumberFormat` + unit suffix (RON / mp / buc). Always shown.

**Hover tooltip:** full deputy name + exact value + party name.

**Click:** links to `data/v1/declaratii-avere/legislatura-2024/{cdep_idm}.json` (raw data, same pattern as existing avere.html leaderboard links).

### Null handling

Deputies with `null` for the selected metric are shown at minimum size (12px circle) at the end, greyed out, with "—" as value label. Still filterable by party.

### i18n

Uses existing `i18n.js` pattern. RO/EN strings for: toolbar labels, metric names, tooltip text, null label.

---

## Files changed / created

| File | Action |
|---|---|
| `scripts/build_avere_deputies.py` | New script |
| `data/v1/stats/avere-deputies-2024.json` | New generated artifact |
| `deputati-avere.html` | New page |
| `pages/` (if applicable) | Link from avere.html or index |
| `.gitignore` | Add `.superpowers/` if not present |

---

## Deferred

- **Liste view** (bar chart per deputy): toolbar button present but disabled, implemented in a follow-up.
- Legislatura selector (hardcoded to 2024 for now).

---

## Verification

1. Run `PYTHONPATH=. python scripts/build_avere_deputies.py --leg 2024` — confirm `data/v1/stats/avere-deputies-2024.json` contains ~332 records with expected fields.
2. Open `deputati-avere.html` via `python -m http.server 8000` — confirm circles render and are sized correctly.
3. Switch metric — circles re-sort and resize without page reload.
4. Toggle a party chip — filtered deputies disappear.
5. Type in search — list filters to matching names.
6. Resize browser window — grid wraps cleanly at all widths.
7. Deputies with missing photos show initials fallback.
8. Deputies with null metric value appear greyed at end.
