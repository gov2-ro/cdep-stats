# Activity Log

Chronological record of meaningful work. Newest entries on top within each section.

## Dashboards

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
