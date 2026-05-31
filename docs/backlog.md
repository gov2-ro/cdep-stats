# Backlog

Known issues and future improvements. Use `- [ ]` checkboxes; add enough context to act on later.

---

## Deploy — Removed pages to revisit

- [ ] **Re-evaluate `vot.html` (voturi recente widget) for the landing page**
  - Individual vote pages (`data/v1/voturi/{leg}/{id}.json`) are 4 500+ files that bloat the archive. Removed `vot.html` and the "Voturi recente" widget from `index.html`. Revisit if a lightweight summary view (e.g. render from `_index.json` only, no drill-down) is worth adding back.

- [ ] **Re-evaluate `proiect.html` (cele mai disputate proiecte widget) for the landing page**
  - `proiect.html` had no inbound nav links. The "Cele mai disputate proiecte" widget on `index.html` (top 5 by amendments) was removed along with it. `data/v1/proiecte/` and `data/v1/amendamente/` are excluded from the deploy archive but kept on disk. Revisit if a project detail page is worth wiring into the nav properly.

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


## Misc

- [x] replace cdep link from /pls/parlam/structura2015.mp?idm={ID}&cam=2&leg=2024 to /ords/pls/parlam/structura2015.mp?idm={ID}&leg=2024
- [x] link to [monitorul.ai](https://monitorul.ai) via [MCP](https://monitorul.ai/mcp).  
  - [x] find URI correspondences
  - [x] Add contextual relevant links.
  - [ ] see if any pages from monitorul.ai are missing
- [ ] cercuri in some views don't render right
- [x] OG info
  - [ ] fix og:image
- [x] move html files in folder, not root. — created `web/` deployment folder with build script (2026-06-01)
- [ ] show cars, homes, terenuri as icons, one per each? - relative to suprafata or kph?
- [x] **Remove dead CSS rules in deputati-avere.html and deputati-activitate.html** — done 2026-05-31; removed `.metric-select`, `.search-input`, `.party-chips`, `.party-chip` rules.
- [ ] re-add sanctiune.html, vot.html and other pages found in https://github.com/Endimion2k/cdep-api-poc
- [ ] make more static? we generate static but load data from json?! is this SEO friendly?


## Site consistency / front door

- [x] Top nav. Rename site title: Cdep stats. Normalize nav in all pages. Add link to cdep-api on all pages at the end. Remove language swticher border, add flag emoji for language switcher.
- [ ] add top bar with - not official gov.ro site notice (one time / dismissable, save state to browser/cookies): `Versiune alfa / preview. Acesta nu este un proiect oficial al Guvernului României. Date preluate de pe cdep.ro`. See https://ins.gov2.ro/

- [ ] top nav dark background?
- [ ] **Refactor the 16 copy-pasted root pages to a shared header/nav/footer** — nav drift (pages
  falling behind on links/labels) keeps recurring because each page hand-copies its `<nav>`. Extract
  to a shared `assets/nav.js` (or generate these pages like `pages/`) so header/nav/footer live in
  one place. This pass re-synced 5 pages by hand; the root cause remains. (2026-05-31: the
  avere/deputati-avere list logic was extracted to a shared `assets/avere-list.js` — a working
  proof of the shared-module approach; nav/header/footer are still copy-pasted.)
- [ ] **Relink and restyle `search.html`** — currently orphaned (no nav links into it) and on the
  old design. Re-add it to the nav and bring it on-brand. Left out of the 2026-05-31 consistency
  pass on purpose.
- [ ] **`proiect.html` initiator → deputy profile links** — the initiator is a free-text blob with
  no IDs, so linking needs exact name→`cdep_idm` matching against deputati (fragile, risk of
  mislinks). Implement only if the match is provably clean; otherwise leave as text.
- [ ] **`partid.html` long roster is heavy** — the flat ~92-row deputy list makes the page an
  endless scroll. Consider a compact row style or a show-more cap (without hiding data by default).

