# Changelog

Toate modificările notabile ale proiectului sunt documentate aici. Format bazat pe [Keep a Changelog](https://keepachangelog.com/) și [SemVer](https://semver.org/).

## [v0.2.4] — 2026-04-30 — Complete profile pages + legal docs

### Adăugat

- **`/motiune.html?idm={N}`** — pagină profil moțiune cu vot final, rezultat (adoptată/respinsă/retrasă), listă semnatari nominali cu link-uri către search.
- **`/sanctiune.html?id={hash}`** — pagină detaliu sancțiune disciplinară (cu listă completă pe legislatură când lipsește id-ul).
- **`DATA_LICENSE.md`** — clarificare juridică completă: Legea 544/2001 (acces informații publice), GDPR (deputați ca persoane publice), licență OGL v3.0, atribuire recomandată, drept de rectificare prin issue templates.

### Total v0.2.4

8 endpoints + 2 feeds + **6 pagini interactive** (search, deputat, proiect, vot, motiune, sanctiune, status) · 42 tests · documentație juridică completă.

---

## [v0.2.3] — 2026-04-30 — Profile pages + reliability improvements

### Adăugat

- **Status page** (`/status.html` + `/data/v1/status.json`) — health check pentru API: prospețime date, distribuție pe endpoint-uri, mărime fișiere, scraper versions. Util pentru jurnaliști care vor să verifice că datele sunt actualizate.
- **Split fișiere mari pe an** — `/data/v1/interpelari/legislatura-{leg}/{year}.json` și aceleași pentru `proiecte`. Reducere transfer pe mobil de la 21MB la ~3MB/an. Backward compat: fișierele monolitice rămân.
- **`/proiect.html?idp={N}`** — pagină profil proiect legislativ cu timeline procedural, vot final, amendamente, link-uri PDF.
- **`/vot.html?idv={N}`** — pagină profil vot cu defalcare nominală vizualizată: 2 pie charts (overall + per partid), tabel sortabil cu filtre.
- **Snapshot tests pentru toate parserele** (`tests/test_snapshot_parsers.py`) — fixture-uri HTML salvate în `tests/fixtures/`, prind regresii dacă cdep.ro schimbă HTML-ul.
- **CONTRIBUTING.md + issue templates** (data correction, parser bug) — onboarding contributors externi.

### Total v0.2.3

**~38.000 entități** indexate · **8 endpoints JSON** + 2 feeds + **4 pagini interactive** (search, deputat, proiect, vot) + status page · **42 tests** · CI verde · cron zilnic activ.

---

## [v0.2.0] — 2026-04-30 — Multi-legislatură + endpoint-uri suplimentare

### Adăugat

- **Bootstrap legislatura 2020** completă: 354 deputați, 3.616 voturi (cu defalcare nominală), 8 sancțiuni, 18.040 interpelări, 54 comisii, 3.604 proiecte legislative, 721 proiecte cu amendamente (10.063 admise + 413 respinse).
- `/motiuni/legislatura-{leg}.json` — moțiuni simple și de cenzură cu vot final, rezultat (adoptată/respinsă/retrasă), semnatari nominali. Titlul extras din heading HTML, nu din label inexistent.
- `/deputat.html?id={cdep_idm}` — pagină profil deputat user-facing cu foto, partid, județ, contoare activitate, comisii cu rol, cross-link-uri către interpelări adresate și moțiuni semnate.
- Brand update: proiectul e prezentat ca dezvoltat în colaborare cu Comisia pentru Tehnologia Informației și Comunicațiilor (înlocuit textul „candidatura pentru internship" peste tot — README, OpenAPI, index.html, STORAGE.md).

### Total v0.2.0

**~38.000 entități** indexate cross-2-legislaturi · **8 endpoints JSON** + 2 feeds (Atom/JSON) + 2 pagini interactive (search, deputat) · **36 tests** · CI verde · cron zilnic activ.

---

## [v0.1.0] — 2026-04-29 — POC complet

Prima versiune funcțională a API-ului. 7 endpoint-uri live cu date reale, search full-text peste tot corpus-ul, infrastructură CI/CD cu auto-update zilnic.

### Adăugat

**Endpoint-uri**

- `/deputati/legislatura-{leg}.json` — 335 deputați legislatura 2024 cu profile complete (bio, partid, județ, comisii, contoare activitate). Suport și pentru legislaturile 2016 și 2020.
- `/voturi/{leg}/_index.json` + `/voturi/{leg}/{idv}.json` — 816 voturi cu defalcare nominală (DA/NU/abținere/nu au votat per deputat). Acoperire 2024–2026.
- `/sanctiuni/legislatura-{leg}.json` — sancțiuni disciplinare (diminuare indemnizație, avertisment scris, chemare la ordine, retragere cuvânt).
- `/interpelari/legislatura-{leg}.json` — 9.326 interpelări/întrebări parlamentare 2024–2026, cu tracking răspuns (86.4% rate de răspuns).
- `/comisii/legislatura-{leg}.json` — 37 comisii (32 permanente + 5 speciale comune) cu lista completă a membrilor și conducerea.
- `/proiecte/legislatura-{leg}.json` — 1.641 proiecte legislative 2024–2026 cu stadiu, inițiator, cameră decizională, timeline procedural complet, vot final, decret promulgare, **metadate amendamente** (admise/respinse, termen depunere, link PDF raport comisie).
- `/amendamente/legislatura-{leg}.json` — view derivat: 154 proiecte cu cele mai multe amendamente (1.669 admise + 151 respinse = 1.820 trackate), sortate descrescător. Util pentru identificarea celor mai disputate proiecte legislative.
- `/feed.atom` — Atom feed (RFC 4287) cu ultimele 50 evenimente cross-endpoint (voturi, proiecte, interpelări, sancțiuni). Auto-discovery prin `<link rel="alternate">` în landing page.
- `/feed.json` — JSON Feed v1.1 (https://jsonfeed.org/version/1.1/) cu aceleași evenimente.
- `/search.html` — căutare full-text peste ~12.500 entități, cu filter-e faceted (tip, partid, județ, an, stadiu, etc.).

**Infrastructură**

- Self-hosted GitHub Actions runner pe PC Windows din România (cdep.ro geo-blochează runner-ele cloud).
- Workflow `scrape.yml` cu cron zilnic 04:00 UTC: deputați → sancțiuni → voturi → interpelări → proiecte → comisii → HTML pages → Pagefind index → validare → commit.
- Workflow `ci.yml` pentru lint/format pe fiecare push (ruff strict).
- HTTP client cu adapter SSL legacy pentru SHA1 ciphers + truststore.inject_into_ssl() pentru certificate antivirus MITM.

**Modele de date**

- Schemele Pydantic v2 aliniate Popolo: `Deputat` (Person), `Comisie` (Organization), `VoteEvent`, `VoteIndividual`.
- 19 scheme totale documentate în `api/openapi.yaml` (OpenAPI 3.0.3).

**Documentație**

- `README.md` cu cifre live, arhitectură, exemple Python/JS/curl.
- `TIMELINE.md` cu istoric implementare + plan inițial 24 săptămâni.
- `STORAGE.md` (strategia de stocare static JSON cu plan de migrare).
- `INTEGRATIONS.md` (Popolo + Pagefind decision rationale).
- `sitemap.md` (inventarul URL patterns cdep.ro).
- Swagger UI live la `/docs/swagger.html`.
- Landing page interactivă cu demo + statistici live calculate din JSON-uri.

### Note tehnice

- Encoding: cdep.ro returnează ISO-8859-2 pentru voturi XML; gestionat automat de `requests` din declarația HTTP.
- Diacritice: cdep.ro folosește mix de `ţ` (U+0163) și `ț` (U+021B) — toate regex-urile sunt diacritics-insensitive.
- Storage: ~25MB total date JSON (interpelări 10.7MB + voturi 2.3MB index + 800 fișiere individuale ~150MB + proiecte 6.2MB + restul).
- Pagefind index: ~30MB pentru ~12.500 pagini.

### Securitate & licență

- Date publice exclusiv (cdep.ro). Nu se colectează CNP, telefon personal, adresă privată.
- Licență cod: Open Government License v3.0.

[v0.1.0]: https://github.com/Endimion2k/cdep-api-poc/releases/tag/v0.1.0
