# Activity Log

Chronological record of meaningful work. Newest entries on top within each section.

## Dashboards

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
