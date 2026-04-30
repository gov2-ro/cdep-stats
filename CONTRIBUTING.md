# Contribuie la cdep-api-poc

Mulțumim pentru interesul în acest proiect! Datele parlamentare sunt mai utile când oricine le poate îmbunătăți.

## Tipuri de contribuții

- **Corecții de date**: dacă vezi un câmp greșit (ex. partid eronat, dată inversată), deschide un issue cu link la deputat / vot / proiect.
- **Endpoint-uri noi**: secțiuni de pe cdep.ro care nu sunt încă acoperite (vezi [`sitemap.md`](./sitemap.md) §13 pentru lista completă).
- **Bug-uri de parsing**: dacă cdep.ro a schimbat HTML-ul și un parser pică, deschide issue cu URL-ul exact.
- **Documentație**: clarificări în README, exemple de utilizare în Python/JavaScript/curl.
- **Notebook-uri/dashboard-uri**: dacă faci ceva cu datele, ne-ar plăcea să-l vedem în [INTEGRATIONS.md](./INTEGRATIONS.md).

## Setup local

```bash
git clone https://github.com/Endimion2k/cdep-api-poc.git
cd cdep-api-poc
python -m venv .venv
.venv\Scripts\activate              # Windows
# source .venv/bin/activate         # Linux/macOS
pip install -r requirements-dev.txt

# Hooks pre-commit (lint+format automat la fiecare commit)
pre-commit install
```

După `pre-commit install`, `git commit` va rula automat ruff + alte verificări pe fișierele modificate. Dacă ceva pică, commit-ul e blocat până fixezi.

Pentru a rula manual toate hook-urile:
```bash
pre-commit run --all-files
```

## Standarde cod

- **Python 3.11+** (folosim `StrEnum`, `UTC`, `from __future__ import annotations`).
- **Lint+format**: `ruff check . && ruff format --check .` — rulează automat în CI.
- **Pydantic v2** pentru toate modelele de date.
- **Type hints obligatorii** pe funcțiile publice.

## Structură repo

```
cdep-api-poc/
├── api/openapi.yaml            # Spec API
├── data/v1/                    # JSON public, generat automat
├── docs/                       # Swagger UI
├── pages/                      # HTML pentru indexare Pagefind
├── pagefind/                   # Index search (generat)
├── schemas/                    # Pydantic models per resursă
├── scrapers/                   # Cod scraping per resursă
├── scripts/                    # Runner-i, builderi, helpers
├── tests/                      # pytest + fixtures HTML
├── .github/workflows/          # CI + cron scrape
├── CHANGELOG.md
├── CONTRIBUTING.md             # acest fișier
├── README.md
├── TIMELINE.md
└── sitemap.md
```

## Workflow de contribuție

1. **Fork** repo-ul + clone local
2. **Branch nou**: `git checkout -b fix/numele-bugului`
3. **Modificări** + verificare locală: `ruff check . && ruff format . && pytest`
4. **Commit** cu mesaj clar (vezi convenții mai jos)
5. **Push** + **Pull Request** către branch-ul `dev`

## Convenții commit

Format: `<tip>: <descriere scurtă>`

| Tip | Folosit pentru |
|---|---|
| `feat` | Endpoint nou, schemă nouă, feature majoră |
| `fix` | Bug de parsing, regresie, lint |
| `data` | Bootstrap, refresh date scrape |
| `docs` | README, CHANGELOG, comentarii |
| `test` | Tests noi, fixture-uri |
| `refactor` | Rearanjare cod fără schimbare comportament |
| `style` | Formatare (ruff) |
| `chore` | Workflow, dependencies, infrastructură |

Exemple:
- `feat: /motiuni endpoint with vote tracking`
- `fix(interpelari): regex respects diacritics in adresant_grup`
- `data: bootstrap legislatura 2020 voturi`

## Snapshot tests

Când cdep.ro schimbă HTML-ul, parserele se rup. Pentru a prinde regresia rapid:

1. Rulează `python scripts/save_fixtures.py` ca să refresh-uiești fixture-urile din `tests/fixtures/`.
2. Rulează `pytest tests/test_snapshot_parsers.py -v` ca să verifici că parserele extrag corect.
3. Dacă un test cade, **fixează parserul**, nu fixture-ul. Fixture-ul e snapshot-ul realității cdep.ro.

## Adăugare endpoint nou

Pașii standard pentru a adăuga un endpoint pe o secțiune nouă din cdep.ro:

1. **Discovery** URL pattern (în `sitemap.md` §13).
2. **Schema** în `schemas/<nume>.py` — Pydantic model.
3. **Scraper** în `scrapers/<nume>.py` cu `parse_detail` + `scrape`/`scrape_year`.
4. **Runner** în `scripts/run_<nume>.py` cu `--leg`/`--year` args.
5. **HTML pages** în `scripts/generate_html.py` (function `generate_<nume>`).
6. **Workflow** în `.github/workflows/scrape.yml` (pas nou).
7. **OpenAPI** în `api/openapi.yaml` (path + schema).
8. **Snapshot test** în `tests/test_snapshot_parsers.py`.
9. **Index** în README.md (tabelul de cifre live).

## Contact

- **Issues**: pentru bug-uri și sugestii ale features
- **Pull Requests**: pentru schimbări concrete cod/docs
- **Repo**: https://github.com/Endimion2k/cdep-api-poc

## Cod de conduită

Fii respectuos. Acceptăm critică tehnică argumentată, nu atacuri personale. Datele parlamentare sunt politic sensibile — păstrăm proiectul **neutru**, ne ocupăm doar de calitatea structurată a datelor publice, nu de interpretarea lor politică.
