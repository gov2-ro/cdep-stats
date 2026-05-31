# CDEP → Monitorul.ai Correspondence

**Generated:** 2026-05-31
**Total entries:** 1050 (786 unique deputies across legislatures 2016, 2020, 2024)

## Method

The `person_id` slug is derived algorithmically from the deputy name:
1. Lowercase
2. Strip Romanian diacritics (ă→a, â→a, î→i, ş→s, ţ→t, etc.)
3. Replace spaces and special chars with hyphens

## Accuracy

- **Verified sample:** 50 randomly selected deputies
- **Exact match rate:** 86% (43/50)
- **Known fixes applied:** 9

### Mismatch patterns (all found correctly by `search_persons`)

| Deputy (cdep) | Algorithmic ID | Canonical ID | Reason |
|---|---|---|---|
| Gheba Daniel-Sorin | gheba-daniel-sorin | daniel-sorin-gheba | Name order reversed |
| Anastase Roberta Alma | anastase-roberta-alma | anastase-roberta | Middle name dropped |
| Ciolacu Ion-Marcel | ciolacu-ion-marcel | ciolacu-marcel | Short form |
| Gorghiu Alina-Ştefania | gorghiu-alina-stefania | gorghiu-alina | Short form |
| Zahoranszki Brigitta-Eva | zahoranszki-brigitta-eva | brigitta-eva-zahoranszki | Name order reversed |
| Ardeleanu Georgiana-Anca | ardeleanu-georgiana-anca | georgiana-anca-ardeleanu | Name order reversed |
| Vidra Vlad-Andrei | vidra-vlad-andrei | andrei-vidra-vlad | Name order reversed |

## ID Systems

| ID | Source | Format | Scope |
|---|---|---|---|
| `cdep_id` | cdep.ro (scraped) | 16-char hex hash | Stable across legislatures |
| `cdep_idm` | cdep.ro (scraped) | Integer (1–363) | Per-legislature; used in `?idm=N&leg=YYYY` URLs |
| `monitorul_id` | monitorul.ai | Name-derived slug | Stable; e.g. `adomnicai-mirela-elena` |

## Files

| File | Key | Description |
|---|---|---|
| `monitorul_cdep.json` | — | Full correspondence with all fields and metadata |
| `monitorul_cdep_lookup.json` | `cdep_id` | `cdep_id → {cdep_idm, cdep_url, monitorul_id, monitorul_url, ...}` |
| `monitorul_idm_lookup.json` | `"{idm}_{leg}"` | `"319_2024" → {monitorul_id, monitorul_url, cdep_name, ...}` |

## Usage

```python
import json

# By internal cdep_id
with open('data/v1/correspondence/monitorul_cdep_lookup.json') as f:
    lookup = json.load(f)
profile = lookup[deputy_id]
# → {cdep_idm, cdep_name, legislatura, cdep_url, monitorul_id, monitorul_url}

# By cdep.ro numerical idm + legislature (e.g. ?idm=319&leg=2024)
with open('data/v1/correspondence/monitorul_idm_lookup.json') as f:
    idm_lookup = json.load(f)
profile = idm_lookup["319_2024"]
# → {cdep_id, cdep_name, monitorul_id, monitorul_url}
```

## Verification

To verify an entry, use the MCP `search_persons` tool with the deputy name:
```
mcp__monitorul__search_persons(q="Deputy Name")
```
Take the first result that is not an "înlocuit" or "online" variant.