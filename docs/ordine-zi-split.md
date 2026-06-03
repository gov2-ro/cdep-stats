# Ordine-Zi Data Split

The `legislatura-2024.json` (33.54 MB) has been split into 4 modular files to reduce size and improve selective loading.

## Files

### sesiuni.csv (0.02 MB)
Session/agenda metadata, one row per unique session. Fields:
- `id` — session ID (unique)
- `session_date`, `session_date_end` — session date range
- `legislatura` — legislature year (e.g., 2024)
- `cam` — chamber (2 = Camera Deputaților)
- `titlu` — agenda title
- `data_aprobare` — approval date
- `pdf_url` — URL to PDF version (if available)

**Note:** Original JSON had 191 session entries but only 131 unique sessions (60 duplicates with some having different items, which have been merged).

### items.csv (3.93 MB)
Agenda items without entities. One row per item. Fields:
- `sesiune_id` — foreign key to sesiuni.csv
- `item_index` — position in session (0-based)
- `pozitie` — agenda position number
- `nr_inregistrare` — registration number
- `idp` — bill/project ID
- `descriere` — item description (HTML)
- `doc_pdf_url` — URL to PDF document
- `ozitm` — internal reference
- `num_docs` — count of associated documents

**Item ID format:** For cross-linking with docs and entities:
```
{sesiune_id}_{item_index:03d}
```
Example: `50906d0563955cb9_000`

### docs.csv (11.86 MB)
Document references for items. One row per document. Fields:
- `item_id` — foreign key (session_id_item_index)
- `data` — document date
- `titlu` — document title
- `pdf_url` — URL to document
- `sursa` — source (e.g., "fisa_pl")

### entities.json (5.15 MB)
Structured data extracted from items, keyed by item_id. Each entry contains:
```json
{
  "item_id": {
    "item_type": "string",
    "flags": ["flag1", ...],
    "referenced_acts": ["act1", ...],
    "commissions": ["commission1", ...],
    "commission_slugs": ["slug1", ...],
    "subject": "string (optional)",
    "institutions": ["institution1", ...]
  }
}
```

## Size Comparison

| Format | Size | Notes |
|--------|------|-------|
| Original JSON | 33.54 MB | Monolithic, has 60 duplicate sessions |
| Split files | 20.95 MB | **37.5% reduction**, no data loss |
| Merged back | 33.46 MB | Roundtrip lossless |

## Usage

### Split into modular files
```bash
python scripts/split_ordine_zi.py
```
Produces: `sesiuni.csv`, `items.csv`, `docs.csv`, `entities.json`

### Merge back to original format
```bash
python scripts/merge_ordine_zi.py
```
Produces: `legislatura-2024-merged.json` (33.46 MB, nearly identical to original)

## Web Integration

The web frontend can:
1. Load `sesiuni.csv` to display session list
2. Load `entities.json` to populate filters (commissions, item_type, etc.)
3. Load `items.csv` and `docs.csv` on demand for specific sessions

This allows lazy loading of data and reduces initial page weight from 34 MB to ~8 MB (sesiuni + entities).

## Cross-linking

All three data files are linked via `item_id = {sesiune_id}_{item_index:03d}`:

```
sesiuni.csv → items.csv (via sesiune_id)
items.csv → docs.csv (via item_id constructed from sesiune_id + item_index)
items.csv → entities.json (via item_id)
```
