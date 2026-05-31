# Plan: Wealth Dashboard (`/avere` stats + `avere.html`)

## Context

The project is a static-file parliamentary API (JSON on GitHub Pages, no server). The
richest single dataset is `declaratii-avere`: PDF-parsed wealth declarations for 332
deputies (2024), each with chronological figures — liquid accounts (`conturi_total_ron`),
annual income (`venituri_anuale_ron`), debt (`datorii_total_ron`), property counts
(`terenuri_count`, `cladiri_count`, `suprafata_total_mp`), vehicle count (`auto_count`),
and first→last **deltas**. Each record cross-links to party / county / gender / age via
`canonical_id`.

Today there is no analytical surface — only landing-page counters and Pagefind search.
This is the **first** of a sequenced set of dashboards (full menu brainstormed; wealth
chosen first). Audience: **journalists** (rankings, outliers, red-flag swings) **and
researchers** (distributions, per-party comparisons, downloadable aggregates). Delivery:
**precompute aggregate JSON via a `build_*` script → a static chart page reads it**.

Outcome: `avere.html` — a wealth dashboard with leaderboards, party comparisons,
distributions, and a red-flag section, backed by a new `data/v1/stats/avere-{leg}.json`
aggregate endpoint.

### Honesty constraint (drives the design)
We have *measured* monetary fields (conturi, venituri, datorii) but only *counts* for
property and vehicles — **no asset values**. We therefore will **not** invent a single
"net worth" number. We rank/compare on the real measured fields and show property/vehicle
portfolios as counts. A methodology/caveats block states this plainly (PDF-parsed, RON
normalized at fixed rates, `auto_count` is a mention proxy).

## Approach

Two artifacts plus wiring, following existing conventions
(`build_*.py` + standalone HTML page + vanilla `fetch` + `i18n.js`).

### 1. `scripts/build_avere_stats.py` (new) — reuse `raport_avere.py` logic
Reads `data/v1/declaratii-avere/legislatura-{leg}.json` (the summary index already built
by `build_declaratii_avere.py`). Emits `data/v1/stats/avere-{leg}.json`:

- `meta`: generated_at, source, count, **caveats string**, rates used.
- `leaderboards` (journalist angle) — top 15 each, `{nume, partid, value, n_declaratii,
  detail_url}`:
  - `top_conturi` (largest liquid assets, `ultima_conturi_ron`)
  - `top_venituri` (top earners, `ultima_venituri_ron`)
  - `top_datorii` (most indebted, derive from detail or carry in summary — see note)
  - `top_imobile` (most properties, `ultima_imobile_count`)
  - `delta_crestere` / `delta_scadere` (biggest cash increases / decreases — **red flags**)
  - `delta_imobile` (most newly-acquired properties in mandate)
- `per_partid` (researcher angle) — for each party with N≥3: `{n, median_conturi,
  mean_conturi, median_venituri, median_datorii, total_imobile, total_suprafata_mp,
  conturi_values[]}` (raw array kept for client-side box-plot/quartiles).
- `distributie`: overall quartiles (q1/median/q3/p90) for conturi & venituri.

Reuse the sort/median/defaultdict logic verbatim from `raport_avere.py:26-134`; change
the sink from `print` to a `model_dump`-style dict written with
`json.dumps(..., ensure_ascii=False, indent=2)`. Match `build_declaratii_avere.py` for
`Meta`, `ROOT`, arg parsing (`--leg`, `--all`, default 2024).

> Note on `datorii`: `AvereSummary` does not currently carry `ultima_datorii_ron`. Either
> (a) read it from the per-deputy detail files in the build script (preferred — no schema
> change), or (b) add the field to `AvereSummary` + `build_declaratii_avere.py`. Plan uses
> (a) to avoid re-running the expensive PDF build.

### 2. `avere.html` (new) — dashboard page
Standalone page mirroring `deputat.html` structure (same header/footer, `i18n.js`,
`data-i18n` keys, `?leg=` query param, source-JSON link). Loads
`data/v1/stats/avere-{leg}.json` with `fetch`. Charting via **Chart.js v4 from CDN**
(no build step; consistent with the no-bundler setup). Sections:

1. **Stat cards** — N deputies, median liquid assets, median income, # red-flag swings.
2. **Leaderboards** — tabbed/sortable tables (richest, top earners, most indebted, most
   properties). Each row links to the deputy's detail JSON / profile.
3. **Party comparison** — grouped bar chart: median conturi / venituri / datorii per party.
4. **Distribution** — per-party box-plot (or histogram) of liquid assets from
   `conturi_values[]`.
5. **Red flags** — biggest cash increases & decreases over the mandate, with delta + #
   declarations; framed as "needs explanation, not proof".
6. **Methodology & caveats** + prominent link to the raw `avere-{leg}.json` (researcher
   transparency / downloadable data).

### 3. Wiring
- `scripts/validate_data.py` — register the `data/v1/stats/avere-{leg}.json` output path.
- `scripts/refresh_all.py` — call `build_avere_stats.py` after `build_declaratii_avere.py`.
- `index.html` — add an "Averi / Wealth" entry to nav and a link from the stats area.
- `i18n.js` — add the new `data-i18n` keys (RO + EN) used by `avere.html`.
- `CLAUDE.md` "Derived/aggregated builds" — add the `build_avere_stats.py` command.
- `docs/activity-log.md` — add a `### 2026-05-28 — Wealth dashboard` entry.

## Critical files
- Reuse: `scripts/raport_avere.py` (top-list + per-party logic), `scripts/build_declaratii_avere.py` (Meta/IO conventions), `schemas/avere.py` (fields).
- New: `scripts/build_avere_stats.py`, `avere.html`.
- Edit: `scripts/validate_data.py`, `scripts/refresh_all.py`, `index.html`, `i18n.js`, `CLAUDE.md`, `docs/activity-log.md`.
- Data inputs: `data/v1/declaratii-avere/legislatura-2024.json` (+ `legislatura-2024/{idm}.json` for datorii).

## Verification
1. `PYTHONPATH=. python scripts/build_avere_stats.py --leg 2024` → inspect
   `data/v1/stats/avere-2024.json`: leaderboards non-empty, per-party medians match a
   spot-check against `raport_avere.py` output (run it, compare top-10 conturi).
2. `PYTHONPATH=. python scripts/validate_data.py` passes for the new path.
3. `ruff check scripts/build_avere_stats.py && ruff format --check`.
4. Serve (`python -m http.server 8000`), open `/avere.html?leg=2024`: cards populate,
   charts render, leaderboard links resolve, language toggle works, caveats + raw-JSON
   link present. Confirm with Chrome DevTools MCP (screenshot + no console errors).
5. Confirm no fabricated "net worth" appears anywhere; property/vehicles shown as counts.

## Out of scope (next in the sequence)
Per-deputy report card (J58), voting/accountability/activity dashboards, 2020/2016
wealth pages (build script supports `--all`, but page wiring deferred), geographic/gender
breakdowns of wealth.
