# CDEP Stats — statistici parlamentare Camera Deputaților

[lab.gov2.ro/cdep](https://lab.gov2.ro/cdep/)

Dashboard de statistici și transparență parlamentară pentru Camera Deputaților cu 15+ pagini de analiză, filtrare interactivă și extragere automată de entități.

<mark>⚠️Notă</mark>: proiect în lucru (WIP) – datele nu sunt 100% verificate. Dacă observi vreo incorectitudine adăugă [un issue](https://github.com/gov2-ro/cdep-stats/issues) sau scrie-ne la poșta redacției: cancelarie@gov2.ro 

---

## 🌐 Pagini și funcționalități

### Analitice
| Pagină | URL | Descriere |
|--------|-----|-----------|
| **Index** | `index.html` | Panou de bază cu statistici agregate (deputați, voturi, proiecte, interpelări, comisii, moțiuni, ordine de zi, averi, sanțiuni) |
| **Voturi** | `voturi.html` | Listă plenului cu filtrare pe stadiu, tip, dată; detalii pe `vot.html` cu defalcare nominală per deputat și agregare pe partide |
| **Interpelări** | `interpelari-stats.html` | Rate de răspuns, top asker/ministrii, trend lunar din 9.700+ interpelări (2024–2026) |
| **Proiecte** | `proiecte-stats.html` | Defalcare pe stadiu (inițiat, pe ordinea, promulgat), rate de succes per partid, trend lunar |
| **Activitate Deputați** | `deputati-activitate.html` | Leaderboard pe ședințe, luări de cuvânt, propuneri legislative, legi promulgate; filtrare pe partid/județ |
| **Averi Deputați** | `avere.html` → `deputati-avere.html` | Leaderboard pe conturi, venituri, datorii, imobile; percentile și delta vs. declarația anterioară; analiză per partid |
| **Interese Declarate** | `interese.html` | Declarații de interese din PDF-uri cu timestamp de actualizare |

### Entități
| Pagină | URL | Descriere |
|--------|-----|-----------|
| **Deputați** | `deputat.html?id=...` | Profil complet cu activitate, voturi, interpelări, avere, partid, comisii; link la [monitorul.ai](https://monitorul.ai/) |
| **Partide** | `partide.html` → `partid.html?id=...` | Componență, culori/lozuri, rate agregare voturi |
| **Comisii** | `comisii.html` → (detaliu pe deputat.html) | Listă comisii cu conducere și link-uri la membri |
| **Județe** | `judete.html` | Distribuție deputați, rate vot/activitate per județ |
| **Moțiuni** | `motiuni.html` | Moțiuni parlamentare cu filtrare pe stadiu |
| **Ordine de Zi** | `ordine-zi.html` → `ordine-zi-lista.html` | **Lista filtrabilă** a ședințelor plenului cu filtre pe tip (proiecte/hotărâri/moțiuni), comisie, instituție, urgență; context-aware dynamic counts; **Agendă detaliată** cu clasificare automată, extragere entități (comisii, acte normative, indicatori procedurali) |
| **Sesiuni** | `sesiune.html?id=...` | Detalii ședință: ordinea de zi, documente referențiate, transcrie stenogramă (dacă disponibilă) |
| **Proiecte** | `proiect.html?id=...` | Bill detail: proponent, stadiu, timeline, link voturi, amendamente admise/respinse |

### Alte resurse
| Pagină | URL | Descriere |
|--------|-----|-----------|
| **Sitemap** | `sitemap.xml` | Index pentru căutare și SEO |
| **Feed Atom** | `feed.atom` | Ultimele 60 vot, proiecte, interpelări, sanțiuni (15 fiecare) |
| **Feed JSON** | `feed.json` | Formatul JSON Feed v1.1 |

## Screenshots

![statistici deputați](docs/reference/screenshots/cdep-stats-0.png)
![avere deputați](docs/reference/screenshots/cdep-stats-1.png)
![avere deputați 2](docs/reference/screenshots/cdep-stats-2.png)
![activitate](docs/reference/screenshots/cdep-stats-3.png)
![proiecte](docs/reference/screenshots/cdep-stats-4.png)
![interpelări](docs/reference/screenshots/cdep-stats-5.png)


## 🔧 Scripturi și Pipeline

### Orchestrator

**Cadence-aware runner** — selectează stagii pe bază de frecvență:

```bash
python3 scripts/refresh_all.py                  # weekly (default: daily + weekly stages)
python3 scripts/refresh_all.py --cadence daily  # fast (~10-15 min, no PDFs)
python3 scripts/refresh_all.py --cadence full   # full refetch + PDFs + HTML generation
python3 scripts/refresh_all.py --full           # backward-compat alias for --cadence full
python3 scripts/refresh_all.py --skip-voturi    # omit slowest scraper
python3 scripts/refresh_all.py --only interpelari proiecte  # selective stages
```

Writes `data/v1/last_updated.json` after each run (displayed in footer).

### Scrapers (externi — fetch de la cdep.ro)

| Script | Cadență | Output | Note |
|--------|---------|--------|------|
| `run_deputati.py` | weekly | `deputati/legislatura-{leg}.json` | Profiluri deputați; `--full` pentru refetch weekly |
| `run_voturi.py` | daily | `voturi/{leg}/_index.json` + per-vote JSON | Default `--days 7`; incremental by ID |
| `run_interpelari.py` | daily | `interpelari/legislatura-{leg}/` | Dinamică pe an; `--years` pentru backfill |
| `run_proiecte.py` | daily | `proiecte/legislatura-{leg}/` | Dinamică pe an; `--full` pentru refetch status |
| `run_motiuni.py` | daily | `motiuni/legislatura-{leg}.json` | `--full` weekly |
| `run_ordine_zi.py` | daily | `ordine-zi/legislatura-{leg}.json` | Dinamică pe an; 33.5 MB monolith (candidat split) |
| `run_sanctiuni.py` | weekly | `sanctiuni/legislatura-{leg}.json` | — |
| `run_stenograme.py` | weekly | `stenograme/legislatura-{leg}/{YYYYMMDD}.json` | Transcrii plen; `--full` full refetch |
| `run_declaratii.py` | weekly | `declaratii/legislatura-{leg}.json` | URLs PDF (nu și conținut) |
| `run_doc_comisii.py` | weekly | `doc-comisii/all.json` | ~85.000 docs comisii; `--pages N` incremental |

### Build Scripts (derivate — procesare date locale)

| Script | Cadență | Output | Descriere |
|--------|---------|--------|-----------|
| `build_comisii.py` | daily | `stats/comisii-{leg}.json` | Agregare din deputați; dedup nume |
| `build_amendamente.py` | daily | `stats/amendamente-{leg}.json` | Bills cu ≥1 amendament, sortate |
| `build_home_stats.py` | daily | `stats/home-{leg}.json` | Precompute counts pt. index.html |
| `build_proiecte_index.py` | daily | `stats/proiecte-index-{leg}.json` + `bill-vote-map-{leg}.json` | Thin index + cross-reference |
| `build_feeds.py` | daily | `feed.atom` + `feed.json` | Balanced feeds (15 per type, 60 total) |
| `build_interpelari_stats.py` | daily | `stats/interpelari-{leg}.json` | Rat răspuns, asker top, ministrii, trend |
| `build_proiecte_stats.py` | daily | `stats/proiecte-{leg}.json` | Stadiu breakdown, per-party success, trend |
| `build_split_by_year.py` | daily | `{endpoint}/legislatura-{leg}/{year}.json` + `_index.json` | Reduce mobil load (21MB → 3MB/year) |
| `build_status.py` | daily | `status.json` | Contori + timestamp freshness |
| `build_avere_stats.py` | full | `stats/avere-{leg}.json` + `avere-context-{leg}.json` | Top leaderboards + percentile rankings |
| `build_declaratii_avere.py` | full | `declaratii-avere/legislatura-{leg}/` | Parse PDF-uri; summari + per-deputy detail |
| `build_declaratii_intereses.py` | full | `declaratii-interese/legislatura-{leg}/` | Parse interest PDFs |
| `build_activitate_deputies.py` | weekly | `stats/activitate-deputies-{leg}.json` | Activity fields + party + age cohort enrichment |
| `generate_html.py` | full | `pages/{tip}/{id}.html` | One HTML per entity (search indexing) |
| `build_sitemap_xml.py` | full | `web/sitemap.xml` | SEO sitemap |

### Utility Scripts

```bash
# N-gram analysis — detect formulaic patterns in agendas
PYTHONPATH=. python3 scripts/analyze_ngrams.py --leg 2024              # bigrams
PYTHONPATH=. python3 scripts/analyze_ngrams.py --leg 2024 --ngram 3    # trigrams
PYTHONPATH=. python3 scripts/analyze_ngrams.py --leg 2024 --words      # word frequencies
PYTHONPATH=. python3 scripts/analyze_ngrams.py --leg 2024 --compare    # extracted vs unextracted

# Validate all generated data
PYTHONPATH=. python3 scripts/validate_data.py

# Split ordine-zi monolith into modular CSV + JSON (experimental)
python3 scripts/split_ordine_zi.py              # → sesiuni.csv, items.csv, docs.csv, entities.json
python3 scripts/merge_ordine_zi.py              # → legislatura-2024-merged.json
```

---

## 📤 Deploy

### Full deploy (all data, ~5-10 min)
```bash
./scripts/deploy.sh user@host:/path/to/public_html
```
Syncs all 270 MB stable blobs (voturi, proiecte, ordine-zi, interpelari, declaratii-avere) via checksum-based rsync, then dynamic files (HTML, stats, assets).

### Fast daily deploy (~30 sec)
```bash
./scripts/deploy.sh --quick user@host:/path/to/public_html
```
Skips stable blobs (assumes prior full sync). Only syncs dynamic files (stats, HTML, last_updated.json, small data dirs).

### Dry-run
```bash
DRY=1 ./scripts/deploy.sh [--quick] user@host:/path/to/public_html
```

### Legacy zip-based deploy (if rsync not available)
```bash
python3 scripts/build_web.py                    # → deploy.zip
# then: scp deploy.zip user@host:/tmp/ && ssh user@host unzip /tmp/deploy.zip -d /path/to/public_html
```

---

## 📊 Date

- **Sursa**: [www.cdep.ro](https://www.cdep.ro) — date publice Camera Deputaților
- **Fetch**: [Endimion2k/cdep-api-poc](https://github.com/Endimion2k/cdep-api-poc) scraper
- **Licență**: [Open Government License v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- **Geo + Assets**: `assets/geo/` (TopoJSON), `assets/imagini/` (deputați), `assets/legenda-partide.csv`

---

## 🏗️ Arhitectură

Arhitectura completă la [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

**Snapshot**: 
- **Scrapers** (Python 3.11+, Pydantic v2) → `data/v1/{endpoint}/` JSON
- **Builds** (Pydantic aggregation) → `data/v1/stats/` JSON indexe + metadata
- **Web** (vanilla JS + HTML) → responsive pages, Pagefind full-text search
- **Footer** → async-fetches `last_updated.json` pentru timestamp

---

## 🚀 Setup Local

```bash
# Install deps
pip install -r requirements-dev.txt
pre-commit install

# Lint + format
ruff check . && ruff format .

# Tests
PYTHONPATH=. pytest -v
PYTHONPATH=. pytest tests/test_parsers_helpers.py

# Type check (soft)
mypy scrapers schemas scripts

# Serve locally (requires web/{data,assets} symlinks)
cd web && ln -sf ../data data && ln -sf ../assets assets && cd ..
python3 -m http.server 8000
# → http://localhost:8000/web/

# Run scraper (requires Romania IP or VPN)
python3 scripts/run_deputati.py --leg 2024 --verbose

# Orchestrate all (daily mode)
python3 scripts/refresh_all.py --cadence daily
```
