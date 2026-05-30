# Activity Log

Chronological record of meaningful work. Newest entries on top within each section.

## Data Quality

### 2026-05-29 — Add derived aggregate fields to avere parser + schema

Added 7 derived fields computed at parse time: `total_active_monetare_ron` (conturi + plasamente + bijuterii), `avere_neta_ron` (total_active − datorii), `nr_judete` (distinct counties with property), `nr_companii` (number of company stakes/loans), `terenuri_forestiere_count`, `terenuri_agricole_count`, `an_prima_proprietate`. Added corresponding 5 `ultima_*` snapshot fields to `AvereDeputat` and `AvereSummary`. All monetary values already in RON (converted via fixed May-2026 rates at parse time). 34 unit tests passing.

### 2026-05-29 — Full PDF extraction pipeline: all ANI form sections + per-row detail lists

**What was done**
- Extracted parser logic to `parsers/avere_pdf.py` (shared module; eliminates ~200 lines duplicated in `analiza_avere_pdf.py`).
- Added 4 new detail-list parsers: `_parse_imobile_details`, `_parse_vehicule`, `_parse_conturi_detaliate`, `_parse_plasamente`.
- Added 3 new scalar sections: II.2 bijuterii, III bunuri înstrăinate, VI cadouri.
- Fixed latent bug: IV section was scanned as a whole, inflating `conturi_total_ron` with IV.2 plasamente values. Now IV.1 and IV.2 are extracted separately.
- `schemas/avere.py`: 3 new models (VehiculDetail, ContDetail, PlasamentDetail); `AvereDeclaratie` +11 fields; `AvereDeputat` +2 snapshot fields; `AvereSummary` +3 fields.
- Populated `imobile_detaliate` (was schema-defined but always empty); added 6 category aggregates (`suprafata_agricol_mp`, `suprafata_forestier_mp`, `suprafata_intravilan_mp`, `suprafata_luciu_mp`, `suprafata_alte_mp`, `suprafata_cladiri_mp`).
- 26 unit tests covering all new functions with synthetic text (77/77 total suite passing).

**Verified on Iordache Ion (leg-2024 idm=153):** 83 imobile rows, 10 vehicule, conturi 3.09M RON, bijuterii 352k RON, suprafata_forestier 6.38M m².

**Action needed:** Re-run `build_declaratii_avere.py --all` to regenerate JSON from cached PDFs.

### 2026-05-29 — Fix conturi_total_ron=0 and auto_count undercount in PDF parser

**Audit:** Manual comparison of Iordache Ion (leg-2024, idm=153) PDF vs extracted JSON revealed two parser bugs.

**Bug 1 — `conturi_total_ron` always 0 for this PDF layout.**
`RE_AMOUNT` requires `<number> <currency>` order. The ANI PDF table lays out columns as `CURRENCY | YEAR | BALANCE` (e.g. `"RON 2015 377500"`), so no match ever fires. Actual accounts for Iordache Ion: ~3.09M RON across CEC Bank current/deposit accounts, EUR deposits, and insurance funds — all missed.
Fix: added `RE_AMOUNT_REV` regex (`CURRENCY YYYY amount`) and scan the conturi and datorii sections with both forward and reversed regexes.

**Bug 2 — `auto_count` misses "Alt mijloc de transport" entries.**
Vehicles labeled "Alt mijloc de transport" don't match any keyword in the auto regex. In pdfplumber-extracted text they appear as `^Alt mijloc de ...` at line start. Iordache Ion: 3 such entries (a 500Ai farm vehicle, a VOS tractor attachment, a Honda quad) were missed → count 7 instead of 10.
Fix: added `alt mijloc` to the regex alternation group.

**Verified on cached PDF (00dd571ad7d8.pdf):** `conturi_total_ron` 0 → 3,091,542 RON; `auto_count` 7 → 10.

**Known limitations documented in `docs/backlog.md`:** `venituri_anuale_ron` double-counts co-owned rental income; `suprafata_total_mp` ignores `cota-parte` fraction.

**Action needed:** Re-run `build_declaratii_avere.py --leg 2024 --leg 2020` to regenerate JSON from cached PDFs.

### 2026-05-29 — Fix auto_count inflation in PDF parser

**Bug:** `auto_count` was overcounting vehicles for every deputy by exactly 4. The section header "1. Autovehicule/autoturisme, tractoare, maşini agricole, şalupe, iahturi şi alte mijloace de transport..." contains the keywords `autovehicul`, `autoturism`, `şalup`, `iaht` — 4 extra word-boundary matches that inflated every count.

**Fix:** Changed regex from `\b...\w*` to `^...\w*` with `re.MULTILINE` in both `scripts/build_declaratii_avere.py` and `scripts/analiza_avere_pdf.py`. In pdfplumber's extracted text each table row starts at a new line; the section header has a `1. ` prefix and is never at `^`.

**Verified:** Deputy 15 (Badea Nelu-Valentin): old=14 → new=10, matching the PDF exactly.

**Action needed:** Re-run `build_declaratii_avere.py --leg 2024` and `--leg 2020` to regenerate corrected JSON from cached PDFs (no network required).

### 2026-05-29 — Fix suprafata_mp truncation in PDF parser

**Bug:** `RE_MP = re.compile(r"(\d{1,5}...)\s*m\s*²?")` only captures up to 5 digits. For a 6-digit area like `284354 m²` the regex engine matches starting at the second digit, extracting `84354`; for 7-digit areas like `1500000 m²` it matches `00000 = 0` which is filtered by the `> 5` guard, so the area is lost entirely.

**Impact:** `suprafata_total_mp` significantly undercounts. Iordache Ion: stored 1,897,569 m², correct value ~12,197,569 m² (~6× undercount).

**Fix:** Changed `\d{1,5}` to `\d+` in `RE_MP` in both `build_declaratii_avere.py` and `analiza_avere_pdf.py`. `terenuri_count` (number of matches) is unaffected — old regex still matched once per row, just at the wrong digit position.

**Action needed:** Re-run `build_declaratii_avere.py --leg 2024` and `--leg 2020` to regenerate corrected JSON.

---

## Dashboards

### 2026-05-30 — Avere ranking section on deputy profile pages

**What was done**
- Extended `scripts/build_avere_stats.py` with four new helpers: `_load_deputati_lookup()`, `_age_cohort()`, `_pct_from_bottom()`, `_rank_from_top()`, and the main `_build_context()` function.
- New output `data/v1/stats/avere-context-2024.json`: per-deputy percentile ranks across 5 metrics (active, venituri, imobile, suprafata, datorii) × 4 comparison groups (national, party, age cohort, județ).
- `deputat.html` now fetches `avere-context-{leg}.json` and renders a ranking section between the stat cards and detail lists: 5 percentile bars (with national median marker) + group comparison chips.
- 21 unit tests added in `tests/test_avere_context.py`.

**Decisions**
- Zero-datorii deputies excluded from datorii ranking (0 = no debt, not last place).
- Group chips hidden when N < 3 (too small to be statistically meaningful).
- `avere-context-{leg}.json` is a separate file from `avere-{leg}.json` to keep both files small and focused.
- Age cohorts are 5-year brackets computed at December 31 of the legislature's opening year.
- Join keyed on `cdep_idm` (not `id`) — the two datasets use incompatible hash-based ID schemes.

### 2026-05-29 — Avere sections on deputy profile page

Added 5 wealth declaration sections to the bottom of `deputat.html`, loading `data/v1/declaratii-avere/legislatura-{leg}/{idm}.json` in the existing `Promise.all`. New `renderAvere()` function generates: (1) stat cards grid with total active, avere netă, nr imobile, suprafață, venituri, conturi, bijuterii, vehicule; (2) imobile grouped by category from `imobile_detaliate[]`, sorted by area descending, with parcel count; (3) vehicule list (natura + marca + an fabricație); (4) plasamente list with type tag (hidden when empty); (5) bunuri înstrăinate summary (hidden when empty). Added `fmtRON()` and `fmtMP()` helpers (M/K/plain thresholds). Missing avere file → all sections silently absent.

### 2026-05-29 — Deputies Avere Circle Dashboard — implementation

Built `deputati-avere.html` — per-deputy wealth visualization as a circle grid.

**What was done**
- New build script `scripts/build_avere_deputies.py`: joins avere index + per-deputy detail files + deputati index. Emits `data/v1/stats/avere-deputies-2024.json` with 332 deputies and a `parties` lookup dict.
- New page `deputati-avere.html`: sticky toolbar (Cercuri/Listă toggle, metric dropdown, party chips, search, count badge), circle grid sorted descending by selected metric, circles sized by √(value/max) clamped [12, 68]px, party badge overlaid at circle bottom, photo with initials fallback, hover tooltip, click opens raw detail JSON.
- i18n keys added to `i18n.js` (ro + en) for all toolbar labels and metric names.
- Link added to `avere.html` header: "⬤ Vizualizare cercuri ↗".
- 6 unit tests covering join logic, null handling, and parties dict.

**Decisions**
- `build_leg(leg, root=ROOT)` accepts an explicit `root` parameter so tests can point at `tmp_path` without module patching.
- All 2024 deputies have declarations, so null-val deputies (greyed at 12px) only appear if a future leg has deputies without filings — the path is implemented and tested via fixtures.
- `parties` dict in JSON is the full historical CSV (319 entries); the page builds chips only from parties actually present in the deputies array.
- Liste view button present but disabled (deferred per spec).

---

### 2026-05-28 — Deputies avere visual dashboard — design spec

Brainstormed and specced a new per-deputy wealth visualization page (`deputati-avere.html`).

**What was done**
- Explored existing `avere.html` aggregate dashboard, avere data structures, deputati image URLs, and party assets.
- Designed and validated layout via interactive browser mockups (visual companion).
- Wrote design spec: `docs/superpowers/specs/2026-05-28-avere-deputies-dashboard-design.md`.

**Decisions**
- New standalone page, not an extension of `avere.html`.
- Layout: flex-wrap organic grid — deputies as circles sorted descending by selected metric, largest top-left, flowing to fill width.
- Circle size: radius ∝ √(value), clamped 12–68px diameter (area proportional to value).
- Deputy photo from cdep.ro URL (deputati data, joined on `cdep_idm`); fallback = initials.
- Party badge overlaid at circle bottom-center: party logo (`data/assets/imagini/partide/`) + short name.
- Six metric options: venituri anuale, conturi bancare, nr. imobile, suprafață terenuri, nr. auto, datorii.
- New build script `scripts/build_avere_deputies.py` joins avere index + individual detail files + deputati; outputs `data/v1/stats/avere-deputies-{leg}.json` with `parties` mapping and `deputies` array.
- Bar chart ("liste") view deferred to follow-up.

### 2026-05-28 — Wealth dashboard (`/avere.html` + `/stats/avere` aggregate)

First analytical dashboard in a sequenced set (full menu brainstormed; wealth chosen
first; audience = journalists + researchers; delivery = precompute + chart page).

**What was done**
- `scripts/build_avere_stats.py` — new build step. Reads the already-parsed
  `data/v1/declaratii-avere/legislatura-{leg}.json` summary index, reuses the top-list /
  per-party logic from `raport_avere.py`, and emits `data/v1/stats/avere-{leg}.json`:
  journalist leaderboards (top conturi/venituri/datorii/imobile + biggest cash
  increases/decreases + newly-acquired properties), per-party aggregates (median/mean +
  raw `conturi_values[]` for box-plots), overall quartiles, and stat cards.
- `avere.html` — standalone dashboard page (mirrors `deputat.html` shell + `i18n.js`,
  `?leg=` param). Chart.js v4 via CDN. Sections: stat cards → tabbed leaderboards →
  per-party median bar charts → CSS box-plots of liquid assets → methodology/caveats +
  raw-JSON download link.
- Wiring: `refresh_all.py` runs `build_avere_stats.py` after `build_comisii`; nav link +
  `nav_avere` i18n key (RO/EN); `CLAUDE.md` build command.

**Non-obvious decisions**
- **No fabricated "net worth".** We have measured monetary fields (conturi, venituri,
  datorii) but only *counts* for property/vehicles — no asset values. A single composite
  would mislead, so we rank on real fields and show portfolios as counts. Stated in the
  page's methodology block and in the build script's `CAVEATS`.
- **`datorii` read from detail files.** `AvereSummary` doesn't carry `ultima_datorii_ron`,
  so `build_avere_stats.py` reads it (plus suprafață/auto) from the per-deputy detail
  JSONs rather than re-running the expensive PDF parse or changing the schema.
- **`validate_data.py` left untouched** — it's deputati-specific (only globs
  `legislatura-*.json` deputy files), not a generic path registry, so the stats output
  neither needs registration nor breaks it.
