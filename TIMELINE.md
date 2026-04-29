# TIMELINE — CDEP API

> Acest document descrie atât **planul inițial** (24 săptămâni, 6 faze, ~240h) cât și **implementarea reală** care a comprimat aceste 6 milestone-uri într-un sprint intensiv POC.
> Arhitectură aleasă: **A — Static snapshot** (scraper → JSON → GitHub Pages). Motivație: cost zero, zero server, prim livrabil rapid, portabilitate totală.

---

## Implementare efectivă — POC v0.1 (sprint accelerat)

Cele 6 milestone-uri planificate pe 24 săptămâni au fost livrate într-un sprint intensiv. Mai jos, ordinea cronologică reală.

### Faza 0 — Setup & Discovery ✅

- [x] Audit cdep.ro — cele 13 secțiuni mapate în [`sitemap.md`](./sitemap.md): URL patterns pentru deputați, voturi, proiecte, comisii, interpelări, sancțiuni, stenograme.
- [x] Stack ales și setup: Python 3.11+, `requests` + `parsel`, `pydantic v2`, `pdfplumber`, `truststore` (pentru SSL legacy cdep.ro).
- [x] Studiu Popolo + decizie subset (Person, Organization, VoteEvent, Vote) — documentat în [`INTEGRATIONS.md`](./INTEGRATIONS.md).
- [x] Structură repo: `/scrapers`, `/schemas`, `/scripts`, `/data/v1`, `/api`, `/tests`, `/pages`.
- [x] **Self-hosted GitHub Actions runner** pe PC Windows din România — cdep.ro geo-blochează runner-ele cloud GitHub.
- [x] Workflow `scrape.yml` cu cron zilnic 04:00 UTC și `ci.yml` lint/format/typecheck.
- [x] `ruff` + `pyproject.toml` cu reguli stricte.

### Faza 1 — `/deputati` ✅ — **335 records**

- [x] Scraper listă deputați (legislatura 2024) folosind `structura2015.de` (single-page, 354 deputați complete).
- [x] Scraper profil individual — bio, partid, județ, circumscripție, comisii, contoare activitate.
- [x] Extindere la legislaturile 2016 + 2020.
- [x] `canonical_id` derivat din hash stabil (numele se schimbă între legislaturi, partidele se schimbă).
- [x] Paralelizare cu `ThreadPoolExecutor` (`MAX_WORKERS` env).
- [x] Fix critical: SSL legacy adapter pentru SHA1 ciphers + `truststore.inject_into_ssl()` pentru certificate antivirus MITM.
- [x] Endpoint live: [`/data/v1/deputati/legislatura-2024.json`](https://endimion2k.github.io/cdep-api-poc/data/v1/deputati/legislatura-2024.json)

### Faza 2 — `/voturi` cu defalcare nominală ✅ — **816 records**

- [x] Discovery URL pattern: `evot2015.xml?par1=1&par2=YYYYMMDD` (date structurate per zi).
- [x] Scraper iterează weekday-uri în interval, fetch XML, apoi `evot2015.nominal?idv=N` pentru defalcare.
- [x] Parsare cu `xml.etree.ElementTree` — cdep.ro folosește ISO-8859-2 encoding (gestionat automat).
- [x] Storage incremental: `_index.json` + `{idv}.json` per vot (155MB total).
- [x] Validare: `prezenti = pentru + contra + abtineri + nu_au_votat`.
- [x] Endpoint live: 816 voturi 2024–2026 cu defalcare nominală individuală.

### Faza 3 — `/sanctiuni` + `/interpelari` ✅ — **6 + 9.326 records**

- [x] **Sancțiuni**: scraper pentru `sanctiuni_parlam.lista_sanctionati`. Parsare div-uri `grup-parlamentar-list` cu split pe `<hr>`. Taxonomie: DIMINUARE_INDEMNIZATIE, AVERTISMENT_SCRIS, CHEMARE_ORDINE, RETRAGERE_CUVANT, OTHER.
- [x] Fix Unicode: regex acceptă atât `ţ` (U+0163) cât și `ț` (U+021B) pentru diminuare indemnizație.
- [x] **Interpelări**: scraper pentru `interpelari2015.lista` + `interpelari2015.detalii`. Bootstrap pentru 2024 + 2025 + 2026 (9.326 entries totale, 86.4% cu răspuns primit).
- [x] Cross-link cu deputați via `adresant_canonical_id`.

### Faza 4 — Search Pagefind cu filter-e ✅ — **~12.500 entități indexate**

- [x] Builder `scripts/generate_html.py` produce ~12.500 pagini HTML statice cu `data-pagefind-body` și `data-pagefind-meta`.
- [x] Pagefind index built ca pas final în CI (`npx pagefind --site pages`).
- [x] Pagina `search.html` cu PagefindUI: traduceri în RO, filter pills, fallback elegant.
- [x] Filtre faceted: `tip` (deputat/vot/sancțiune/interpelare/comisie/proiect), `partid`, `județ`, `legislatura`, `an`, `rezultat`, `răspuns`, etc.
- [x] Normalizare adresant_grup (curățare valori murdare ca "AUR Destinatar:" → "AUR").

### Faza 5 — `/comisii` ✅ — **37 records**

- [x] Insight: datele despre comisii sunt deja nested în `/deputati` — nu e nevoie de scraper nou.
- [x] Builder `scripts/build_comisii.py` agregă din profile → `/comisii/legislatura-{leg}.json`.
- [x] Normalizare nume: strip variante temporale ("(din feb. 2025)", "(până în sep. 2025)") → 37 comisii unice (32 permanente + 5 speciale comune).
- [x] Schema: Comisie cu președinte, vicepreședinți, secretari + lista membrilor cu rol și partid.

### Faza 6 — `/proiecte-lege` ✅ — **1.641 records**

- [x] Discovery prin WebFetch: URL-uri `upl_pck2015.lista?anp=YYYY` și `upl_pck2015.proiect?cam=2&idp=N`.
- [x] Schema completă: înregistrări (BPI, Camera Deputaților, Senat, Guvern), titlu, tip, caracter, procedura urgență, inițiator, cameră decizională, stadiu, lege_nr, decret_nr, vot final, timeline procedural complet.
- [x] Parser cu CSS/XPath: `<td bgcolor="fff0d8">label</td><td>value</td>` pattern + lookup case+diacritics-insensitive.
- [x] Bootstrap 2024 + 2025 + 2026: 1.641 proiecte parsed 100% cu success.
- [x] Calitate date: 100% titlu, inițiator, cameră decizională, timeline. 23.1% promulgate ca lege.

### Faza 7 — Polish & landing ✅

- [x] Landing page `index.html` cu date reale (335 / 816 / 1641 / 9326 / 37 / 6) — fetch live din JSON.
- [x] Demo interactiv: top deputați alfabetic + ultimele 6 voturi + distribuție partide reale (PSD 86 / AUR 61 / PNL 50 / USR 40 / UDMR 22 / etc.).
- [x] Indicatori activitate: % deputați cu lege promulgată, % cu interpelări, % proiecte promulgate, % proiecte inițiate de Guvern.
- [x] OpenAPI spec rescris să reflecte cele 6 endpoint-uri implementate + 19 schemas (Deputat, VoteEvent, VoteIndividual, Sanctiune, Interpelare, Comisie, Proiect, TimelineEvent, etc.).
- [x] Swagger UI live cu spec corect.
- [x] README cu cifrele live + arhitectura reală + exemple Python/JS/curl.

---

## Status la zi: 6 endpoint-uri live, ~12.500 entități, search funcțional

| Endpoint | Records | Format |
|---|---:|---|
| `/deputati/legislatura-{leg}.json` | 335 | JSON Pydantic |
| `/voturi/{leg}/_index.json` + `{idv}.json` | 816 | JSON cu defalcare nominală |
| `/sanctiuni/legislatura-{leg}.json` | 6 | JSON |
| `/interpelari/legislatura-{leg}.json` | 9.326 | JSON cu răspuns tracking |
| `/comisii/legislatura-{leg}.json` | 37 | JSON agregat |
| `/proiecte/legislatura-{leg}.json` | 1.641 | JSON cu timeline complet |
| `/search.html` | ~12.500 entități | Pagefind + filter-e faceted |

**CI**: lint/format pe fiecare push (ruff). **Cron**: zilnic 04:00 UTC pe self-hosted runner Windows. **Hosting**: GitHub Pages, cost zero.

---

## Plan inițial (păstrat ca referință) — 24 săptămâni / ~240h

> Plan concret pentru trecerea de la Proof-of-Concept la API public funcțional.
> Buget de timp: **~10 ore / săptămână** (~240h total) · Durată: **24 săptămâni** (~6 luni)

Bifează task-urile pe măsură ce le închei. GitHub redă automat `- [ ]` ca checkbox interactiv în README/Issues/PR-uri.

---

## Overview — 6 faze, 6 milestone-uri

| Fază | Perioadă | Ore | Milestone livrat |
|---|---|---|---|
| 0 · Setup & Discovery | S1–S2 | ~20h | M0 · CI activ, primul push automat |
| 1 · Deputați + Prezență | S3–S6 | ~40h | M1 · `/deputati` live cu date reale |
| 2 · Voturi (plen + individuale) | S7–S11 | ~50h | M2 · `/voturi` live — cel mai valoros endpoint |
| 3 · Proiecte legislative + amendamente | S12–S15 | ~40h | M3 · `/proiecte-lege` + `/amendamente` live |
| 4 · Comisii, grupuri, Birou Permanent | S16–S19 | ~40h | M4 · peisaj organizatoric complet |
| 5 · Extensii accountability (interpelări, moțiuni, sancțiuni, search) | S20–S22 | ~32h | M5 · endpoint-uri suplimentare live |
| 6 · Polish, documentație, lansare | S23–S24 | ~20h | M6 · v1.0 anunțat public |

---

## Faza 0 — Setup & Discovery (S1–S2, ~20h)

Obiectiv: infrastructura e solidă (repo, CI, structură, contract de date) și toate secțiunile cdep.ro sunt mapate.

- [ ] Audit complet cdep.ro — listez toate URL-urile-rădăcină relevante (deputați, voturi, proiecte, comisii, interpelări, moțiuni, stenograme). Salvez inventarul ca `sitemap.md`.
- [ ] Decid stack-ul: **Python 3.11+** · `requests` + `parsel` (CSS/XPath) · `pydantic v2` · `pdfplumber` pentru PDF.
- [ ] Studiu [Popolo spec](https://www.popoloproject.com/) (~2h); decid subsetul adoptat (`Person`, `Organization`, `Membership`, `Motion`, `VoteEvent`); documentez mapping câmp-cu-câmp în [`INTEGRATIONS.md`](./INTEGRATIONS.md).
- [ ] Structură repo: `/scrapers`, `/schemas` (Pydantic aliniat la Popolo = sursă de adevăr), `/data` (output JSON), `/api` (docs + swagger), `/scripts`, `/tests`.
- [ ] Migrez `api/openapi.yaml` la format generat automat din schemele Pydantic, ca să rămână sincronizat.
- [ ] Setup GitHub Actions: workflow `manual` (debug) + `cron` zilnic (06:00 Europe/Bucharest) care rulează scraperul și face commit automat.
- [ ] Setup lint/format: `ruff`, `mypy --strict`, `pre-commit`.
- [ ] Setup teste: `pytest` + `syrupy` (snapshot testing pe output-urile scraperului).
- [ ] Scriu `CONTRIBUTING.md` și `CODE_OF_CONDUCT.md`.

🏁 **M0** — primul push automat de date pe repo (chiar dacă cu un singur endpoint stub); CI verde.

---

## Faza 1 — Deputați + Prezență (S3–S6, ~40h)

Obiectiv: primul endpoint real, end-to-end. Baza pentru restul (toate celelalte endpoint-uri fac referire la `deputat_id`).

- [ ] Scraper listă deputați (legislatura curentă).
- [ ] Scraper profil individual: bio, mandat, partid, județ, circumscripție, comisii, contact.
- [ ] Scraper statistici prezență (plen + comisii, pe ani, absențe motivate vs nemotivate).
- [ ] Extindere la ultimele 3 legislaturi — verific stabilitatea URL-urilor istorice.
- [ ] Normalizare diacritice + ID canonic (ID cdep se schimbă între legislaturi → introduc `canonical_id` derivat din hash stabil).
- [ ] Teste de regresie: min. 20 de profile cu captură HTML salvată; alertă în CI dacă structura se schimbă.
- [ ] Publicare JSON în `/data/v1/deputati/` (fișier per legislatură + fișier agregat).
- [ ] Actualizare Swagger UI cu exemple reale (nu mock).
- [ ] README update + post de vizibilitate: „Primul endpoint live”.

🏁 **M1** — `/deputati`, `/deputati/{id}`, `/deputati/{id}/prezenta` live cu date reale.

---

## Faza 2 — Voturi (S7–S11, ~50h)

Obiectiv: cel mai valoros endpoint; și cel mai dificil (mix HTML + PDF + variații istorice).

- [ ] Scraper index ședințe plen (per sesiune, per an).
- [ ] Scraper vot nominal per ședință: tabele HTML unde există, fallback PDF (`pdfplumber`).
- [ ] Handling PDF scanate: dacă >5% inaccesibile → OCR `tesseract` cu flag `needs_review`.
- [ ] Mapare vot → `deputat_canonical_id` → **partid-la-data-votului** (deputații își schimbă partidele).
- [ ] Validare totaluri: `for + impotrivă + abțineri + absenți = total deputați`. Test care blochează commit dacă se rupe.
- [ ] Paginare per-an (`voturi-2026.json` etc.) pentru fișiere sub ~5MB.
- [ ] Endpoint `/voturi/{id}` cu lista individuală (un fișier per vot).
- [ ] Documentez în Swagger cazurile edge: voturi anulate, reluate, secrete.
- [ ] Cross-validare manuală: 10 voturi random verificate contra cdep.ro.

🏁 **M2** — `/voturi` și `/voturi/{id}` live; post public demo („vezi toate voturile deputatului X din 2026”).

---

## Faza 3 — Proiecte legislative + amendamente (S12–S15, ~40h)

- [ ] Scraper listă proiecte din toate stadiile (inițiat, comisie, dezbatere, adoptat, respins, retras).
- [ ] Scraper detaliu proiect: traseu complet, data fiecărei etape, comisie sesizată, inițiator, co-inițiatori.
- [ ] Scraper amendamente: autor, text, soartă (admis/respins/retras).
- [ ] Legătura amendament → vot (când a fost supus la vot).
- [ ] Endpoint `/proiecte-lege/{id}/amendamente`.
- [ ] Cross-referință: fiecare inițiator apare în `/deputati`.
- [ ] Filtrare pe stadiu și keyword (client-side pe JSON paginate).

🏁 **M3** — `/proiecte-lege`, `/proiecte-lege/{id}`, `/proiecte-lege/{id}/amendamente` live.

---

## Faza 4 — Comisii, grupuri, Birou Permanent (S16–S19, ~40h)

- [ ] Scraper listă comisii (permanente, speciale, comune).
- [ ] Scraper componență comisie + președinte, vicepreședinți, secretari.
- [ ] Scraper activitate comisie: ședințe, rapoarte, avize emise.
- [ ] Scraper grupuri parlamentare: componență, lideri, purtători de cuvânt.
- [ ] Scraper Birou Permanent: componență, decizii publice.
- [ ] Enrichment pe `/deputati/{id}`: comisii + grup curent.
- [ ] Endpoint-uri `/comisii`, `/comisii/{slug}/activitate`, `/grupuri-parlamentare`, `/birou-permanent`.

🏁 **M4** — peisajul organizatoric al Camerei expus în JSON.

---

## Faza 5 — Extensii accountability (S20–S22, ~32h)

- [ ] Scraper interpelări (listă + detaliu: subiect, destinatar, răspuns primit sau nu).
- [ ] Scraper întrebări scrise (flux separat).
- [ ] Scraper moțiuni (simple + de cenzură), cu semnatari și rezultat vot.
- [ ] Scraper declarații politice din plen.
- [ ] Scraper sancțiuni deputați (`sanctiuni_parlam.lista_sanctionati?leg=YYYY&cam=2`): tip sancțiune, data, deputat afectat, motivație. Endpoint `/sanctiuni`. Descoperit în sitemap, valoare mare pentru jurnalism.
- [ ] Integrare [Pagefind](https://pagefind.app) în build pipeline: `pagefind --site data/v1 --output-path data/v1/_pagefind` ca pas final în GitHub Actions; `<PagefindUI />` în landing page. Efort redus de la ~6h la ~2h față de indexul invertit manual. Vezi [`INTEGRATIONS.md`](./INTEGRATIONS.md) §2.
- [ ] Endpoint `/search?q=&tip=` (deputat, vot, proiect, interpelare).
- [ ] Feed-uri `/feed.atom` și `/feed.json` — ultimele 100 de evenimente (vot nou, proiect schimbat stadiu, răspuns la interpelare).

🏁 **M5** — toate extensiile live; `/search` funcțional pentru uz jurnalistic.

---

## Faza 6 — Polish, documentație, lansare (S23–S24, ~20h)

- [ ] Landing page rescrisă — cazuri concrete: „Ești jurnalist? Iată cum afli toate voturile deputatului din circumscripția ta.”
- [ ] Ghiduri în 3 limbaje: Python (`requests`), JavaScript (`fetch`), `curl`. Exemple complete.
- [ ] Status page static (ultimul scrape reușit + timestamps per resursă, din metadata commit-urilor).
- [ ] Monitorizare CI: email automat dacă scraperul pică 2 zile la rând.
- [ ] Pachet prezentare Camera Deputaților: 2 pagini + screen recording 2 min + link demo.
- [ ] Release tag `v1.0` + `CHANGELOG.md` complet.
- [ ] Anunț public: LinkedIn (RO), eventual Hacker News, outreach direct către 3 jurnaliști.

🏁 **M6** — v1.0 lansat public; proiectul are vizibilitate dincolo de cercul imediat.

---

## Primii 7 zile — acțiune imediată

- [ ] **Ziua 1 (2h)** · setup mediu local: Python 3.11, venv, git; creez branch `dev`.
- [ ] **Ziua 2 (2h)** · parcurg cdep.ro manual 45 min; notez secțiunile + URL-urile în `sitemap.md`.
- [ ] **Ziua 3 (1.5h)** · schelet scraper pentru `/deputati` (doar listă, fără profil încă).
- [ ] **Ziua 4 (1.5h)** · rulez scraperul local, salvez JSON în `/data/v1/deputati/legislatura-curenta.json`; commit pe `dev`.
- [ ] **Ziua 5 (1h)** · configurez GitHub Actions (workflow manual) care rulează scraperul end-to-end.
- [ ] **Ziua 6 (1h)** · merge `dev` → `main`; activez GitHub Pages pe `/data`; verific că JSON-ul e accesibil public.
- [ ] **Ziua 7 (1h)** · update README cu statusul nou și link către JSON real; partajez pe LinkedIn.

---

## Registru de riscuri (scurt)

| Risc | Prob. | Impact | Mitigare |
|---|---|---|---|
| cdep.ro schimbă HTML-ul | Mare | Mediu | Snapshot tests; alertă CI; buffer ~10% timeline |
| Rate limiting / blocare IP | Mic-Med | Mare | Throttling 1 req/s; User-Agent cu email contact |
| PDF-uri scanate ilizibile | Mare | Mediu | Fallback OCR; flag `needs_review`; documentare |
| Date inconsistente (ID-uri, diacritice) | Mare | Mic | Layer normalizare + `canonical_id` |
| GDPR / reuse date | Mic | Mare | Doar date publice; licență OGL v3.0; fără CNP/telefon |
| Scope creep | Mare | Mediu | Roadmap blocat 6 luni; ideile noi → `BACKLOG.md` |
| Bus factor 1 | Mare | Mare | Open-source; docs onboarding; invitare contributori după M2 |
| GitHub Actions tier depășit | Mic | Mic | Scraping incremental; buffer ~5 EUR/lună |
| Cerere de blocare din partea Camerei | Mic | Mare | Comunicare proactivă; doar date publice; poziție „complementar, nu concurent” |

---

## KPI la M6

**Tehnic** — Uptime ≥99% · Freshness ≤24h · Scraper success rate ≥95% · Coverage 100% pe sitemap · Test coverage ≥70%.
**Adopție** — ≥50 stele GitHub · ≥3 proiecte externe consumatoare · ≥1 citare în presă · ≥500 req/zi · ≥5 issues externe.
**Organizațional** — Recunoaștere din Comisia IT CDEP · ≥1 co-maintainer activ · onboarding nou contributor <2h.

---

*Ultimă actualizare: 2026-04-29 · versiune POC: v0.1.0 · 6 endpoint-uri live*
