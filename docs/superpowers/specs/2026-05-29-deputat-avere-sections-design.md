# Deputat Avere Sections — Design Spec

**Date:** 2026-05-29  
**Status:** Approved

---

## Goal

Add wealth declaration (avere) data to the existing `deputat.html` deputy profile page as new sections at the bottom. Keep it simple — match the existing page style exactly.

---

## Approach

Option A: inline sections appended to `deputat.html` below the existing cross-links section. No new pages, no tabs, no collapsibles.

---

## Data Source

Fetch `data/v1/declaratii-avere/legislatura-${leg}/${idNum}.json` in parallel with the existing `Promise.all([...])` in `loadDeputat()`. Use `.catch(() => null)` so a missing file doesn't break the page. If the fetch returns null or has no declaratii, skip all avere sections silently.

Use the **last declaration** (`data.declaratii[data.declaratii.length - 1]`) for all display values.

---

## Sections (in order, added at the bottom)

### 1. Declarație de avere — stat cards

Heading: `Declarație de avere` + date (`data_depunere`) + PDF link (↗) in muted text beside heading.

8-card grid using the existing `.activitate` / `.act-card` pattern:

| Card | Field | Format |
|---|---|---|
| Total active | `total_active_monetare_ron` | `fmtRON()` |
| Avere netă | `avere_neta_ron` | `fmtRON()` — red if negative |
| Nr. imobile | `terenuri_count + cladiri_count` | integer |
| Suprafață | `suprafata_total_mp` | `fmtMP()` |
| Venituri anuale | `venituri_anuale_ron` | `fmtRON()` |
| Conturi bancare | `conturi_total_ron` | `fmtRON()` |
| Bijuterii / artă | `bijuterii_total_ron` | `fmtRON()` — omit card if 0 |
| Vehicule | `auto_count` | integer |

Below the cards, one line of muted metadata:
`Prima proprietate: {an_prima_proprietate} · {nr_judete} județe · {nr_companii} companii`  
Omit each token if null/0.

**Number formatting helpers** (defined once in the script):
- `fmtRON(v)` → `"3.4M RON"` / `"352K RON"` / `"63,000 RON"` (M ≥ 1,000,000 / K ≥ 10,000 / else locale)
- `fmtMP(v)` → `"10.8M m²"` / `"6,380 m²"` same thresholds

### 2. Imobile ({n})

Heading: `Imobile (${terenuri_count + cladiri_count})`

Grouped summary rows — one row per category that has at least one property:

| Category key | Label |
|---|---|
| `forestier` | Terenuri forestiere |
| `agricol` | Terenuri agricole |
| `extravilan` | Terenuri extravilane |
| `intravilan` | Terenuri intravilane |
| `luciu_apa` | Luciu de apă |
| `alte_cladiri` / `locuinta` / `apartament` / `comercial` / `vacanta` / `necunoscuta` | Clădiri ({subcategorie}) |

Each row: `{Label} · {count} parcele · {fmtMP(suprafata)}` — right-aligned suprafata.

Build this by iterating `imobile_detaliate[]` (available in the JSON), grouping entries by `categorie`, and summing `suprafata_mp`. This gives accurate per-category counts and totals for all categories without relying on schema-level count fields (only forestier and agricol have dedicated count fields; others do not).

Note line (muted): `Județe: {nr_judete}` if nr_judete > 0.

**Hide section entirely** if terenuri_count + cladiri_count === 0.

### 3. Vehicule ({n})

Heading: `Vehicule (${auto_count})`

One `.list-item` per entry in `vehicule[]`:  
`{natura}` (left) · `{marca || ''}` (muted) · `{an_fabricatie || ''}` (right-aligned muted)

**Hide section** if `vehicule.length === 0`.

### 4. Plasamente & investiții ({n})

Heading: `Plasamente & investiții (${plasamente_detaliate.length})`

One `.list-item` per entry in `plasamente_detaliate[]`:  
`{emitent || '—'}` (left) · `{tip || ''}` (muted tag) · `{fmtRON(valoare_ron)}` (right)

**Hide section** if `plasamente_detaliate.length === 0`.

### 5. Bunuri înstrăinate ({n})

Heading: `Bunuri înstrăinate în ultimele 12 luni (${bunuri_instrainate_count})`

One `.list-item` per entry — parsed from the `bunuri_instrainate_count` and `bunuri_instrainate_total_ron` scalars. Since we don't store per-row detail for this section, show a single summary line:
`{bunuri_instrainate_count} bunuri · total {fmtRON(bunuri_instrainate_total_ron)}`

**Hide section** if `bunuri_instrainate_count === 0`.

---

## Files changed

| File | Change |
|---|---|
| `deputat.html` | Add avere fetch to `Promise.all`, add `renderAvere(avere)` helper, insert 5 sections into the rendered HTML |

No new files. No new build scripts. No schema changes.

---

## Error handling

- Avere fetch fails / 404 → skip all sections silently (`.catch(() => null)`)
- `declaratii` array empty → skip all sections
- Individual field null/0 → hide that card or section per the rules above

---

## Not in scope

- Conturi detaliate table (institution-level accounts) — too much detail for a profile page
- Multiple declarations / timeline — use latest only
- Comparisons/rankings — backlog item
- i18n keys — add Romanian labels directly (page is currently mixed RO/EN anyway)
