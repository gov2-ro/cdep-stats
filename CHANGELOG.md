# Changelog

Toate modificările notabile ale proiectului sunt documentate aici. Format bazat pe [Keep a Changelog](https://keepachangelog.com/) și [SemVer](https://semver.org/).

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
