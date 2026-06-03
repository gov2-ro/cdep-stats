# Backlog

Known issues and future improvements. Use `- [ ]` checkboxes; add enough context to act on later.

---

## Pipeline & Deploy (Active)

- [ ] **Split ordine-zi monolith into modular CSV/JSON files** (37.5% size reduction candidate)
  - **Problem**: `data/v1/ordine-zi/legislatura-2024.json` is 33.54 MB, blocks initial page load
  - **Proposal**: Split into `sesiuni.csv` (0.02 MB) + `items.csv` (3.93 MB) + `docs.csv` (11.86 MB) + `entities.json` (5.15 MB) = 20.95 MB (37.5% reduction, zero data loss).
  - **Web UX**: Load sesiuni + entities on initial page (~5 MB), lazy-load items/docs on session click
  - **Implementation notes**:
    - `scripts/split_ordine_zi.py` and `scripts/merge_ordine_zi.py` already exist and tested (`docs/ordine-zi-split.md`)
    - Add `split_ordine_zi.py` to daily cadence in `refresh_all.py` (after `run_ordine_zi.py`)
    - Update `ordine-zi.html` to lazy-load CSV/JSON instead of monolith
    - Keep merge script as recovery utility
    - Phase in: generate split files alongside monolith during transition period

- [ ] **Deploy safety & documentation improvements**
  - **Problem**: `deploy.sh` had unsafe `--delete` with partial exclusions on `data/v1/`, which could delete managed files
  - **Status**: FIXED in commit b617dca7d (removed --delete from Pass 2 data/v1 sync, only use on stats/)
  - **TODO**: 
    - Document deploy.sh behavior in CLAUDE.md with examples
    - Add deploy.sh dry-run to CI or pre-deploy checklist (at least once per release)
    - Test both full + --quick modes against staging server
    - Consider adding file count/size validation post-deploy (sanity check that key files exist)

- [ ] **Large data dir optimization** — move `interpelari/` and `ordine-zi/` to yearly splits
  - **Problem**: `interpelari/legislatura-2024.json` is 83 MB; current split_by_year only handles interpelari/proiecte at year level
  - **Similar to**: `split_by_year.py` optimization that reduced `proiecte/` load from 21 MB to ~3 MB/year
  - **Implementation notes**:
    - Extend `split_by_year.py` to also split `interpelari/legislatura-2024.json` and `ordine-zi/legislatura-2024.json` by year
    - This pairs well with the ordine-zi split proposal above (split monolith, then year-split the split)
    - Would reduce `ordine-zi` mobile load from 34 MB to ~5 MB/year (2024: 4 MB, 2023: 2 MB, etc.)

---

## Cross-links

- [ ] **Back-fill `data_inregistrare_cd` on necunoscut.json bills** — voted bills lack a registration date and land in `necunoscut.json`, so `proiect.html` can't show their full detail view. Running `run_proiecte.py` with a flag to re-scrape bill metadata and populate `data_inregistrare_cd` would move them into year files, making `proiect.html` detail + `proiect.html → vot.html` cross-link work for all voted bills. `bill-vote-map-{leg}.json` already has the 394 matched pairs for 2024; the cross-link fires as soon as the bill appears in a year file.

---

## Deploy — Removed pages to revisit

- [ ] **Re-evaluate `vot.html` (voturi recente widget) for the landing page**
  - Individual vote pages (`data/v1/voturi/{leg}/{id}.json`) are 4 500+ files that bloat the archive. Removed `vot.html` and the "Voturi recente" widget from `index.html`. Revisit if a lightweight summary view (e.g. render from `_index.json` only, no drill-down) is worth adding back.

- [ ] **Re-evaluate `proiect.html` (cele mai disputate proiecte widget) for the landing page**
  - `proiect.html` had no inbound nav links. The "Cele mai disputate proiecte" widget on `index.html` (top 5 by amendments) was removed along with it. `data/v1/proiecte/` and `data/v1/amendamente/` are excluded from the deploy archive but kept on disk. Revisit if a project detail page is worth wiring into the nav properly.

- [ ] **Switch deploy to rsync — eliminate the scp+unzip bottleneck**
  - Current flow: `build_web.py` produces a 347 MB zip of 5,286 files; `scp deploy.zip && unzip -o` is slow and re-transfers everything on every deploy.
  - Fix: two-pass rsync. Pass 1 — stable/immutable data (`voturi/`, `declaratii-avere/`) with `--checksum` so only new files transfer after the first sync. Pass 2 — `web/*.html`, `assets/`, `data/v1/stats/`, and all small dirs (< 100 files) which are fast to zip or rsync whole.
  - PHP is **not** needed for this; nginx static serving is fine. PHP would only be warranted if dynamic queries (search, filter) are added later.
  - A `scripts/deploy.sh` wrapper would codify the two-pass logic.

- [ ] re-add, reconsider sanctiune.html, vot.html and other pages found in https://github.com/Endimion2k/cdep-api-poc (motiune.html, voturi.html,  sanctiune.html, status.html)

- [x] interpelari-stats.html is broken — fixed 2026-06-01

- [x] **[SYSTEMIC] Eliminate recurring "set properties of null" errors in page JS** — FIXED
  - **Root cause:** Pages tried to set properties on non-existent DOM elements:
    - `document.getElementById('json-link').href = ...` (element never existed)
    - `document.getElementById('leg-toggle').innerHTML = ...` (inconsistent across pages)
  - **Comprehensive fix (2026-06-01):**
    1. Removed ALL `json-link` references (was dead code trying to update non-existent element)
    2. Consolidated leg toggle to `NAV.renderLegToggle()` — single source of truth in nav.js
    3. Updated 8 pages to use NAV function: interpelari-stats, avere, deputati-activitate, voturi, proiecte-stats, partide, judete, deputati-avere
    4. Added null-checks on remaining `document.querySelector()` calls (e.g., back link in deputati-avere.html)
  - **Still TODO (lower priority):**
    - Consolidate JSON link into nav.js footer
    - Add ESLint rule to catch unsafe `getElementById(...)` patterns at build time
    - Review and add null-checks to other modules (avere-list.js, etc.) — these are less critical since they target elements that exist

- [x] **vot.html: cross-link to bill description from proiecte data** — done 2026-06-03
  - PL-x votes: 475/619 matched to `proiecte-index-2024.json` (title + link to `proiect.html`); 144 from prior legislatures get cdep.ro search fallback.
  - PH CD votes (125): extended `parseBillRef()` to detect hotărâre pattern and show cdep.ro fallback.

- [ ] **voturi.html / vot.html: add "What's new" badge or visual indicator to nav**
  - voturi.html and vot.html are newly unlocked pages (previously removed due to deploy size constraints). Consider marking them as "New" or highlighting them in the nav briefly to draw attention.



---

## PDF Parser — Known Limitations

- [x] **`venituri_anuale_ron` double-counts income from co-owned properties** — partially fixed 2026-06-03
  - Added `venituri_titular_ron` field (parsed from section VII X.1. subsections only) to `AvereDeclaratie`.
  - `venituri_anuale_ron` unchanged (household total, kept for backward compatibility).
  - `deputat.html` shows `venituri_titular_ron` when available, falls back to `venituri_anuale_ron`.
  - Field will populate on next PDF parse run (pdfplumber required); existing data has `venituri_titular_ron=0`.
  - [ ] Update aggregate rankings in `build_avere_stats.py` to use `venituri_titular_ron` once data is populated.

- [x] **`suprafata_total_mp` ignores `cota-parte` (ownership share)** — fixed 2026-06-03
  - Parser now multiplies each property area by its cota fraction before aggregating.
  - Post-processed 131 existing deputy files. Iordache Ion: 10,858,310 m² → ~5,429,155 m². Enache Mihai-Adrian: 2,686 m² → 1,992 m².


## Profile pages

- [x] **Avere comparison / rankings on deputy profile page** — done (shipped in prior session)
  - `renderAvereRanking(ctx)` in `deputat.html`: 5 metric bars (active, venituri, imobile, suprafata, datorii) + party/age/județ comparison chips. Data from `avere-context-{leg}.json`.
  - [ ] use `data/assets/geo/romania-counties.geojson` for choropleth județe comparison
- [x] enhance avere.html with thumbnails for ppl and partide
- [ ] 3rd lists view mode: bar chart (per category) matrix (one for each deputat) – LATER or SKIP alltogether
- [x] party profile pages — `partid.html?id=PSD&leg=2024` built 2026-05-31


## Ordine de Zi — Entity Extraction

- [x] **Review NotebookLM entity proposals for gaps in regex extraction**
  - `docs/notebooklm-entities.csv` contains 101 entity/regex pairs across 14 categories generated by NotebookLM from the ordine-zi data. Several categories are not yet covered by `scrapers/entities_ordine_zi.py`:
    - **National Institutions** — BNR, CSM, ANCOM, CES, Consiliul Fiscal, Consiliul Concurenței, Consiliul Legislativ
    - **International Bodies** — European Commission, ECB, Committee of the Regions
    - **Specialized Bodies** — Academia de Științe Agricole, RA-APPS, Inspecția Muncii
  - Caveats: the CSV regexes need cleanup before use — inconsistent diacritics (cedilla `ş`/`ţ` vs. comma-below `ș`/`ț`), missing `\b` word boundaries, some duplicates, and row 15 (`Comisiei` under European Commission) would false-match every Romanian commission genitive.
  - See also: `docs/ordine-zi-entity-analysis.md` for full n-gram analysis and existing taxonomy comparison.

## Ordine de Zi — List View Enhancements

- [ ] **Enhance ordine-zi-lista.html with UX & query features**
  - **URL persistence**: Save filter state to `?q=...&type=bills&flags=urgenta,prioritate&year=2024` so filters survive page reload and can be shared.
  - **Saved queries / favorites**: Let user bookmark/name a filter preset ("Urgent bills from juridica commission") and recall it from a dropdown.
  - **Column toggles**: Render as table option (columns for type, action, law_category, flags, commissions) with resizable/sticky header for long lists.
  - **Sorting**: Allow sort by session date, position, item type (currently sorted as displayed).
  - **CSV export**: "Export results as CSV" button for use in external tools (data analysis, monitoring).
  - **Bulk actions**: Mark/flag items for follow-up or export a subset of filtered results.
  - **Mobile layout**: Filter bar collapses into a modal/drawer to free space on small screens.
  - **Performance**: For very large filter results (1000+), consider pagination or virtual scrolling to keep DOM light.
  - **Refinement**: Suggest related filters (e.g. "X% of results are from juridica commission — filter by it?") to help users narrow down.
  - Context: The current implementation is a working MVP; these enhancements add power-user and discoverability features.

## Misc

- [x] replace cdep link from /pls/parlam/structura2015.mp?idm={ID}&cam=2&leg=2024 to /ords/pls/parlam/structura2015.mp?idm={ID}&leg=2024
- [x] link to [monitorul.ai](https://monitorul.ai) via [MCP](https://monitorul.ai/mcp).  
  - [x] find URI correspondences
  - [x] Add contextual relevant links.
  - [ ] see if any pages from monitorul.ai are missing
- [x] cercuri in some views don't render right
- [x] OG info
  - [x] fix og:image
- [x] move html files in folder, not root. — created `web/` deployment folder with build script (2026-06-01)
- [x] look into Declarații de interese
- [ ] daily scraper - deploy script that only adds novelty? – generally make deploy smarter
- [ ] show cars, homes, terenuri as icons, one per each? - relative to suprafata or kph?
- [ ] ce fel de vehicole, șalupe, tractoare, motociclete?
- [ ] car brands stats/charts, overall, per party, per judet, per age group?
- [ ] ce înseamnă coloana partid în /interese?
- [x] **Remove dead CSS rules in deputati-avere.html and deputati-activitate.html** — done 2026-05-31; removed `.metric-select`, `.search-input`, `.party-chips`, `.party-chip` rules.
- [ ] cele mai preferate mărci de mașini / pe partid, pe județ, pe vârstă

- [ ] when/if json gets too large, go duckdb smth?
- [ ] make a list of scraped targets, the fetched fields, and target files.

- [ ] make more static? we generate static but load data from json?! is this SEO friendly?
- [ ] create llms.txt
- [ ] add filter by minoritati in party list / filters
- [ ] create api partide, or enhance with banipartide data? GET partide, GET partid

- [ ] întrebări & interpelări https://www.cdep.ro/ords/pls/parlam/interpelari2015.home


## Site consistency / front door

- [x] Top nav. Rename site title: Cdep stats. Normalize nav in all pages. Add link to cdep-api on all pages at the end. Remove language swticher border, add flag emoji for language switcher.
- [x] add top bar with - not official gov.ro site notice (one time / dismissable, save state to browser/cookies): `Versiune alfa / preview. Acesta NU ESTE un proiect oficial al Guvernului României. Date preluate de pe cdep.ro`. See https://ins.gov2.ro/
- [x] top nav dark background?
- [x] **Refactor the 16 copy-pasted root pages to a shared header/nav/footer** — nav drift (pages
  falling behind on links/labels) keeps recurring because each page hand-copies its `<nav>`. Extract
  to a shared `assets/nav.js` (or generate these pages like `pages/`) so header/nav/footer live in
  one place. This pass re-synced 5 pages by hand; the root cause remains. (2026-05-31: the
  avere/deputati-avere list logic was extracted to a shared `assets/avere-list.js` — a working
  proof of the shared-module approach; nav/header/footer are still copy-pasted.)
- [ ] **Relink and restyle `search.html`** — currently orphaned (no nav links into it) and on the
  old design. Re-add it to the nav and bring it on-brand. Left out of the 2026-05-31 consistency
  pass on purpose. much LATER. maybe
- [ ] **`proiect.html` initiator → deputy profile links** — the initiator is a free-text blob with
  no IDs, so linking needs exact name→`cdep_idm` matching against deputati (fragile, risk of
  mislinks). Implement only if the match is provably clean; otherwise leave as text.
- [ ] **`partid.html` long roster is heavy** — the flat ~92-row deputy list makes the page an
  endless scroll. Consider a compact row style or a show-more cap (without hiding data by default).

