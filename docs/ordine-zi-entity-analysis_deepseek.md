# Ordine de Zi — Entity Pattern Analysis

Analysis of `data/v1/ordine-zi/legislatura-2024.json` (June 2026).

**Scope:** 123 sessions, 4,572 items total (4,307 numbered, 265 procedural/info).

## Structural Formula

Romanian parliamentary language is highly formulaic. An item like:

> *Proiectul de Lege **pentru modificarea și completarea** Legii nr.286/2009 privind Codul penal (PL-x 129/2025) - lege organică - Adoptat de Senat...*

Breaks down as:

1. **Type** — `Proiectul de Lege`
2. **Preposition + Action** — `pentru modificarea și completarea`
3. **Target act** — `Legii nr.286/2009`
4. **Subject matter** — `privind Codul penal`
5. **Registration number** — `(PL-x 129/2025)`
6. **Law category** — `lege organică`
7. **Procedural metadata** — `Adoptat de Senat`, commission reports, etc.

## Document Type Taxonomy

| First word | Count | % |
|---|---|---|
| `Proiectul` | 3,767 | 82.4% |
| `Propunerea` | 443 | 9.7% |
| `Informare` | 95 | 2.1% |
| `Reexaminarea` | 65 | 1.4% |
| `Propunere` (indefinite) | 24 | 0.5% |
| `Prezentarea` | 23 | 0.5% |
| `Dezbaterea` | 18 | 0.4% |
| `Raportul` | 16 | 0.3% |
| `Alocuțiunea` | 16 | 0.3% |
| Others | ~65 | 1.4% |

The top 4 cover ~95.6% of all items.

### Full 30-type breakdown (from `_ITEM_TYPE_PREFIXES`)

| Type | Slug |
|---|---|
| Proiectul de Lege / Proiectul Legii | `proiect_lege` |
| Proiectul de Hotărâre / Hotărare | `proiect_hotarare` |
| Propunerea / Propunere legislativă | `propunere_legislativa` |
| Reexaminarea | `reexaminare` |
| Dezbaterea moțiunii simple | `motiune_simpla` |
| Dezbaterea moțiunii de cenzură | `motiune_cenzura` |
| Informare (casete) | `informare_casete` |
| Informare | `informare` |
| Raportul | `raport` |
| Solicitarea | `solicitare` |
| Vacantarea | `vacantare` |
| Declarația Parlamentului | `declaratie` |
| Dezbateri politice | `dezbateri_politice` |
| Angajarea răspunderii | `angajare_raspundere` |
| Alocuțiunea | `alocutiune` |
| Prezentarea | `prezentare` |
| etc. | |

## Action Verbs (after `pentru`/`privind`)

| Action | ~Count | Notes |
|---|---|---|
| `aprobarea OUG nr.X/Y` | 1,110 | Most common — government emergency ordinances |
| `aprobarea OG nr.X/Y` | 532 | Government ordinances |
| `modificarea și completarea` | 680+ | Amend and supplement |
| `modificarea` (standalone) | 355+ | Amend only |
| `completarea` (standalone) | 150+ | Supplement only |
| `modificarea anexei` | 84 | Annex amendment (hotărâre pattern) |
| `reglementarea` | 110+ | Regulating measures |
| `ratificarea` | ~20 | Treaty ratification |
| `adoptarea opiniei` | ~300 | EU opinion adoption (hotărâre pattern) |

## Referenced Acts

### By act type

| Act type | Occurrences | Unique values | Top example |
|---|---|---|---|
| **Lege nr.** | 937 | 95 | Legea nr.95/2006 (72×) |
| **OUG nr.** (full form) | 375 | 30 | OUG nr.127/2023 (50×) |
| **OG nr.** | 70 | 9 | OG nr.40/2006 (14×) |
| **PL-x** (uppercase) | 3,398 | 465 | PL-x 160/2025 (56×) |
| **Pl-x** (lowercase) | 530 | 153 | Pl-x 271/2010 (24×) |
| **OUG nr.** (abbreviated) | 21 | 4 | OUG nr.153/2024 (9×) |
| Hot. Parlament | ~30 | — | `Hotărârea Parlamentului României nr.X/Y` |
| Hot. Cam. Dep. | ~50 | — | `Hotărârea Camerei Deputaților nr.X/Y` |
| Decizia CCR | ~50 | — | `Decizia Curții Constituționale nr.X` (no year) |

### Registration number formats

| Format | Example | Meaning |
|---|---|---|
| `PL-x NNN/YYYY` | PL-x 160/2025 | Proiect de Lege |
| `Pl-x NNN/YYYY` | Pl-x 271/2010 | Propunere legislativă |
| `PH CD NNN/YYYY` | PH CD 89/2025 | Proiect de Hotărâre Cam. Dep. |
| `PHCD NNN/YYYY` | PHCD 93/2025 | Same, compact form |
| `MS N/YYYY` | MS 7/2025 | Moțiune simplă |
| `MC N/YYYY` | MC 1/2026 | Moțiune de cenzură |

## Codes (Coduri) Referenced

| Code | Count |
|---|---|
| Codul administrativ | 73 |
| Codul penal | 65 |
| Codul fiscal | 47 |
| Codul de procedură penală | 41 |
| Codul de procedură civilă | 35 |
| Codul silvic | 16 |
| Codul muncii | 8 |
| Codul civil | 7 |

## Procedural Flags

| Flag | Count | Pattern |
|---|---|---|
| `camera_decizionala` | 2,332 | "Cameră decizională" |
| `procedura_urgenta` | 1,214 | "Procedură de urgență" |
| `rezerva_raport` | 268 | "Se dezbate sub rezerva..." |
| `adoptat_art115` | 219 | "condițiile articolului 115" |
| `retrimis_comisie` | 97 | "Retrimis la comisie" |
| `prioritate_legislativa` | 89 | "Prioritate legislativă" |

## Law Categories

| Category | Count | HTML pattern |
|---|---|---|
| `lege_ordinara` | 152 | `<b>lege ordinară</b>` |
| `lege_organica` | 7 | `<b>lege organică</b>` |
| Unqualified "lege" | 307 | `<b>lege</b>` |

## Chamber Mentions

| Mention | Count |
|---|---|
| Senat | 3,615 |
| Cameră decizională | 3,533 |
| Prima Cameră sesizată | 328 |

## Edge Cases & Gaps

1. **Abbreviated OUG** — `OUG nr.112/2022` (without "Ordonanța de urgență a Guvernului" expansion): 21 occurrences. Not currently captured by `referenced_acts`.

2. **Capitalized "Urgență"** — `de Urgență` variant exists; regex is case-insensitive but normalization to Ț (comma-below) is important.

3. **Dash-prefixed items** — Investiture sessions have 3 items starting with `- ` (dash-bullet). The `extract_item_type` function already strips these.

4. **Genitive/indefinite forms** — `Proiectul Legii` (genitive) and `Propunere legislativă` (indefinite) are handled by item_type prefixes.

5. **Commission-with-decision** — `Comisia juridică (Respingere)` — parenthetical decision tags within commission names. Could be split for cleaner data.

6. **Un-extracted items** — ~1,597 numbered items still have `entities: null`. These look extractable; the build script likely just needs a re-run rather than new patterns.

## Entity Coverage

- 2,910 / 4,572 items have populated `entities` (64%)
- 2,711 / 4,307 numbered items (63%)
- 199 / 265 non-numbered items (75%)

The entity extraction uses **pure regex** — no NLP/LLM. Romanian parliamentary phrasing is formulaic enough that regex-based extraction reaches high coverage with zero hallucinations.

## Existing Implementation

| File | Purpose |
|---|---|
| `schemas/ordine_zi_entities.py` | Pydantic models: `OrdineZiItemEntities`, `ReferencedAct` |
| `scrapers/entities_ordine_zi.py` | Regex extractors for all entity types |
| `scripts/build_ordine_zi_entities.py` | CLI script to enrich JSON data in-place |
| `tests/test_ordine_zi_entities.py` | 62 tests |
| `web/ordine-zi.html` | UI badges, commission chips, filter bar |
