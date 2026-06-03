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

# **Recommended: Combined pipeline + deploy in one command**
./scripts/run-and-deploy.sh daily user@host:/path/to/public_html    # daily scrape + quick deploy (~15 min)
./scripts/run-and-deploy.sh weekly user@host:/path/to/public_html   # weekly scrape + full deploy (~60 min)
./scripts/run-and-deploy.sh daily                                   # scrape + build only (no deploy)

# Or run separately:
# Orchestrate scrapers + builds (cadence-aware, dynamic year)
python3 scripts/refresh_all.py                  # weekly (default: daily + weekly stages)
python3 scripts/refresh_all.py --cadence daily  # fast daily run (~10-15 min, no PDF parsing)
python3 scripts/refresh_all.py --cadence full   # full refetch + PDFs + HTML/sitemap generation
python3 scripts/refresh_all.py --skip-voturi    # omit slow voturi scraper
python3 scripts/refresh_all.py --only interpelari proiecte  # selective run

# Deploy to production
./scripts/deploy.sh user@host:/path/to/public_html     # full deploy (all data, ~5-10 min)
./scripts/deploy.sh --quick user@host:/path/to/public_html  # fast daily sync (~30s, stats/HTML/data only)

# OR: Build deploy.zip for scp-based deploy (if rsync not available on target)
python scripts/build_web.py

# N-gram analysis: discover formulaic patterns in agenda descriptions (no new deps)
PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024              # bigrams
PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --ngram 3    # trigrams
PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --words      # single-word topical frequencies
PYTHONPATH=. python scripts/analyze_ngrams.py --leg 2024 --compare    # diff extracted vs. unextracted

# Validate generated data
PYTHONPATH=. python scripts/validate_data.py

# Serve locally (HTML lives in web/, data in data/, assets in assets/)
# web/data and web/assets are symlinks to ../data and ../assets (gitignored, local dev only)
# If symlinks are missing: cd web && ln -sf ../data data && ln -sf ../assets assets && cd ..
python -m http.server 8000
# Then open: http://localhost:8000/web/
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
