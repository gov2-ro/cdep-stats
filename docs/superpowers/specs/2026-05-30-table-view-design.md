# Design Spec: Sortable Table View for deputati-avere and deputati-activitate

**Date:** 2026-05-30
**Status:** Approved

---

## Context

Both `deputati-avere.html` and `deputati-activitate.html` show deputy data as a circle/bubble grid sorted by a single selected metric. A table view lets users compare all metrics at once and sort by any column. The avere page already has a disabled "Cercuri | Listă" toggle — this spec enables it and implements the same pattern for the activitate page.

Audience: journalists and researchers scanning for outliers across multiple dimensions simultaneously.

---

## Visual Design

**Cell style:** Inline bar — value text above a 3px bar whose width is proportional to the column maximum. Null values show `—` with no bar.

**Columns:**

| Page | Columns (left → right) |
|---|---|
| `deputati-avere.html` | Name/Party · Active lichide totale · Venituri anuale · Conturi bancare · Nr. imobile · Suprafață · Datorii |
| `deputati-activitate.html` | Name/Party · Ședințe · Luări cuvânt · Propuneri legislative · Legi promulgate · Declarații politice · Întrebări/Interpelări |

**Name column:** sticky-left (doesn't scroll horizontally), 28px circular photo with initials fallback, deputy name, party badge underneath. Clicking a row navigates to `deputat.html?id={cdep_idm}&leg={leg}`.

**Sort:** Click any header to sort descending; click again for ascending; click again to reset to default (first metric column, descending). Active sort column header is highlighted blue; others are neutral grey. Null values always sort last regardless of direction.

**Bar scaling:** Each column's bar widths are independent — the column maximum is always the full bar width. Bars are re-scaled on sort/filter.

**Value formatting:**
- RON monetary values: `fmtRON()` (existing helper — M/K thresholds)
- Area: `fmtMP()` (existing helper)
- Counts (imobile, auto, activity integers): plain number

**Color:**
- Active sort column value text: `var(--blue)` — takes priority over all other rules
- All other columns: `var(--text2)` (neutral)
- Datorii column value text when non-zero and NOT the active sort column: `var(--red-text)` (debt stands out)
- Null `—`: `var(--text3)`, italic

---

## Toolbar Changes

**View toggle (both pages):**
- Label: `⬤ Cercuri` and `≡ Tabel`
- In circle view: metric dropdown visible; in table view: metric dropdown hidden (display:none)
- Party chips, search input, and count badge remain unchanged in both views
- Default view: circles (no URL state change needed)

**avere page:** Replace the currently-disabled `<button>` list toggle with the new ≡ Tabel button. Re-enable it.

**activitate page:** Add the same `⬤ Cercuri | ≡ Tabel` toggle to its toolbar, styled identically.

**Sort state:** When switching from circles → table, the table pre-sorts by whichever metric was selected in the circle dropdown. When switching back to circles, the metric dropdown shows the last sort column — unless the user had sorted by name, in which case the dropdown keeps its previous metric selection unchanged.

---

## CSS

New classes (added inline to each page's `<style>` block — no shared stylesheet):

```css
.dep-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dep-table{width:100%;border-collapse:collapse;font-size:12px;min-width:680px}
.dep-table thead th{padding:9px 10px;background:var(--bg2);border-bottom:2px solid var(--border);font-weight:500;color:var(--text3);cursor:pointer;white-space:nowrap;user-select:none;text-align:left}
.dep-table thead th.sort-active{color:var(--blue);border-bottom-color:var(--blue)}
.dep-table thead th.sort-name{cursor:default;min-width:160px;position:sticky;left:0;z-index:1;background:var(--bg2)}
.dep-table tbody tr{border-bottom:1px solid var(--border);cursor:pointer}
.dep-table tbody tr:hover{background:var(--bg2)}
.dep-table tbody td{padding:6px 10px;vertical-align:middle}
.dep-table tbody td.td-name{position:sticky;left:0;background:var(--bg);white-space:nowrap;z-index:1}
.dep-table tbody tr:hover td.td-name{background:var(--bg2)}
.bar-cell-val{font-size:11px;margin-bottom:3px;font-variant-numeric:tabular-nums}
.bar-cell-track{height:3px;background:var(--bg3);border-radius:2px;width:80px}
.bar-cell-fill{height:100%;border-radius:2px;opacity:0.75}
.dep-table .null-val{color:var(--text3);font-style:italic;font-size:11px}
```

---

## JavaScript

**`renderTable(deputies, columns, sortKey, sortDir)`** — pure function, returns HTML string. Used as the table view renderer (analogous to the existing circle render loop).

Parameters:
- `deputies`: filtered array (same array used by the circle view after party/search filtering)
- `columns`: array of `{key, label, fmt, color}` objects — defined per-page, not shared
- `sortKey`: field name of active sort column (`null` = default first metric column)
- `sortDir`: `'desc'` | `'asc'`

**Bar width computation:** For each column, find `max = Math.max(...deputies.map(d => d[col.key] ?? 0))`. Each cell's bar width = `(value / max * 100).toFixed(1) + '%'`. Recomputed on every render.

**Sort toggle logic** (on header click):
- If clicking a different column: set sortKey = that column, sortDir = 'desc'
- If same column, sortDir = 'desc': flip to 'asc'
- If same column, sortDir = 'asc': reset to default (first metric, 'desc')

**Integration into existing page flow:**
- Add `let viewMode = 'circles'` state variable
- On toggle click: set viewMode, re-render content area
- The existing `renderContent()` (or equivalent) function checks viewMode and calls either the circle renderer or `renderTable()`
- Sort state (`sortKey`, `sortDir`) persists when toggling between views

---

## Scope

**In scope:**
- Table view for `deputati-avere.html` and `deputati-activitate.html`
- All existing filters (party chips, search, leg toggle) work identically in table view
- Inline bar visualization with value text
- Column-click sorting with direction toggle

**Out of scope:**
- Column visibility toggling (show/hide columns)
- Frozen/pinned column configuration
- Export to CSV
- Responsive column collapsing on mobile (horizontal scroll is sufficient)

---

## Verification

1. `python -m http.server 8000` → open `deputati-avere.html`
2. Click "≡ Tabel": metric dropdown disappears, table renders with 332 rows
3. Click any metric column header: rows re-sort descending, header highlighted blue
4. Click same header again: re-sorts ascending
5. Click same header third time: resets to default sort
6. Type in search box: rows filter, bar widths re-scale to new filtered max
7. Click a party chip to deselect: rows filter, count badge updates
8. Click a row: navigates to `deputat.html?id=...`
9. Click "⬤ Cercuri": returns to circle view, metric dropdown reappears
10. Repeat steps 2–9 for `deputati-activitate.html`
11. Check mobile (375px): horizontal scroll works, name column sticks
