# CDEP API — Camera Deputaților, date deschise

Un API REST public, gratuit, care expune datele parlamentare ale **Camerei Deputaților** din România în format **JSON**. Construit deasupra surselor publice de pe [cdep.ro](https://www.cdep.ro), actualizat zilnic.

> **Status**: 🟢 POC funcțional · **12 endpoint-uri live** · 9 legislaturi cu moțiuni (1992-2024) · search full-text · cron zilnic incremental

[![License: OGL v3.0](https://img.shields.io/badge/license-OGL%20v3.0-blue.svg)](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)
[![Status: POC live](https://img.shields.io/badge/status-POC%20live-green.svg)](https://endimion2k.github.io/cdep-api-poc/)
[![Docs: Swagger](https://img.shields.io/badge/docs-Swagger%20UI-green.svg)](https://endimion2k.github.io/cdep-api-poc/docs/swagger.html)

**Demo live:** https://endimion2k.github.io/cdep-api-poc/

---

## Cifre live (legislatura 2024 — în curs)

| Endpoint | Records | URL |
|---|---:|---|
| `/deputati` | **335** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json) |
| `/voturi` (cu defalcare nominală) | **~3.000** | [_index.json](https://endimion2k.github.io/cdep-api-poc/data/v1/voturi/2024/_index.json) |
| `/sanctiuni` | **6** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/sanctiuni/legislatura-2024.json) |
| `/interpelari` (2024–2026) | **9.758** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/interpelari/legislatura-2024.json) |
| `/comisii` (agregat) | **37** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/comisii/legislatura-2024.json) |
| `/proiecte` (2024–2026) | **3.252** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/proiecte/legislatura-2024.json) |
| `/amendamente` (derived) | **154+ proiecte** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/amendamente/legislatura-2024.json) |
| `/motiuni` (cross-9-legislaturi) | **162 (1992-2024)** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/motiuni/legislatura-2024.json) |
| 🆕 `/ordine-zi` | **~150 sesiuni/an** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/ordine-zi/legislatura-2024.json) |
| 🆕 `/declaratii` (avere + interese) | **332 dep × ~3 PDF-uri** | [legislatura-2024.json](https://endimion2k.github.io/cdep-api-poc/data/v1/declaratii/legislatura-2024.json) |
| 🆕 `/stenograme` | **~150 ședințe/an** | [_index.json](https://endimion2k.github.io/cdep-api-poc/data/v1/stenograme/legislatura-2024/_index.json) |
| 🆕 `/doc-comisii` (rapoarte/avize) | **85.895 docs total** | [all.json](https://endimion2k.github.io/cdep-api-poc/data/v1/doc-comisii/all.json) |
| **Legislatura 2020** | 354 dep / 3.616 vot / 8 san / 18.040 int / 54 com / 3.604 pro / 721 amend / 22 mot | — |
| **Legislatura 2016** | 361 dep / 5 san / 67 com / 3.252 pro / 25 mot + interpelări | — |
| `/feed.atom` + `/feed.json` | **ultimele 60 evenimente** | [feed.atom](https://endimion2k.github.io/cdep-api-poc/data/v1/feed.atom) · [feed.json](https://endimion2k.github.io/cdep-api-poc/data/v1/feed.json) |
| **Search full-text** | **~38.000 entități indexate** | [/search](https://endimion2k.github.io/cdep-api-poc/search.html) |

Datele se actualizează automat zilnic la 04:00 UTC. Daily cron rulează **incremental** (3-5 min) — refresh doar ce e nou. Săptămânal `--full` pentru schimbări de stadiu pe entități cunoscute.

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

### ✅ Date parlamentare (JSON)

| Endpoint | Descriere |
|---|---|
| `GET /deputati/legislatura-{leg}.json` | Profile complete (bio, partid, județ, comisii, activitate) |
| `GET /voturi/{leg}/_index.json` | Index voturi (timestamp, descriere, counts agregate) |
| `GET /voturi/{leg}/{idv}.json` | Detalii vot cu defalcare nominală (DA/NU/AB per deputat) |
| `GET /sanctiuni/legislatura-{leg}.json` | Sancțiuni disciplinare |
| `GET /interpelari/legislatura-{leg}.json` | Interpelări/întrebări parlamentare cu răspuns |
| `GET /comisii/legislatura-{leg}.json` | Comisii cu lista membrilor și conducerea |
| `GET /proiecte/legislatura-{leg}.json` | Proiecte legislative cu stadiu, timeline, voturi, promulgare |
| `GET /amendamente/legislatura-{leg}.json` | View derivat — proiecte sortate după număr amendamente |
| `GET /motiuni/legislatura-{leg}.json` | Moțiuni simple + cenzură (acoperire 1992-2024) |
| 🆕 `GET /ordine-zi/legislatura-{leg}.json` | Ordinea de zi a ședințelor plenului cu cross-link `idp` la proiecte |
| 🆕 `GET /declaratii/legislatura-{leg}.json` | Declarații de avere + interese (link-uri PDF + date depunere) |
| 🆕 `GET /stenograme/legislatura-{leg}/_index.json` | Index stenograme + `{YYYYMMDD}.json` per ședință |
| 🆕 `GET /doc-comisii/all.json` | Rapoarte, avize, sinteze, procese verbale ale comisiilor |

### ✅ Feeds & Search

| Endpoint | Descriere |
|---|---|
| `GET /feed.atom` / `/feed.json` | Atom (RFC 4287) / JSON Feed v1.1 — ultimele 60 evenimente cross-endpoint |
| `GET /search.html?q=` | Pagefind full-text peste toate datele |
| `GET /status.html` + `/data/v1/status.json` | Status page cu prospețime date |

### ✅ Pagini interactive (HTML)

| Endpoint | Descriere |
|---|---|
| `GET /deputat.html?id={cdep_idm}` | Profil deputat cu cross-link voturi/interpelări/moțiuni |
| `GET /proiect.html?idp={N}` | Profil proiect cu timeline + amendamente + vot final |
| `GET /vot.html?idv={N}` | Profil vot cu defalcare nominală + pie chart pe partide |
| `GET /motiune.html?idm={N}` | Profil moțiune cu vot final și semnatari nominali |
| `GET /sanctiune.html?id={hash}` | Detaliu sancțiune disciplinară |
| Toate paginile au toggle limbă RO/EN | i18n cu ~110 chei traduse, fade transition |

### 🔜 Propuse (în lucru sau viitor)

| Endpoint | Status |
|---|---|
| Stenograme — parsare intervenții individuale | WIP — extragem text complet, intervenții = TODO |
| Declarații istorice (2020, 2016, 2012) | viitor — schimă identică, doar bootstrap |
| Texte complete amendamente (PDF parsing) | viitor |

Vezi [`api/openapi.yaml`](./api/openapi.yaml) pentru schema completă.

### 💡 Cross-link între endpointuri

Datele sunt **interconectate** prin ID-uri stabile:

- `cdep_idm` (deputat) leagă: `/deputati` ↔ `/voturi/.../votes[]` ↔ `/interpelari/...adresant_canonical_id` ↔ `/motiuni/...semnatari[]` ↔ `/declaratii/...cdep_idm`
- `cdep_idv` (vot) leagă: `/voturi/_index` ↔ `/voturi/{idv}.json` ↔ `/proiecte/...vot_final`
- `cdep_idp` (proiect) leagă: `/proiecte/...` ↔ `/amendamente/...` ↔ `/ordine-zi/.../items[].idp` ↔ `/doc-comisii/.../idp` ↔ `/feed.atom`
- `cdep_idi` (interpelare) leagă: `/interpelari/...` ↔ `/deputati/...activitate_intrebari_interpelari`
- `cdep_idm` (moțiune) leagă: `/motiuni/...` ↔ `/deputati/...moțiuni semnate`

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

### Recipes pentru noile endpointuri

**1. Ce votează plenul săptămâna asta?** (ordine-zi)
```python
oz = requests.get("https://endimion2k.github.io/cdep-api-poc/data/v1/ordine-zi/legislatura-2024.json").json()
proiecte = requests.get("https://endimion2k.github.io/cdep-api-poc/data/v1/proiecte/legislatura-2024.json").json()
proi_by_idp = {p["cdep_idp"]: p for p in proiecte["data"]}

for sesiune in oz["data"][:1]:  # cea mai recentă
    print(f"Ședința {sesiune['session_date']}: {sesiune['titlu']}")
    for item in sesiune["items"]:
        if item["idp"]:
            proi = proi_by_idp.get(item["idp"])
            print(f"  PCT{item['pozitie']}: {item['nr_inregistrare']} — stadiu: {proi['stadiu'] if proi else '?'}")
```

**2. Toate declarațiile de avere ale unui partid** (declaratii)
```python
decl = requests.get("https://endimion2k.github.io/cdep-api-poc/data/v1/declaratii/legislatura-2024.json").json()
psd = [d for d in decl["data"] if d["partid_short"] == "PSD"]
for d in psd[:10]:
    pdf_avere = d["avere"][-1]["url"] if d["avere"] else None
    print(f"{d['deputat_nume']:35s} → {pdf_avere}")
```

**3. Rapoarte emise de comisia Buget în 2026** (doc-comisii)
```python
docs = requests.get("https://endimion2k.github.io/cdep-api-poc/data/v1/doc-comisii/all.json").json()
rapoarte_buget = [
    d for d in docs["data"]
    if d["tip"] == "raport" and any(c["nume"] == "Buget" for c in d["comisii"])
    and d["data"] and d["data"].startswith("2026")
]
for d in rapoarte_buget[:5]:
    print(f"{d['data']} — {d['nr_proiect']} → {d['pdf_url']}")
```

**4. Toate moțiunile de cenzură din istoria parlamentară** (motiuni cross-leg)
```python
toate_motiunile = []
for leg in [2024, 2020, 2016, 2012, 2008, 2004, 2000, 1996, 1992]:
    m = requests.get(f"https://endimion2k.github.io/cdep-api-poc/data/v1/motiuni/legislatura-{leg}.json").json()
    cenzura = [x for x in m["data"] if x["tip"] == "cenzura"]
    toate_motiunile.extend(cenzura)
print(f"Total moțiuni de cenzură 1992-2024: {len(toate_motiunile)}")
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

**Cătălin Popa** · dezvoltat în colaborare cu **Comisia pentru Tehnologia Informației și Comunicațiilor** a Camerei Deputaților pentru transparentizarea activității parlamentare și consolidarea accesului public la datele guvernamentale deschise.

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
| M7 — `/amendamente` (derivat) | ✅ done | 154 proiecte cu 1.820 amendamente trackate, slim view sortat |
| M8 — feeds + motions | ✅ done | Atom/JSON feeds, /motiuni cu vot și semnatari |
| M9 — bootstrap legislatura 2020 | ✅ done | 354 dep / 3.616 vot / 18.040 int / 3.604 pro / 22 mot |
| M10 — profil deputat dedicat | ✅ done | `/deputat.html?id=N` cu cross-link-uri |
| M11 — i18n RO/EN + bootstrap leg 2016 | ✅ done | Toggle limbă pe toate paginile + leg 2016 (361 dep, 25 mot, 3.252 pro) |
| M12 — arhivă istorică moțiuni 1992-2024 | ✅ done | 162 moțiuni cross-9-legislaturi, cu auto-distribute corect |
| M13 — migrare cdep.ro → ORDS (`/ords/pls/`) | ✅ done | URL prefix nou + parser rescris pentru schema HTML nouă |
| M14 — incremental complet (toate endpointurile) | ✅ done | Daily cron 3-5 min, săptămânal `--full` pentru schimbări stadiu |
| M15 — 4 endpointuri noi | ✅ done | `/ordine-zi`, `/declaratii`, `/stenograme`, `/doc-comisii` |
| M16 — lansare publică | 🔜 | 2-page brief, screen recording, outreach jurnaliști |
