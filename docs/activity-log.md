# Activity Log

Chronological record of meaningful work. Newest entries on top within each section.

### 2026-06-01 — Cross-links, compact UI, deploy script

**What was done**
- `scripts/build_proiecte_index.py` (new) — reads all proiecte files including `necunoscut.json` and emits `data/v1/stats/proiecte-index-{leg}.json` (846 KB for 2024, 1.9 MB for 2020): just `{cdep_idp, nr_inregistrare, nr_camera_deputati, titlu, stadiu, tip, source_url}` per bill. Separators compressed (no extra whitespace).
- `web/vot.html` — bill cross-link: fetches the proiecte index in parallel with the vote data, parses bill number from `descriere` with regex, renders a blue callout card linking to `proiect.html?idp=...` if found locally, else a fallback link to cdep.ro search. Also fixed `index.html` vote links to use `cdep_idv` (numeric) not `v.id` (UUID).
- `web/deputat.html` — each committee name is now a link to `comisii.html?leg=...`.
- `web/partid.html` — compact deputy roster: photo 28×28 (was 40×40), padding 5px (was 10px), judet inline after name with "·" separator (was a second div row). Row height ~39px.
- `web/index.html` — 6 new dash-cards (Voturi, Comisii, Moțiuni, Agendă, Interese, Legi); card grid compacted to `minmax(180px,1fr)` with 8px gap and 12px padding (was 220px/12px/16px).
- `scripts/deploy.sh` (new) — two-pass rsync deploy replacing `build_web.py + scp+unzip`: pass 1 uses `--checksum` for stable/large dirs (voturi, declaratii-avere, proiecte); pass 2 uses `--delete` for HTML/assets/stats. Supports `DRY=1` dry-run.

**Decisions**
- Bill index is NOT included as a build step in a scraper chain — it reads existing `data/v1/proiecte/` files that are already on disk after `run_proiecte.py`. Run once after scraping, or add to refresh pipeline manually.
- `necunoscut.json` stays excluded from deploy archive (too large) but IS read by `build_proiecte_index.py` at build time to populate the thin index.
- `deploy.sh` is a standalone script, not wired into any CI yet — needs host credentials to run.

### 2026-06-01 — Nav overhaul + index.html polish

**What was done**
- `assets/nav.js` — all 12 pages now in top nav and footer sitemap. Nav restructured so all items (logo, links, cdep-api, dark/lang toggle) are a single inline flow using `display:contents` on `<nav>` and `flex-wrap:wrap` on `.header-inner`. Logo is single-line. `justify-content:flex-start` prevents last-row items from spreading. Injected CSS from `renderHeader()` so all pages pick up changes without touching individual HTML files.
- `assets/nav.js` — `vot.html` highlights "Voturi", `partid.html` highlights "Partide" (active-link fix).
- `web/index.html` party bars — changed bar fill from pastel `p.bg` to party color at 33% opacity (`color+'55'`). UDMR and Neaf bars were nearly invisible before.
- `web/index.html` voturi recente — vote titles are now links to `vot.html?id=...&leg=2024`.
- `web/index.html` — new "Agendă parlamentară" column (4th demo-card) alongside "Voturi recente": loads most-recent session from `data/v1/ordine-zi/legislatura-2024.json`, shows 7 agenda items truncated at 110 chars, links to `ordine-zi.html`.

**Decisions**
- CSS injected from `nav.js` rather than editing 17 HTML files; uses `!important` to override per-page defaults.
- `display:contents` on `<nav>` makes links direct flex children of `.header-inner` so they wrap in the same flow as logo and toolbar.
- Agenda widget loads on every index.html visit (not precomputed) since ordine-zi.json is small (19 sessions, ~150KB).

### 2026-06-01 — Five new pages: comisii, motiuni, interese, ordine-zi, proiect

**What was done**
- `web/comisii.html` — Parliamentary committees browser. Loads `data/v1/comisii/legislatura-{leg}.json`; lists all 37 committees (2024) grouped by type (permanente / speciale comune); accordion expand shows membership table with party pills and color-coded party distribution bar. Added "Comisii" to main nav in `assets/nav.js` (between Activitate and Interpelări). Legislature toggle 2024/2020/2016.
- `web/motiuni.html` — Censure motions timeline 1992–2024. Loads all 9 legislature files in parallel; 162 motions total. Stat cards (total/respinse/adoptate/în procedură), filter buttons, chronological leg-group layout with status dot colors.
- `web/interese.html` — Declarations of interest browser. Loads `data/v1/declaratii/legislatura-{leg}.json` (332 deputies for 2024); columns: deputy link, party pill, avere PDF, interese PDF. Live search + party dropdown filter. Legislature toggle 2024/2020.
- `web/ordine-zi.html` — Session agendas. Loads `data/v1/ordine-zi/legislatura-{leg}.json` (19 sessions); accordion list sorted descending by date; most-recent session auto-expanded; each item shows description and PDF link if available.
- `web/proiect.html` — Bill browser + detail page. Default mode: loads all year-specific proiecte files (`2024.json`, `2025.json`, `2026.json` for leg 2024) and shows 52 searchable/filterable bills. With `?idp=XX&leg=YYY`: shows individual bill detail (title, status, timeline, vote counts, document links). Added "Explorează proiecte cu dată ↗" link to `proiecte-stats.html` subtitle.
- `scripts/build_web.py` — Changed proiecte exclusion from `data/v1/proiecte/*` to just `necunoscut.json` and `_index.json`; year-specific files (200KB for leg 2024) are now included in the deploy archive.

**Decisions**
- `necunoscut.json` excluded from deploy: 6.1MB for leg 2024, 15MB for leg 2020 — too large. Bills in those files (≈97% of total) show a fallback message with a cdep.ro link in detail mode. The year-specific files cover bills with a known registration date.
- `avere rankings on deputat.html` was already implemented (skipped — `renderAvereRanking` + `avere-context-{leg}.json` wired in a previous session).
- All pages verified with Playwright: 7/7 pass, zero JS console errors.

### 2026-06-01 — Build voturi.html (vote list) and vot.html (vote detail) pages

**What was done**
- Created `voturi.html`: paginated list of all votes from `data/v1/voturi/{leg}/_index.json` with 50 votes per page, sorted by date descending.
  - Vote summary shows counts: pentru/contra/abțineri/nu_au_votat and links to detail page.
  - Legislature toggle (2024/2020) to switch between legislatures: 885 votes in 2024, 3,617 in 2020.
  - Full pagination with "Primă / Ultimă" and page number navigation.
- Created `vot.html`: individual vote detail page showing every deputy's choice for a specific vote + party discipline analysis.
  - Vote header shows: descriere (bill), timestamp, vote outcome (ADOPTAT/RESPINS based on >50% threshold).
  - Summary cards: total votes (pentru/contra/abțineri/nu_au_votat).
  - Party discipline table: per-party breakdown with "coeziune" % (% voting majority opinion within party).
  - Full deputy roster: deputy name, party, vote choice (avec color badge: verde pentru, roșu împotrivă, ambra abținere, gri absent).
  - Cross-links: voturi.html lists link to vot.html?leg={leg}&id={idv}, vot.html links back to voturi.html?leg={leg}.

**Why**
Both pages were removed from the original codebase because they bloated the deployment archive (4,500+ individual vote JSON files). The rsync deployment strategy (added to backlog) unblocks these pages — the data files stay on the server permanently, so serving them is now zero-cost. These pages provide high civic value: citizens can inspect individual votes, see how their deputies voted, and analyze party discipline/cohesion on specific bills.

**Decisions**
- Page limit: 50 votes per page for voturi.html — balances readability vs. one-page load time.
- Party discipline metric: chose "coeziune %" = (majority_votes / total_votes) per party on that bill, which is simple and meaningful.
- Vote outcome: >50% threshold (for/contre) determines ADOPTAT vs. RESPINS (not using prezenti as denominator to avoid skewing by absences).
- Sorted descending by timestamp so newest votes appear first in the list.

---

### 2026-06-01 — Fix interpelari-stats.html (broken party color mapping)

**What was done**
- Fixed `interpelari-stats.html` page which was broken and not loading data correctly.
- Removed two lines of dead code that referenced a non-existent `json-link` DOM element, causing JavaScript errors.
- Updated `PARTY_COLORS` mapping: fixed 'SOSRO' → 'SOS RO' to match actual data in `interpelari-2024.json` and `interpelari-2020.json`.
- Added 'Minoritati' party color (#666) to support the small minority party group in the stats breakdown.
- Aligned `rateBar()` color threshold from >=90 to >=80 for consistency with the visual color fill bar logic.

**Why**
The page was in the backlog as "broken" — party name mismatch between the hardcoded color map and the actual JSON data caused undefined colors in the display, and dead code trying to update a missing element would throw JS errors in dev tools. These were lightweight fixes that unblock the page for use.

**Decisions**
- Kept the color threshold at >=80 (green) / >=70 (amber) / <70 (red) to align with the visual bar styling.
- Did not add a separate page for interpellations list yet — that's a future task (Tier 2 brainstorm). This fix brings the stats page back online.

---

### 2026-06-01 — Multi-party affiliation timeline, compact nav, activity badges, footer links

**What was done**
- Added multi-party affiliation timeline to `deputati-activitate.html`: full party switching history per deputy with timeline bars, party badges, and tenure dates below the activity circle grid.
- Extended `build_activitate_deputies.py` with new `_load_parties_timeline()` function to compute per-deputy tenure periods across all legislatures; `activitate-deputies-{leg}.json` now includes `party_timeline[]` with `party` / `start_date` / `end_date`.
- Added multi-party badge support to `deputati-activitate.html`: when a deputy held multiple parties across all legs, a small colored badge grid (2–5 party logos) overlays the deputy circle, color-coded by tenure proportion.
- Compacted nav bar: reduced logo font from 20px to 18px, nav item spacing, and streamlined header height for cleaner appearance across all pages.
- Restored 5 activity indicators on `index.html` (avere/activitate/interpelări/proiecte/partide) that had been hidden; layout now matches design with proper stat cards.
- Injected GitHub icon + link (`gov2-ro/cdep-stats` repo) into all page footers (16 root pages), right-aligned; adds `footer-github` i18n key (RO/EN).

**Why**
Deputies frequently switch parties across legislatures (term limits, mergers, splits, defections). The timeline provides context for career patterns; badges avoid cluttering the grid with legend-sized party logos. The activity indicators restore visibility of all core dashboards on the homepage, improving discoverability. The footer link credits the open-source repository and invites contributions.

**Decisions**
- Party timeline computed from `deputati/legislatura-{leg}.json` across all cached legs, not just the selected leg, to show full historical affiliation.
- Multi-party badge only shown when ≥2 parties; single-party deputies show no badge (implicit context clear).
- Footer GitHub link uses a fixed `<svg>` icon (12×12, scalable) rather than an emoji to maintain visual consistency.

---

### 2026-06-01 — Fix missing i18n.js in web/ (profile_monitorul key rendered literally)

**What was done**
- `i18n.js` was deleted from the project root as part of the move to `web/` but was never added to
  `web/`. The deployed site had an older `i18n.js` without the `profile_monitorul` key, so
  `applyI18n()` replaced the element text with the bare key string instead of "Profil monitorul.ai".
- Restored `web/i18n.js` from git HEAD (which includes both the RO and EN translations for
  `profile_monitorul`).
- Updated `scripts/build_web.py` to include `web/*.js` files in `deploy.zip` alongside `web/*.html`.

**Why**
The `profile_monitorul` key was added to `i18n.js` at the same commit as the monitorul.ai link
feature (`6fc4a2dcb`). When `i18n.js` was removed from the root without being placed in `web/`, the
fallback in `t(key)` kicked in — returning the key name itself when not found in the translation dict.

### 2026-06-01 — Create deployment folder structure for shared hosting

**What was done**
- Created `web/` folder with all assets needed for deployment to shared hosting (923MB).
- Structure includes: 16 root HTML pages, favicon, i18n.js, assets/ (CSS/JS + images), pages/ 
  (generated detail pages), pagefind/ (search index), and data/v1/ (API JSON data).
- Added `scripts/build_web.py` to automate the assembly. Rebuilds web/ from source files in one pass.
- Updated `.gitignore` to exclude web/ (generated artifact).
- Updated CLAUDE.md with the new build step and deployment instructions.

**Why**
The repo previously used GitHub Pages (HTML files in root). After moving to shared hosting, the 
deployment structure was unclear. Creating a clean `web/` folder makes it easy to zip and deploy 
via scp to any shared host. Excluded unnecessary files: source code (scripts/), raw data beyond API 
(data/analize, 1.1GB analysis stats not served by the app), and development artifacts.

**How to apply**
1. After running all scrapers and build steps: `python scripts/build_web.py`
2. Deploy: `zip -r deploy.zip web/ && scp deploy.zip user@host:/path/to/public_html/`

### 2026-05-31 — Normalize site nav, title, and language switcher

**What was done**
- Renamed site title from "cdep-api stats" to **Cdep stats** across all 16 HTML pages (logo markup
  and og:title).
- Normalized the nav bar across all pages: consistent logo link, 6 nav items (Averi/Activitate/
  Interpelări/Proiecte/Partide/Județe), `cdep-api ↗` external link, language toggle slot.
- Added full nav to `search.html` (was a minimal header with just lang toggle).
- Added missing `lang-toggle-slot` and `<script src="i18n.js">` to `partid.html`.
- Standardized `.header-inner` max-width to 1100px (was 1200px on 4 pages).
- Removed commented-out search links, ARIA role attributes from index.html header.
- Language switcher: removed border (`border:none`), replaced "EN"/"RO" text with 🇬🇧/🇷🇴 flag
  emojis, bumped font-size to 14px for emoji readability.

**Why**
The nav had diverged across pages over time — inconsistent logo markup (span vs anchor), varying
widths, missing i18n on one page, and the cdep-api link only on the homepage. Standardizing makes
maintenance easier and gives users consistent navigation + a direct link to the data source.

### 2026-05-31 — CDEP → Monitorul.ai correspondence list

**What was done**
- Created a correspondence list mapping all cdep.ro deputies (786 unique, 1,050 entries across
  legislatures 2016/2020/2024) to their monitorul.ai profiles.
- The `monitorul_id` slug is derived algorithmically from the deputy name (lowercase → strip
  diacritics → spaces→hyphens). Verified 50 random samples via `mcp__monitorul__search_persons`:
  **86% exact match** (43/50). All 50 were found by search even when the slug differed.
- 9 known mismatches fixed manually (name-order reversals, short forms, dropped middle names).
- Three files written to `data/v1/correspondence/`:
  - `monitorul_cdep.json` — full correspondence with metadata, all ID systems, verification status.
  - `monitorul_cdep_lookup.json` — quick map `cdep_id → monitorul profile`.
  - `monitorul_idm_lookup.json` — quick map `"{idm}_{leg}" → monitorul profile` for cdep.ro URL lookups.
- Added `cdep_idm` (numerical cdep.ro ID), `cdep_url` (profile URL), `family_name`, and `given_name`
  to each entry alongside the monitorul fields.

**Why**
The monitorul.ai MCP provides rich parliamentary speech data keyed by `person_id`. This
correspondence bridges the two datasets, enabling cross-linking between cdep deputy pages and
monitorul.ai profiles. The `idm_lookup` file specifically supports resolving cdep.ro URLs like
`?idm=319&leg=2024` directly to monitorul profiles.

**How to apply**
- Use `monitorul_cdep_lookup.json` for `cdep_id → monitorul` lookups in the app.
- Use `monitorul_idm_lookup.json` when starting from a cdep.ro URL.
- To verify/fix entries: call `mcp__monitorul__search_persons(q="Deputy Name")` and take the first
  non-"înlocuit"/"online" result's `person_id`.

### 2026-05-31 — Merge avere.html + deputati-avere.html into one wealth page

**What was done**
- **`avere.html` is now the single wealth page.** Kept its aggregate stat cards, party bar-charts,
  conturi box-plots and methodology, but replaced the old 7-tab "Topuri" leaderboard with a
  deputati-avere-style **deputy list limited to 50**, controlled by a toolbar above it:
  `⬤ Cercuri / ≡ Tabel` view toggle · 6-metric selector (Venituri/Conturi/Imobile/Suprafață/Auto/
  Datorii) · `Top 50 / Ultimii 50 / Lista completă ↗`. Charts now sit **below** the list. Fetches
  both `stats/avere-{leg}.json` (cards/charts) and `stats/avere-deputies-{leg}.json` (the list).
- **`deputati-avere.html` is now the full-list-only page.** Delinked from the nav; reachable only
  via the merged page's `Lista completă ↗` (opens in a new tab carrying `leg`/`metric`/`view`).
- **`Averi++` removed site-wide.** Single `Averi` nav entry on all pages; `index.html` collapsed its
  two wealth dashboard cards into one.
- **Evolution columns.** The list's table view gained 3 columns — *Creștere conturi în mandat*,
  *Scădere conturi în mandat*, *Imobile noi în mandat*. Backed by two new per-deputy fields
  (`delta_conturi_ron`, `delta_imobile`) added to `scripts/build_avere_deputies.py` output (nulled
  unless the deputy has ≥2 declarations); data regenerated for 2024 + 2020.
- **Shared renderer.** Extracted the list/table/circle markup both pages used into
  `assets/avere-list.js` (`AVERE.renderTable` / `AVERE.renderCircles` + formatting helpers). The two
  pages now render from one source instead of diverging copies.
- **Toolbar polish.** In table view the metric pills are hidden (every metric is reachable by
  clicking a column header anyway); they return for the single-metric circle view. Added a second
  `Top 50 / Ultimii 50 / Lista completă ↗` toolbar below the list, right-aligned, with the currently
  active subset option hidden so it reads as a "switch to the other view" footer.

**Decisions**
- **Ranking spans the full dataset, not the visible 50.** The old "Topuri" leaderboard ranked every
  deputy per metric; an early version of the merged list only re-sorted the on-screen 50, which the
  user rejected. The list now ranks all 332 deputies by the active metric and slices Top/Ultimii 50
  from that. Clicking a sortable table header sets that column as the active metric (re-ranking the
  whole dataset) and flips Top↔Ultimii on repeat clicks. Built on a `METRICS` registry of 9 rankable
  metrics, each with a `val(d)` returning a positive magnitude (null = excluded); `scadere` returns
  `-delta_conturi_ron` so biggest drops rank first.
- The 3 evolution metrics (*Creștere conturi*, *Scădere conturi*, *Imobile noi în mandat*) are
  therefore **first-class rankable metrics** — selectable in the metric bar and used for circle
  sizing — in addition to being table columns. They're computed from `delta_conturi_ron` /
  `delta_imobile` (sign-filtered), so only deputies with ≥2 declarations and a matching direction
  appear in those rankings (75 / 22 / 9 deputies respectively for 2024).
- Top/Bottom 50 rank over deputies *with* a value for the active metric (nulls excluded).
- i18n stays light (footer/loading only), per the existing dashboard convention — the new toolbar
  labels are literal Romanian, like the metric buttons always were. Dropped the now-unused
  `card_averepp_desc` i18n key.
- `lipsa.jpg` (ANI placeholder logo) is filtered in the shared module's `logoOf()`, killing a
  pre-existing 404 on both pages.

**Verification** — `pytest tests/test_build_avere_deputies.py` green (incl. new evolution-field
test); `ruff` clean; `node --check` OK on both the inline `avere.html` script and
`assets/avere-list.js`. Full-dataset ranking checked with a node simulation against the real
`avere-deputies-2024.json`: conturi top = Becali George 32.1M (the corrected value, not the stale
385M), and crestere/scadere/imobile_noi rank 75/22/9 deputies across the whole set; `renderTable`
emits `data-sort="scadere"` for derived columns. Earlier browser pass (pre-ranking-rework): merged
page rendered with 0 console errors, Top/Bottom 50 + metric switch + Cercuri/Tabel work, `Lista
completă ↗` opens deputati-avere.html in the right state, 2024 & 2020 both load, no mobile overflow
at 390px; `Averi++` gone from every nav.

---

### 2026-05-31 — Homepage rebuild, site-wide consistency, cross-links, perf

**What was done**
- **Homepage (`index.html`) rebuilt rich.** Restored the real-data widgets the orphaned render
  functions already implied: party seat-bars (`#party-bars`), legislative indicators
  (`#indicators`), recent votes (`#vote-list`), most-disputed projects (`#top-disputed`), and a
  filterable deputy finder (`#dep-list` + `#f-partid`/`#f-judet`/`#f-search`). Added 7 dashboard
  entry cards so the page is a real hub. Removed the dead `.main{display:none}`; skip-link now
  resolves to `#main-content`. (The old `git show 4aa3c60b4^` body was a mock API-docs console —
  not restored.)
- **Homepage payload ~20 MB → ~1.1 MB.** `loadData()` no longer pulls the 11.4 MB
  `interpelari/legislatura-2024.json` or 6.4 MB `proiecte/legislatura-2024.json` just for counts.
  New `scripts/build_home_stats.py` precomputes 9 2024-scoped counts → `data/v1/stats/home-2024.json`;
  proiecte indicators read the existing 4.8 KB `stats/proiecte-2024.json`. Final fetch set: 5 data
  files (home-stats + deputati + voturi index + amendamente + proiecte-stats). Verified in DevTools:
  exactly those requests, no raw interpelari/proiecte. Wired the build into `scripts/refresh_all.py`
  and documented it in `CLAUDE.md`.
- **Nav drift fixed.** Synced `vot.html`, `proiect.html`, `motiune.html`, `sanctiune.html`,
  `status.html` to the modern nav (adds Partide + Județe, drops the stale `Averi^ALT` label).
- **i18n on the two newest pages.** `partide.html` and `judete.html` now load `i18n.js`, render the
  EN/RO toggle, and carry `data-i18n` on loading + footer strings (using existing keys) so the
  toggle actually switches language. Added the home-hub keys to `i18n.js` (ro + en).
- **Favicon.** New `favicon.svg` (green bar-chart mark) + `<link rel="icon">` on all 16 root pages
  (was 404 everywhere).
- **Cross-links.** `deputat.html`: party badge → `partid.html?id={code}&leg={leg}`, județ →
  `judete.html`. `vot.html`: 286 roster names → `deputat.html?id={cdep_idm}` via a collision-safe
  word-sorted name→idm join (100% match).
- **Dead CSS** removed from `deputati-avere.html` / `deputati-activitate.html` (`.metric-select`,
  `.party-chips`, etc.). Logo unified to italic `stats` (dropped literal asterisks).

**Bugs caught & fixed during browser verification**
- `deputat.html` threw `Identifier 'leg' has already been declared` (duplicate `const leg`) — a
  SyntaxError that silently killed the whole profile render. Removed the redeclaration.
- `partide.html` logged a `lipsa.jpg` 404 (placeholder logo filename in `avereData.parties`) — now
  filtered out at load so it falls back to the colored dot / initials cleanly.
- `index.html` had 148 px of horizontal overflow at 390 px because the `#f-judet` select sized to
  its longest option. Capped `.filter-bar select/input` at `max-width:100%;min-width:0`.

**Decisions**
- Party resolution uses a diacritic-insensitive `normRo()` substring match (data uses cedilla
  `ţ/ş`, regexes used comma `ț/ș`) — fixed the same latent bug in `index.html` and `deputat.html`.
- i18n on dashboard-style pages stays light (footer + loading only), matching the existing
  `avere.html` convention — nav labels are left as proper-noun-ish text.
- `search.html` left orphaned (explicitly out of scope this pass; tracked in backlog).

---

### 2026-05-31 — Județe comparison page (judete.html)

**What was done**
- Created `judete.html`: circle/table visualization with one shape per județ. Metrics: N dep., median ședințe, median propuneri, median venituri RON, median conturi RON.
- Data joined client-side from deputati + avere-deputies + activitate-deputies on `cdep_idm`.
- Long diaspora string normalized to "Diaspora"; 44 județe total.
- Circle color = dominant party; size ∝ selected metric.
- Table view: 7 sortable columns (județ, n, dominant party, 4 median metrics).
- Click on circle/table row opens inline deputy panel below grid: party breakdown chips + deputy rows sorted by ședințe.
- URL state: metric, view, selected judet persisted via pushState.

**Decisions**
- Medians computed only over deputies with non-null values for that metric.
- Diaspora treated as a județ for display (19 deputies in 2024).
- `judAbbr()` maps county names to 2-3 char abbreviations for circle labels.

---

### 2026-05-31 — Party profile page (partid.html)

**What was done**
- Created `partid.html?id=PSD&leg=2024`: party profile showing activity aggregate cards (summed), wealth summary cards (median/total from avere-{leg}.json per_partid), conturi distribution box plot, and a full sortable deputies grid.
- Deputies grid sortable by 5 metrics (Ședințe, Propuneri, Legi, Venituri, Conturi); each row links to `deputat.html`.
- Added "Județe" nav link across all existing pages (anticipating judete.html).

**Decisions**
- Party codes match the `partid` field in stats JSON files (`PSD`, `SOS RO`, `Minoritati`, etc.) — URLs use these directly.
- Full party name derived by joining on `cdep_idm` with deputati data (avoids fragile regex).
- Box plot only shown when ≥5 data points.

---

### 2026-05-30 — Toolbar redesign, URL state, OG meta tags

**What was done**
- Replaced `<select id="metric-select">` with a connected segmented button strip (`.metric-btns`) on both `deputati-avere.html` and `deputati-activitate.html`. Active metric highlights blue; on mobile (≤600px) buttons wrap as individual pills.
- Replaced party-chips inline display with a compact `[Partide ▾]` dropdown (`.party-dd`): shows party color dot, logo, name, deputy count, checkbox per row. Button label updates to `(N/total)` when filtered. Closes on outside click.
- Removed search input and `query` state from both pages entirely.
- Moved year toggle to far right of toolbar via DOM reorder (count badge keeps `margin-left:auto`).
- Added `pushState()` / `applyURLState()` to both pages: params `metric`, `parties`, `view` persisted via `history.replaceState`. `leg` param carried forward if non-default.
- Added OG meta tags (`og:title`, `og:description`, `og:url`, `og:image` 1200×630, `twitter:card: summary_large_image`) to all 6 main pages. Updated existing partial tags on `index.html`.
- Added `scripts/generate_og.py`: starts a local HTTP server, screenshots all 6 pages at 1200×630 with Playwright, saves to `data/assets/og/`.

**Decisions**
- `pushState` preserves `?leg=` param so leg-2020 URLs remain stable across metric/party changes.
- OG image paths use the GitHub Pages base URL; screenshots need to be committed to `data/assets/og/` for them to resolve.
- Search removed completely — no hidden input kept, per spec.

---

### 2026-05-30 — Nav polish + data refresh

**What was done**
- Renamed nav label "Averi<sup>ALT</sup>" → "Averi++" across all 12 pages for consistency with the current branding in `deputati-avere.html`.
- Fixed logo text on older pages from `cdep.api` → `cdep-api stats` to match the landing page.
- Commented out the broken `search.html` link from pages that still had it.
- `index.html` landing: replaced `<ul>` link list with inline middot-separated links — cleaner visual.
- Regenerated `data/v1/stats/avere-2024.json` — `median_conturi` updated from 4,455 to 61,100 RON following the improved PDF parser (conturi section now parsed correctly).

---

### 2026-05-30 — Sortable table view for deputati-avere and deputati-activitate

**What was done**
- Added `≡ Tabel` toggle button to both `deputati-avere.html` and `deputati-activitate.html` toolbars. The avere page already had a disabled list button; it was enabled and repurposed. The activitate page got a new toggle inserted between the legislature selector and the metric dropdown.
- In table view: all 6 metric columns shown simultaneously (vs. one at a time in circle view), each cell shows value above a 3px inline bar scaled to the column max.
- Clicking any column header sorts the table; clicking twice flips to ascending; clicking a third time resets to default.
- The metric dropdown is hidden in table view. Switching back to circles syncs the dropdown to the last sort column.
- Name column is sticky-left for horizontal scroll on narrow screens.
- Bar scaling uses `Math.abs` so negative `datorii_ron` values display correctly.

**Decisions**
- No shared JS file — both pages are self-contained to match existing project conventions.
- Bar width scales to column max within the current filtered set — rescales when search/party filters change.
- Datorii column value text is red (debt stands out) in the avere table unless it is the active sort column (blue takes priority).
- activitate COLUMNS omit `isDebt` (all values are non-negative counts).

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
