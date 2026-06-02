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

---

## N-Gram Analysis (Deterministic NLP Approach)

### Method

Pure Python n-gram extraction with:
- Romanian-aware tokenizer (handles diacritics, camelCase boundaries)
- Context-specific stopword list (~120 words: function words + parliamentary boilerplate)
- Bigram, trigram, and 4-gram frequency analysis

### Top Bigrams

| Count | Bigram | Existing coverage |
|---|---|---|
| 3,276 | `proiectul lege` | ✓ item_type |
| 2,985 | `lege ordinară` | ✓ law_category |
| 2,811 | `adoptat senat` | ✓ senate_adoption_date |
| 2,608 | `urgență guvernului` | ✓ act references |
| 2,423 | `comun comisia` | ✓ commissions |
| 2,253 | `ordonanței urgență` | ✓ act references |
| 2,128 | `cameră decizională` | ✓ flags |
| 2,108 | `aprobarea ordonanței` | ✓ action |
| 1,906 | `modificarea completarea` | ✓ action |
| 1,444 | `senat [year]raport` | ⚠️ date captured, sequence lost |
| 614 | `teza iii-a` | ⚠️ not captured |
| 606 | `constituția româniei` | ⚠️ not captured |
| 598 | `româniei republicată` | ⚠️ not captured |

### Top Trigrams

| Count | Trigram | Existing coverage |
|---|---|---|
| 2,579 | `lege ordinară adoptat` | ✓ (across fields) |
| 2,422 | `ordinară adoptat senat` | ✓ |
| 2,233 | `ordonanței urgență guvernului` | ✓ |
| 2,095 | `proiectul lege aprobarea` | ✓ |
| 1,822 | `urgență cameră decizională` | ✓ |
| 614 | `teza iii-a constituția` | ⚠️ **not captured** |
| 598 | `constituția româniei republicată` | ⚠️ **not captured** |
| 451 | `sub rezerva depunerii` | ✓ flag, ⚠️ structure lost |
| 451 | `rezerva depunerii raportului` | ✓ flag, ⚠️ structure lost |
| 384 | `adoptarea opiniei referitoare` | ✓ (but no eu_opinion subtype) |

### Extracted vs. Unextracted N-Gram Comparison

The 1,662 items **without entities** are structurally identical to extracted items.
Their "over-represented" n-grams are mostly date/year patterns, not new entity types.
This confirms the regex taxonomy is comprehensive — the gap is a build script re-run,
not missing patterns.

### Single-Word Topical Frequencies (stopwords removed)

| Count | Word | Notes |
|---|---|---|
| 6,992 | `2025` | Year references dominate (nr.X/YYYY patterns) |
| 3,269 | `2024` | |
| 2,893 | `adoptare` | Decision: adoption |
| 1,475 | `2026` | |
| 1,266 | `2023` | |
| 1,210 | `buget` | Budget commission context |
| 1,182 | `juridică` | Legal commission |
| 920 | `măsuri` | "măsuri fiscal-bugetare" etc. |
| 919 | `publică` | "administrație publică" |
| 763 | `european` | EU opinion context |
| 702 | `acte normative` | "modificarea unor acte normative" |
| 614 | `condițiile` / `teza` / `iii-a` / `constituția` | Constitutional basis cluster |
| 576 | `respingere` | Rejection decision |
| 499 | `adoptarea` | Adoption (noun) |

---

## Gaps Discovered via N-Grams

### 1. Constitutional Basis Boilerplate (614 occurrences)

The n-gram cluster `teza III-a` → `constituția României` → `republicată` appears in ~13% of items but isn't captured as a discrete entity. This is the constitutional procedure marker (art.75/art.115) that determines whether the Chamber is the decisional body.

**Current state:** Partial — `adoptat_art115` flag exists but only catches one variant.
**N-grams surfaced:** `teza iii-a constituția româniei republicată` (4-gram, 587×)

### 2. Procedural Stage Sequence

"Adoptat de Senat → Raport → Cameră decizională" is a formulaic sequence. Currently only the senate date is extracted; the procedural *stage* (which chamber has acted, what remains) isn't modeled.

**Current state:** `senate_adoption_date` (date only), `camera_decizionala` (flag only).
**N-grams surfaced:** `adoptat senat [year]raport comun comisia` (4-gram chain, 774×)

### 3. EU Opinion Subtype

`proiect_hotarare` items with "adoptarea opiniei referitoare la Comunicarea Comisiei către Parlamentul European" form a large subtype (~300 items) but aren't tagged with a subtype flag like `eu_opinion`.

**Current state:** `item_type: proiect_hotarare` ✓, but no subtype distinction.
**N-grams surfaced:** `adoptarea opiniei referitoare comunicarea comisiei` (4-gram, 384×)

### 4. Commission Extraction Scope

The regex only scans lines starting with "Raport"/"Raport comun". Commissions mentioned in "Aviz" or "punct de vedere" contexts are missed. N-grams show some commission names appear in patterns that don't start with "Raport".

### 5. Motion Topic Extraction

Moțiune items have `initiator_count` and `initiator_type` but the motion *topic* isn't extracted as a `subject`. The topic usually appears after "cu tema" or in the motion title.

---

## Practical Use of N-Grams for This Project

### What n-grams do well (vs. regex)

| Capability | Regex | N-grams |
|---|---|---|
| Known pattern extraction | ✓ precise | Overkill |
| Unknown pattern discovery | ✗ blind spot | ✓ surfaces new formulaic phrases |
| Drift detection over time | ✗ needs manual updates | ✓ new n-grams = new legislative formulas |
| Stopword-aware topical keywords | N/A | ✓ wordcloud-style insight |
| Morphological variant handling | Manual `(?:a|ei?)` patterns | ✗ no lemmatization |

### Recommended approach

1. **Keep regex for extraction** — it's precise, fast, and covers ~95% of patterns.
2. **Use n-grams for discovery** — periodically run n-gram analysis on the corpus to:
   - Surface new formulaic phrases (drift detection)
   - Validate the existing taxonomy (what's trending up/down)
   - Generate a "wordcloud" of legislative topics for each session
3. **Add spaCy only if needed** — for lemmatization (grouping morphological variants) or noun-phrase chunking (better subject extraction). The ~15 MB `ro_core_news_sm` model would add Romanian POS tagging and NER.

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
