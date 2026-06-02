# Backlog

Known issues and future improvements. Use `- [ ]` checkboxes; add enough context to act on later.

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

- [ ] **`venituri_anuale_ron` double-counts income from co-owned properties**
  - ANI declarations require both spouses to list the same jointly-owned properties under sections 3.1 and 3.2 (cedarea folosinței). The parser sums all `amount RON/EUR` hits in section VII without deduplication, so rental income from shared plots appears twice. Venituri also include income for spouse, children, and other family members, plus one-off entries (real estate sales, dividends from family SRL) that inflate the annual figure. The field name `venituri_anuale_ron` is misleading — it is the total household sum, not the personal income of the titular.
  - Fix would require parsing by sub-section (1.1/1.2/1.3, 3.1/3.2, etc.) and choosing a clear semantic for the field (titular-only vs. household).
  - Audit case: Iordache Ion (leg-2024 idm=153) — stored 2,022,830 RON; titular-only ≈ 1,500,000 RON.

- [ ] **`suprafata_total_mp` ignores `cota-parte` (ownership share)**
  - The parser sums the full declared area for every imobil without applying the `Cota-parte` column. For properties co-owned by spouses at 1/2 share, the stored value is 2× the actual personal share. The cota-parte fraction also varies (1/3, 1/4, etc.).
  - Fix would require parsing the `Cota-parte` column per row and multiplying each area by the fraction before summing.
  - Audit case: Iordache Ion (leg-2024 idm=153) — all 73 terenuri + 10 cladiri are at 1/2; stored 10,858,310 m², actual personal share ≈ 5,429,155 m².


## Profile pages

- [ ] **Avere comparison / rankings on deputy profile page**
  - Add a contextual rankings section to the deputat avere profile: how does this deputy rank vs. national average, vs. party average, vs. same age cohort, vs. same județ. Show percentile for key metrics: total_active_monetare_ron, suprafata_total_mp, nr_imobile, venituri_anuale_ron.
  - Requires: age from deputat profile (birth_date), județ from deputat profile, pre-computed party/age/județ aggregates in the stats build step.
  - [ ] use `data/assets/geo/romania-counties.geojson` for choropleth județe comparison
- [x] enhance avere.html with thumbnails for ppl and partide
- [ ] 3rd lists view mode: bar chart (per category) matrix (one for each deputat) – LATER or SKIP alltogether
- [x] party profile pages — `partid.html?id=PSD&leg=2024` built 2026-05-31


## Ordine de Zi — Entity Extraction

- [ ] **Review NotebookLM entity proposals for gaps in regex extraction**
  - `docs/notebooklm-entities.csv` contains 101 entity/regex pairs across 14 categories generated by NotebookLM from the ordine-zi data. Several categories are not yet covered by `scrapers/entities_ordine_zi.py`:
    - **National Institutions** — BNR, CSM, ANCOM, CES, Consiliul Fiscal, Consiliul Concurenței, Consiliul Legislativ
    - **International Bodies** — European Commission, ECB, Committee of the Regions
    - **Specialized Bodies** — Academia de Științe Agricole, RA-APPS, Inspecția Muncii
  - Caveats: the CSV regexes need cleanup before use — inconsistent diacritics (cedilla `ş`/`ţ` vs. comma-below `ș`/`ț`), missing `\b` word boundaries, some duplicates, and row 15 (`Comisiei` under European Commission) would false-match every Romanian commission genitive.
  - See also: `docs/ordine-zi-entity-analysis.md` for full n-gram analysis and existing taxonomy comparison.

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
- [ ] show cars, homes, terenuri as icons, one per each? - relative to suprafata or kph?
- [ ] ce fel de vehicole, șalupe, tractoare, motociclete?
- [ ] car brands stats/charts, overall, per party, per judet, per age group?
- [ ] ce înseamnă coloana partid în /interese?
- [x] **Remove dead CSS rules in deputati-avere.html and deputati-activitate.html** — done 2026-05-31; removed `.metric-select`, `.search-input`, `.party-chips`, `.party-chip` rules.
- [ ] cele mai preferate mărci de mașini / pe partid, pe județ, pe vârstă

- [ ] when/if json gets too large, go duckdb smth?


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

