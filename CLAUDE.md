# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install deps
pip install -r requirements-dev.txt
pre-commit install

# Lint + format
ruff check .
ruff format .

# Tests (PYTHONPATH required)
PYTHONPATH=. pytest -v
PYTHONPATH=. pytest tests/test_parsers_helpers.py  # single file

# Type check (soft — not blocking CI)
mypy scrapers schemas scripts

# Run a scraper locally (requires network access from Romania — cdep.ro geo-blocks cloud)
python scripts/run_deputati.py --leg 2024 --verbose
python scripts/run_voturi.py --days 7 --leg 2024 --verbose
python scripts/run_interpelari.py --year 2026 --verbose

# Derived/aggregated builds (run after scrapers)
python scripts/build_comisii.py --leg 2024
python scripts/build_amendamente.py --leg 2024
python scripts/build_feeds.py --leg 2024 --per-type 15 --limit 60
python scripts/build_declaratii_avere.py --leg 2024
python scripts/build_avere_stats.py --leg 2024  # aggregate stats for the /avere.html dashboard

# HTML pages + Pagefind index
python scripts/generate_html.py
npx pagefind --site pages --output-path pagefind

# Validate generated data
PYTHONPATH=. python scripts/validate_data.py

# Serve locally
python -m http.server 8000
```

## Architecture

See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the full layer map, ID cross-links, and guide for adding new endpoints.

## Code conventions

- **Python 3.11+** — use `StrEnum`, `datetime.UTC`, `from __future__ import annotations`.
- **Pydantic v2** for all data models; export via `.model_dump(mode="json")`.
- **Type hints required** on all public functions (`mypy --strict` is the target, soft for now).
- **ruff** for lint and format (100 char line length); runs as pre-commit hook.
- Commit types: `feat`, `fix`, `data`, `docs`, `test`.
- `PYTHONPATH=.` is required for all `python scripts/` and `pytest` invocations.

## Env vars for scrapers

| Var | Default | Effect |
|---|---|---|
| `CDEP_SCRAPE_WORKERS` | `1` | Parallel fetch threads; set to 2–4 on GitHub Actions |
| `CDEP_HTTP_THROTTLE_SECONDS` | `0.5` | Delay between requests |
| `PYTHONIOENCODING` | — | Set to `utf-8` on Windows runners to handle diacritics |

## Project tracking

- When detecting things that need to be addressed later, add to `docs/backlog.md`. Use a checkbox `- [ ]` entry with a clear title and enough context to act on it later.
- After completing any meaningful work, add an entry to `docs/activity-log.md` under the relevant section heading with a `### YYYY-MM-DD — Short Title` entry. Include what was done, why, and any non-obvious decisions.
