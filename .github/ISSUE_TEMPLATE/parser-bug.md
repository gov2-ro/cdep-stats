---
name: Bug parser (cdep.ro a schimbat HTML)
about: Un parser nu mai extrage corect un câmp
title: "[parser] "
labels: parser-bug
---

## Endpoint afectat

ex. `scrapers/proiecte.py`, `scripts/run_motiuni.py`

## Câmp problematic

Care câmp lipsește sau e greșit după scrape (ex. `titlu`, `data_promulgare`, `vot_pentru`).

## URL cdep.ro de unde am observat

https://www.cdep.ro/...

## Output current vs expected

```json
// Actual (după parser)
{"titlu": null, ...}

// Expected (din pagina cdep.ro)
{"titlu": "Proiect de Lege ...", ...}
```

## Sugestie de fix (opțional)

Dacă ai identificat regex-ul sau selector-ul rupt, menționează-l aici.
