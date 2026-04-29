# CDEP API — Camera Deputaților, date deschise

Un API REST public, gratuit, care expune datele parlamentare ale **Camerei Deputaților** din România în format **JSON**. Construit deasupra surselor publice de pe [cdep.ro](https://www.cdep.ro), actualizat zilnic.

> **Status**: 🟢 POC funcțional · 6 endpoint-uri live · search full-text live · cron zilnic activ

[![License: OGL v3.0](https://img.shields.io/badge/license-OGL%20v3.0-blue.svg)](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
[![Status: POC live](https://img.shields.io/badge/status-POC%20live-green.svg)](https://endimion2k.github.io/cdep-api-poc/)
[![Docs: Swagger](https://img.shields.io/badge/docs-Swagger%20UI-green.svg)](https://endimion2k.github.io/cdep-api-poc/docs/swagger.html)

**Demo live:** https://endimion2k.github.io/cdep-api-poc/

---

## Cifre live (legislatura 2024)

| Endpoint | Records | URL |
|---|---:|---|
| `/deputati` | **335** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json) |
| `/voturi` (cu defalcare nominală) | **816** | [_index.json](https://endimion2k.github.io/cdep-api-poc/data/v1/voturi/2024/_index.json) |
| `/sanctiuni` | **6** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/sanctiuni/legislatura-2024.json) |
| `/interpelari` (2024–2026) | **9.326** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/interpelari/legislatura-2024.json) |
| `/comisii` (agregat) | **37** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/comisii/legislatura-2024.json) |
| `/proiecte-lege` (2024–2026) | **1.641** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/proiecte/legislatura-2024.json) |
| **Search full-text** | **~12.500 entități indexate** | [/search](https://endimion2k.github.io/cdep-api-poc/search.html) |

Datele se actualizează automat zilnic la 04:00 UTC printr-un workflow GitHub Actions.

---

## De ce există acest proiect

Camera Deputaților publică date de interes public vast — voturi nominale, prezență, proiecte legislative, activitate în comisii — dar exclusiv sub formă de pagini HTML și PDF-uri. Lipsește o interfață programatică care să permită:

- **jurnaliștilor** să monitorizeze rapid deputații din circumscripția lor,
- **ONG-urilor** să urmărească proiectele de lege relevante,
- **cercetătorilor** să facă analize cantitative,
- **dezvoltatorilor civici** să construiască dashboard-uri, boți, extensii de browser,
- **cetățenilor** să-și verifice propriul deputat.

Acest API transformă HTML-ul public în JSON structurat, versionat și documentat.

---

## Endpoint-uri

### ✅ Live în POC

| Endpoint | Format | Descriere |
|---|---|---|
| `GET /deputati/legislatura-{leg}.json` | JSON | Profile complete (bio, partid, județ, comisii, contoare activitate) |
| `GET /voturi/{leg}/_index.json` | JSON | Index voturi (timestamp, descriere, counts agregate) |
| `GET /voturi/{leg}/{idv}.json` | JSON | Detalii vot cu defalcare nominală (DA/NU/AB per deputat) |
| `GET /sanctiuni/legislatura-{leg}.json` | JSON | Sancțiuni disciplinare (diminuare indemnizație, avertisment etc.) |
| `GET /interpelari/legislatura-{leg}.json` | JSON | Interpelări/întrebări parlamentare cu informații despre răspuns |
| `GET /comisii/legislatura-{leg}.json` | JSON | Comisii permanente + speciale comune cu lista membrilor și conducerea |
| `GET /proiecte/legislatura-{leg}.json` | JSON | Proiecte legislative cu stadiu, inițiator, timeline, voturi, decret promulgare |
| `GET /search.html?q=` | HTML | Căutare full-text (Pagefind) peste toate cele de mai sus |

### 🔜 Propuse (neimplementate)

| Endpoint | Status |
|---|---|
| `GET /amendamente` | viitor — extragere din proiectele individuale |
| `GET /motiuni`, `/declaratii-politice`, `/stenograme` | viitor |
| `GET /feed.atom`, `/feed.json` | viitor (notificări modificări) |

Vezi [`api/openapi.yaml`](./api/openapi.yaml) pentru schema completă.

---

## Arhitectură

```
┌──────────────┐  HTTPS+SSL legacy   ┌─────────────────────┐  commit Git    ┌──────────────────┐
│   cdep.ro    │ ──────────────────► │  Self-hosted runner │ ─────────────► │   GitHub repo    │
│  (HTML+XML)  │  ISO-8859-2,SHA1    │   (PC Windows RO)   │                │  data/v1/*.json  │
└──────────────┘                     └─────────────────────┘                └────────┬─────────┘
       ▲                                       │                                      │
       │                              cron 04:00 UTC                          GitHub Pages CDN
   geo-blocked                              zilnic                                    │
       │                                                                              ▼
   GitHub cloud                                                          ┌─────────────────────┐
   runners NU                                                            │   consumatori:      │
   pot fetch direct                                                      │   jurnaliști, ONG,  │
                                                                         │   dezvoltatori      │
                                                                         └─────────────────────┘
```

**Decizii cheie:**

- **Static JSON snapshot** (scraper → JSON → GitHub Pages) — cost zero, zero server, CDN global, portabilitate totală.
- **Self-hosted GitHub Actions runner** pe un PC din România — cdep.ro geo-blochează runner-ele cloud GitHub.
- **Pagefind** pentru search — index static, ~30MB, fără backend.
- **Modelele aliniate Popolo** (Person, Organization, VoteEvent) — facilitează interop cu alte API-uri parlamentare europene.

Detalii în [`STORAGE.md`](./STORAGE.md), [`INTEGRATIONS.md`](./INTEGRATIONS.md), [`sitemap.md`](./sitemap.md).

---

## Stack tehnic

- **Python 3.11+** — scraperi, modele de date
- **`requests` + `parsel`** — HTTP cu adapter SSL legacy + CSS/XPath
- **`truststore`** — încredere certificat de sistem (necesar pe Windows cu antivirus MITM)
- **`pydantic v2`** — modele de date validate, exportate ca JSON
- **GitHub Actions self-hosted** — cron zilnic + workflow manual
- **Pagefind** — index full-text static
- **GitHub Pages** — hosting static pentru JSON + UI + search

---

## Utilizare

### Python
```python
import requests

dep = requests.get(
    "https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json"
).json()

# Top 10 deputați după număr de propuneri legislative
top = sorted(dep["data"], key=lambda d: d["activitate_propuneri_legislative"], reverse=True)[:10]
for d in top:
    print(f"{d['name']:40s} {d['current_party'][:25]:25s} {d['activitate_propuneri_legislative']:3d} propuneri")
```

### JavaScript
```javascript
const res = await fetch(
  "https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json"
);
const { data } = await res.json();
console.log(data.filter(d => d.judet === "Cluj"));
```

### curl + jq
```bash
curl -sL https://endimion2k.github.io/cdep-api-poc/data/v1/voturi/2024/_index.json \
  | jq '.data | sort_by(.timestamp) | reverse | .[0:5] | .[] | {data: .timestamp, descriere, counts}'
```

---

## Instalare locală (pentru dezvoltare)

```bash
git clone https://github.com/Endimion2k/cdep-api-poc.git
cd cdep-api-poc

python -m venv .venv
.venv\Scripts\activate              # pe Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# rulează un scraper (necesită conexiune din România — cdep.ro geo-blochează)
python scripts/run_deputati.py --leg 2024 --verbose
python scripts/run_voturi.py --days 7 --leg 2024 --verbose
python scripts/run_sanctiuni.py --leg 2024 --verbose
python scripts/run_interpelari.py --year 2026 --verbose

# regenerează HTML pages + Pagefind index (după bootstrap)
python scripts/generate_html.py
npx pagefind --site pages --output-path pagefind

# servește local
python -m http.server 8000
# deschide http://localhost:8000/search.html
```

---

## Date & licență

- **Sursa datelor**: [www.cdep.ro](https://www.cdep.ro) — date publice ale Camerei Deputaților
- **Licență cod**: [Open Government License v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
- **Date colectate**: exclusiv date publice; **nu** colectăm CNP, telefon personal, adresă privată
- **GDPR**: datele parlamentarilor ca persoane publice în exercițiul mandatului sunt exceptate de la restricțiile GDPR standard. Cereri de rectificare se pot deschide ca issue.

---

## Autor

**Cătălin Popa** · inițiativă în contextul candidaturii pentru internship la Camera Deputaților, Comisia pentru Tehnologia Informației și Comunicațiilor, Ed. I/2026.

Inspirat de [bikestylish.ro](https://bikestylish.ro) — model similar de API deschis pentru industria bicicletelor din România.

---

## Roadmap

Vezi [**TIMELINE.md**](./TIMELINE.md) pentru istoricul detaliat al implementării și [**CDEP_API_Plan_Implementare.docx**](./CDEP_API_Plan_Implementare.docx) pentru analiza arhitecturală completă (17 pagini).

| Milestone | Status | Conținut |
|---|---|---|
| M0 — setup repo + CI | ✅ done | Repo, CI lint+format, GitHub Pages |
| M1 — `/deputati` | ✅ done | 335 deputați legislatura 2024, profile complete |
| M2 — `/voturi` cu defalcare nominală | ✅ done | 816 voturi 2024–2026 |
| M3 — `/sanctiuni` + `/interpelari` | ✅ done | 6 sancțiuni + 9.326 interpelări |
| M4 — search Pagefind cu filter-e | ✅ done | ~12.500 entități indexate, filter-e pe tip/partid/an/etc. |
| M5 — `/comisii` agregat | ✅ done | 37 comisii (32 permanente + 5 speciale comune) |
| M6 — `/proiecte-lege` | ✅ done | 1.641 proiecte 2024–2026, cu timeline, vot final, promulgare |
| M7 — `/amendamente`, feeds, lansare publică | 🔜 | extragere amendamente, Atom/JSON feeds, anunț extern |
