# Deputies Avere Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a per-deputy wealth circle-visualization dashboard at `deputati-avere.html`, driven by a new `build_avere_deputies.py` build script.

**Architecture:** A new Python script joins three existing data sources (avere index, per-deputy detail files, deputati index) into `data/v1/stats/avere-deputies-2024.json`; a standalone HTML page reads that JSON and renders deputies as circles sized by the selected wealth metric, filterable by party and name search.

**Tech Stack:** Python 3.11+, Pydantic v2, vanilla HTML/CSS/JS, existing `i18n.js` pattern.

---

## File Map

| File | Action |
|---|---|
| `scripts/build_avere_deputies.py` | **Create** — joins three data sources, emits per-deputy JSON |
| `tests/test_build_avere_deputies.py` | **Create** — unit tests for join/null logic |
| `deputati-avere.html` | **Create** — circle dashboard page |
| `i18n.js` | **Modify** — add ~15 new ro+en keys |
| `avere.html` | **Modify** — add link to new page |

---

## Task 1: Tests for build_avere_deputies.py

**Files:**
- Create: `tests/test_build_avere_deputies.py`

- [ ] **Step 1.1: Write the test file**

```python
"""Tests for build_avere_deputies.build_leg() join logic."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _build_leg(root: Path, leg: int) -> int:
    """Import and run build_leg against a tmp root."""
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location(
        "build_avere_deputies",
        Path(__file__).resolve().parent.parent / "scripts" / "build_avere_deputies.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    # Patch ROOT inside the module to use tmp dir
    mod.__dict__["ROOT"] = root  # type: ignore[attr-defined]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.build_leg(leg)  # type: ignore[attr-defined]


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    leg = 2024

    # 1. avere index
    _write_json(
        tmp_path / f"data/v1/declaratii-avere/legislatura-{leg}.json",
        {
            "meta": {},
            "data": [
                {
                    "cdep_idm": 1,
                    "deputat_nume": "Popescu Ion",
                    "legislatura": leg,
                    "partid_short": "PSD",
                    "n_declaratii": 1,
                    "ultima_conturi_ron": 100000.0,
                    "ultima_venituri_ron": 50000.0,
                    "ultima_imobile_count": 2,
                },
                {
                    "cdep_idm": 2,
                    "deputat_nume": "Ionescu Ana",
                    "legislatura": leg,
                    "partid_short": "PNL",
                    "n_declaratii": 0,  # no declaration
                    "ultima_conturi_ron": None,
                    "ultima_venituri_ron": None,
                    "ultima_imobile_count": None,
                },
            ],
        },
    )

    # 2. avere detail for deputy 1 only
    _write_json(
        tmp_path / f"data/v1/declaratii-avere/legislatura-{leg}/1.json",
        {
            "data": {
                "cdep_idm": 1,
                "declaratii": [
                    {
                        "suprafata_total_mp": 150.0,
                        "datorii_total_ron": 30000.0,
                        "auto_count": 2,
                    }
                ],
            }
        },
    )

    # 3. deputati index
    _write_json(
        tmp_path / f"data/v1/deputati/legislatura-{leg}.json",
        {
            "meta": {},
            "data": [
                {"cdep_idm": 1, "image": "https://cdep.ro/img/1.jpg"},
                {"cdep_idm": 2, "image": "https://cdep.ro/img/2.jpg"},
            ],
        },
    )

    # 4. party CSV
    csv_path = tmp_path / "data/assets/legenda-partide.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "ID,Denumire,Ordine,Logo,CUI,Adresa,Judet,UAT,tip-partid\n"
        "PSD,Partidul Social Democrat,1,PSD.jpg,,,,, \n"
        "PNL,Partidul National Liberal,2,PNL.jpg,,,,, \n",
        encoding="utf-8",
    )

    return tmp_path


def test_output_file_created(root: Path) -> None:
    ret = _build_leg(root, 2024)
    assert ret == 0
    out = root / "data/v1/stats/avere-deputies-2024.json"
    assert out.exists()


def test_deputies_count(root: Path) -> None:
    _build_leg(root, 2024)
    payload = json.loads(
        (root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    assert len(payload["deputies"]) == 2


def test_deputy_with_declaration(root: Path) -> None:
    _build_leg(root, 2024)
    payload = json.loads(
        (root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    dep = next(d for d in payload["deputies"] if d["cdep_idm"] == 1)
    assert dep["name"] == "Popescu Ion"
    assert dep["partid"] == "PSD"
    assert dep["image"] == "https://cdep.ro/img/1.jpg"
    assert dep["conturi_ron"] == 100000.0
    assert dep["venituri_ron"] == 50000.0
    assert dep["imobile_count"] == 2
    assert dep["suprafata_mp"] == 150.0
    assert dep["datorii_ron"] == 30000.0
    assert dep["auto_count"] == 2


def test_deputy_without_declaration_has_nulls(root: Path) -> None:
    _build_leg(root, 2024)
    payload = json.loads(
        (root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    dep = next(d for d in payload["deputies"] if d["cdep_idm"] == 2)
    assert dep["conturi_ron"] is None
    assert dep["suprafata_mp"] is None
    assert dep["image"] == "https://cdep.ro/img/2.jpg"


def test_parties_dict_present(root: Path) -> None:
    _build_leg(root, 2024)
    payload = json.loads(
        (root / "data/v1/stats/avere-deputies-2024.json").read_text(encoding="utf-8")
    )
    assert "parties" in payload
    assert payload["parties"]["PSD"] == "PSD.jpg"
    assert payload["parties"]["PNL"] == "PNL.jpg"


def test_missing_avere_index_returns_nonzero(tmp_path: Path) -> None:
    ret = _build_leg(tmp_path, 2024)
    assert ret != 0
```

- [ ] **Step 1.2: Run tests — expect import error (module doesn't exist yet)**

```bash
PYTHONPATH=. pytest tests/test_build_avere_deputies.py -v 2>&1 | head -30
```

Expected: some form of `FileNotFoundError` or `ModuleNotFoundError` — the script doesn't exist yet, which confirms the test file is wired up correctly.

- [ ] **Step 1.3: Commit test file**

```bash
git add tests/test_build_avere_deputies.py
git commit -m "test(avere-deputies): add join/null tests for build_avere_deputies"
```

---

## Task 2: Implement build_avere_deputies.py

**Files:**
- Create: `scripts/build_avere_deputies.py`

- [ ] **Step 2.1: Write the script**

```python
"""Build per-deputy avere payload pentru deputati-avere.html circle dashboard.

Joins:
  1. data/v1/declaratii-avere/legislatura-{leg}.json  — index (cdep_idm, name, partid, metrics)
  2. data/v1/declaratii-avere/legislatura-{leg}/{cdep_idm}.json — detalii (suprafata/auto/datorii)
  3. data/v1/deputati/legislatura-{leg}.json — imagine URL

Emite: data/v1/stats/avere-deputies-{leg}.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from schemas.common import Meta  # noqa: E402

ALL_LEGS = [2024, 2020]


def _load_detail_extras(root: Path, leg: int) -> dict[int, dict]:
    """Returnează {cdep_idm: {suprafata_mp, auto_count, datorii_ron}} din ultima declarație."""
    detail_dir = root / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}"
    extras: dict[int, dict] = {}
    if not detail_dir.is_dir():
        return extras
    for fpath in detail_dir.glob("*.json"):
        try:
            raw = json.loads(fpath.read_text(encoding="utf-8"))["data"]
            declaratii = raw.get("declaratii") or []
            if not declaratii:
                continue
            last = declaratii[-1]
            extras[raw["cdep_idm"]] = {
                "suprafata_mp": last.get("suprafata_total_mp"),
                "auto_count": last.get("auto_count"),
                "datorii_ron": last.get("datorii_total_ron"),
            }
        except (KeyError, json.JSONDecodeError):
            continue
    return extras


def _load_images(root: Path, leg: int) -> dict[int, str]:
    """Returnează {cdep_idm: image_url} din indexul de deputați."""
    deputati_file = root / "data" / "v1" / "deputati" / f"legislatura-{leg}.json"
    if not deputati_file.exists():
        return {}
    data = json.loads(deputati_file.read_text(encoding="utf-8")).get("data", [])
    return {d["cdep_idm"]: d.get("image", "") for d in data if "cdep_idm" in d}


def _load_parties(root: Path) -> dict[str, str]:
    """Returnează {partid_short: logo_filename} din legenda-partide.csv."""
    csv_file = root / "data" / "assets" / "legenda-partide.csv"
    parties: dict[str, str] = {}
    if not csv_file.exists():
        return parties
    with csv_file.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pid = (row.get("ID") or "").strip()
            logo = (row.get("Logo") or "").strip()
            if pid and logo:
                parties[pid] = logo
    return parties


def build_leg(leg: int, root: Path = ROOT) -> int:
    index_file = root / "data" / "v1" / "declaratii-avere" / f"legislatura-{leg}.json"
    if not index_file.exists():
        print(
            f"Lipsește {index_file}. Rulează întâi build_declaratii_avere.py --leg {leg}",
            file=sys.stderr,
        )
        return 1

    avere_index: list[dict] = json.loads(index_file.read_text(encoding="utf-8"))["data"]
    extras = _load_detail_extras(root, leg)
    images = _load_images(root, leg)
    parties = _load_parties(root)

    deputies = []
    for d in avere_index:
        idm: int = d["cdep_idm"]
        ex = extras.get(idm, {})
        has_decl = d.get("n_declaratii", 0) > 0
        deputies.append(
            {
                "cdep_idm": idm,
                "name": d["deputat_nume"],
                "partid": d.get("partid_short") or "Neafiliat",
                "image": images.get(idm, ""),
                "venituri_ron": d.get("ultima_venituri_ron") if has_decl else None,
                "conturi_ron": d.get("ultima_conturi_ron") if has_decl else None,
                "imobile_count": d.get("ultima_imobile_count") if has_decl else None,
                "suprafata_mp": ex.get("suprafata_mp") if has_decl else None,
                "auto_count": ex.get("auto_count") if has_decl else None,
                "datorii_ron": ex.get("datorii_ron") if has_decl else None,
            }
        )

    payload = {
        "meta": Meta(
            generated_at=datetime.now(UTC),
            source_url=(
                f"https://endimion2k.github.io/cdep-api-poc/"
                f"data/v1/declaratii-avere/legislatura-{leg}.json"
            ),
            scraper_version="0.1.0",
            count=len(deputies),
        ).model_dump(mode="json"),
        "parties": parties,
        "deputies": deputies,
    }

    out_dir = root / "data" / "v1" / "stats"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"avere-deputies-{leg}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK leg {leg}: {len(deputies)} deputați · {len(parties)} partide → {out_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build per-deputy avere JSON for circle dashboard."
    )
    parser.add_argument("--leg", type=int, default=2024)
    parser.add_argument("--all", action="store_true", help="Build all legs")
    args = parser.parse_args()

    legs = ALL_LEGS if args.all else [args.leg]
    ret = 0
    for leg in legs:
        r = build_leg(leg)
        if r != 0 and not args.all:
            return r
        ret = ret or r
    return ret


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2.2: Run tests — all should pass**

```bash
PYTHONPATH=. pytest tests/test_build_avere_deputies.py -v
```

Expected output:
```
tests/test_build_avere_deputies.py::test_output_file_created PASSED
tests/test_build_avere_deputies.py::test_deputies_count PASSED
tests/test_build_avere_deputies.py::test_deputy_with_declaration PASSED
tests/test_build_avere_deputies.py::test_deputy_without_declaration_has_nulls PASSED
tests/test_build_avere_deputies.py::test_parties_dict_present PASSED
tests/test_build_avere_deputies.py::test_missing_avere_index_returns_nonzero PASSED
```

- [ ] **Step 2.3: Run against real data and verify shape**

```bash
PYTHONPATH=. python scripts/build_avere_deputies.py --leg 2024
```

Expected: `OK leg 2024: 332 deputați · N partide → data/v1/stats/avere-deputies-2024.json`

Then verify spot-check:
```bash
python3 -c "
import json
d = json.load(open('data/v1/stats/avere-deputies-2024.json'))
print('parties:', list(d['parties'].keys())[:8])
print('total deputies:', len(d['deputies']))
print('sample:', json.dumps(d['deputies'][0], ensure_ascii=False, indent=2))
nulls = sum(1 for x in d['deputies'] if x['conturi_ron'] is None)
print('null conturi:', nulls)
"
```

- [ ] **Step 2.4: Lint**

```bash
ruff check scripts/build_avere_deputies.py && ruff format scripts/build_avere_deputies.py
```

- [ ] **Step 2.5: Commit**

```bash
git add scripts/build_avere_deputies.py data/v1/stats/avere-deputies-2024.json
git commit -m "feat(avere-deputies): build script — joins avere+deputati+partide"
```

---

## Task 3: Add i18n keys

**Files:**
- Modify: `i18n.js`

- [ ] **Step 3.1: Find the insertion point in i18n.js**

Open `i18n.js`. Locate the `ro: { ... }` block and the matching `en: { ... }` block. The new keys go at the end of each block (before the closing `}`).

- [ ] **Step 3.2: Add Romanian keys**

In the `ro: { ... }` block, add after the last existing key:

```javascript
    // Deputies avere dashboard (deputati-avere.html)
    avere_deputies_title: "Averi deputați — vizualizare",
    avere_deputies_sub: "Fiecare cerc = un deputat · mărimea = metrica selectată",
    view_circles: "Cercuri",
    view_list: "Listă",
    metric_venituri: "Venituri anuale",
    metric_conturi: "Conturi bancare",
    metric_imobile: "Nr. imobile",
    metric_suprafata: "Suprafață terenuri (mp)",
    metric_auto: "Nr. autovehicule",
    metric_datorii: "Datorii",
    filter_parties: "Filtrează partide",
    search_deputies: "Caută deputat...",
    deputies_count: "deputați",
    no_declaration: "Fără declarație",
    data_from: "Date din",
```

- [ ] **Step 3.3: Add English keys**

In the `en: { ... }` block, add matching keys:

```javascript
    // Deputies avere dashboard (deputati-avere.html)
    avere_deputies_title: "Deputies' wealth — visualization",
    avere_deputies_sub: "Each circle = one deputy · size = selected metric",
    view_circles: "Circles",
    view_list: "List",
    metric_venituri: "Annual income",
    metric_conturi: "Bank accounts",
    metric_imobile: "No. properties",
    metric_suprafata: "Land area (sqm)",
    metric_auto: "No. vehicles",
    metric_datorii: "Debts",
    filter_parties: "Filter parties",
    search_deputies: "Search deputy...",
    deputies_count: "deputies",
    no_declaration: "No declaration",
    data_from: "Data from",
```

- [ ] **Step 3.4: Verify no syntax errors**

```bash
node -e "const I18N = $(grep -A 9999 'const I18N' i18n.js | head -1); console.log('ok')" 2>&1 || node --input-type=module < i18n.js 2>&1 | head -5
```

Or simply: open a browser console and paste the i18n.js content to check for JS syntax errors.

Simpler check:
```bash
node -c i18n.js
```

- [ ] **Step 3.5: Commit**

```bash
git add i18n.js
git commit -m "feat(avere-deputies): add i18n keys for circle dashboard"
```

---

## Task 4: Implement deputati-avere.html

**Files:**
- Create: `deputati-avere.html`

- [ ] **Step 4.1: Write the page**

```html
<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Averi deputați — vizualizare · Camera Deputaților</title>
<meta name="description" content="Fiecare deputat ca un cerc — mărimea proporțională cu averea declarată. Filtrare pe partid și metrică.">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#fff;--bg2:#f8f8f6;--bg3:#f2f1ee;
  --text:#1a1a1a;--text2:#555;--text3:#888;
  --border:#e0deda;--border2:#ccc;
  --green:#1D9E75;--green-text:#3B6D11;
  --blue:#185FA5;--blue-bg:#E6F1FB;--blue-text:#185FA5;
  --red-bg:#FCEBEB;--red-text:#A32D2D;
  --amber-bg:#FAEEDA;--amber-text:#854F0B;
  --radius:10px;--radius-sm:6px;
  --font:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
}
@media(prefers-color-scheme:dark){
  :root{--bg:#1a1a1a;--bg2:#232323;--bg3:#2a2a2a;--text:#e8e6e0;--text2:#aaa;--text3:#666;--border:#333;--border2:#444;}
}
body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.6;font-size:15px}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
.header{border-bottom:1px solid var(--border);padding:16px 0}
.header-inner{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;align-items:center;gap:16px}
.logo{font-size:15px;font-weight:600;color:var(--text)}
.logo span{color:var(--green)}
.back{margin-left:auto;font-size:13px;color:var(--text2);padding:6px 12px;border-radius:var(--radius-sm)}
.back:hover{background:var(--bg2);text-decoration:none}

.toolbar{position:sticky;top:0;z-index:10;background:var(--bg);border-bottom:1px solid var(--border);padding:10px 0}
.toolbar-inner{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;flex-wrap:wrap;align-items:center;gap:10px}
.view-toggle{display:flex;border:1px solid var(--border2);border-radius:var(--radius-sm);overflow:hidden}
.view-btn{padding:5px 12px;font-size:12px;border:none;background:var(--bg);color:var(--text2);cursor:pointer}
.view-btn.active{background:var(--blue-bg);color:var(--blue-text);font-weight:600}
.view-btn:disabled{opacity:0.4;cursor:not-allowed}
.metric-select{font-size:13px;padding:5px 10px;border:1px solid var(--border2);border-radius:var(--radius-sm);background:var(--bg);color:var(--text);cursor:pointer}
.party-chips{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
.party-chip{display:flex;align-items:center;gap:4px;padding:3px 8px 3px 4px;border-radius:12px;border:1px solid var(--border2);background:var(--bg2);font-size:11px;cursor:pointer;user-select:none;transition:opacity .15s}
.party-chip img{width:14px;height:14px;object-fit:contain;border-radius:2px}
.party-chip.off{opacity:0.35}
.search-input{font-size:13px;padding:5px 10px;border:1px solid var(--border2);border-radius:var(--radius-sm);background:var(--bg);color:var(--text);width:160px}
.count-badge{font-size:12px;color:var(--text3);white-space:nowrap;margin-left:auto}

.main{max-width:1200px;margin:0 auto;padding:20px 24px}
h1{font-size:22px;font-weight:600;margin-bottom:4px}
.sub{color:var(--text3);font-size:13px;margin-bottom:20px}

.circle-grid{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;padding:8px 0}
.dep-item{display:flex;flex-direction:column;align-items:center;cursor:pointer;position:relative}
.dep-item:hover .dep-circle{filter:brightness(0.9)}
.dep-circle{border-radius:50%;overflow:hidden;position:relative;flex-shrink:0;transition:width .3s, height .3s}
.dep-circle img{width:100%;height:100%;object-fit:cover;display:block}
.dep-circle .initials{width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-weight:600;color:#fff;font-size:calc(var(--sz) * 0.3)}
.dep-badge{position:absolute;bottom:2px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:2px;padding:1px 4px;border-radius:3px;font-size:9px;color:#fff;font-weight:600;white-space:nowrap;pointer-events:none}
.dep-badge img{width:10px;height:10px;object-fit:contain}
.dep-name{font-size:9px;color:var(--text2);margin-top:3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-align:center}
.dep-value{font-size:8px;color:var(--text3);text-align:center}
.dep-item.null-val .dep-circle{opacity:0.45}
.dep-item.null-val .dep-value{font-style:italic}

.tooltip{position:fixed;z-index:100;background:rgba(0,0,0,.85);color:#fff;font-size:12px;padding:7px 10px;border-radius:6px;pointer-events:none;max-width:220px;line-height:1.5;display:none}

.loading{text-align:center;padding:60px 0;color:var(--text3)}
.error{padding:24px;background:var(--red-bg);color:var(--red-text);border-radius:var(--radius);margin:20px 0}
.footer{border-top:1px solid var(--border);padding:20px 24px;margin-top:48px;font-size:12px;color:var(--text3);text-align:center}
.footer a{color:var(--text2)}
</style>
</head>
<body>

<header class="header">
  <div class="header-inner">
    <span class="logo">cdep<span>.api</span></span>
    <a href="avere.html" class="back" data-i18n="back">← Înapoi</a>
    <span id="lang-toggle-slot" style="margin-left:8px;display:flex;align-items:center"></span>
  </div>
</header>

<div class="toolbar">
  <div class="toolbar-inner">
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles" data-i18n="view_circles">Cercuri</button>
      <button class="view-btn" id="btn-list" disabled data-i18n="view_list">Listă</button>
    </div>
    <select class="metric-select" id="metric-select">
      <option value="venituri_ron" data-i18n="metric_venituri">Venituri anuale</option>
      <option value="conturi_ron" data-i18n="metric_conturi">Conturi bancare</option>
      <option value="imobile_count" data-i18n="metric_imobile">Nr. imobile</option>
      <option value="suprafata_mp" data-i18n="metric_suprafata">Suprafață terenuri (mp)</option>
      <option value="auto_count" data-i18n="metric_auto">Nr. autovehicule</option>
      <option value="datorii_ron" data-i18n="metric_datorii">Datorii</option>
    </select>
    <div class="party-chips" id="party-chips"></div>
    <input class="search-input" id="search-input" type="text" placeholder="Caută deputat…" data-i18n-attr="placeholder:search_deputies">
    <span class="count-badge" id="count-badge"></span>
  </div>
</div>

<div class="main">
  <h1 data-i18n="avere_deputies_title">Averi deputați — vizualizare</h1>
  <p class="sub" data-i18n="avere_deputies_sub">Fiecare cerc = un deputat · mărimea = metrica selectată</p>
  <div id="circle-grid" class="circle-grid"><div class="loading" data-i18n="loading">Se încarcă…</div></div>
</div>

<div class="tooltip" id="tooltip"></div>

<footer class="footer">
  <p><span data-i18n="data_from">Date din</span> <a href="https://cdep.ro" target="_blank">cdep.ro</a> ·
  <span data-i18n="source">Sursă JSON</span>: <a href="data/v1/stats/avere-deputies-2024.json">avere-deputies-2024.json</a> ·
  <a href="avere.html" data-i18n="nav_avere">Averi (agregate)</a> ·
  <a href="index.html" data-i18n="page_main">Pagina principală</a></p>
</footer>

<script>
const LEG = 2024;
const DATA_URL = `data/v1/stats/avere-deputies-${LEG}.json`;

// Party colors (short → hex), fallback #888 for unknown
const PARTY_COLORS = {
  'PSD':'#185FA5','PNL':'#993C1D','USR':'#3B6D11','AUR':'#854F0B',
  'UDMR':'#5F5E5A','SOSRO':'#A32D2D','POT':'#553378','PMP':'#6D5A9E',
  'PROEUROPA':'#888','Neafiliat':'#888',
};
function partyColor(partid) { return PARTY_COLORS[partid] || '#888'; }

// Formatare compactă pentru valori mari
function fmtVal(v, metric) {
  if (v == null) return '—';
  if (['venituri_ron','conturi_ron','datorii_ron'].includes(metric)) {
    const a = Math.abs(v);
    if (a >= 1e6) return (a/1e6).toFixed(a>=1e7?0:1) + 'M RON';
    if (a >= 1e3) return Math.round(a).toLocaleString('ro-RO') + ' RON';
    return Math.round(a) + ' RON';
  }
  if (metric === 'suprafata_mp') return Math.round(v).toLocaleString('ro-RO') + ' mp';
  return v.toLocaleString('ro-RO');
}

// Mărimea cercului: diametru în px, sqrt-scale, normalizat la maxValue
function circleSize(value, maxValue) {
  if (value == null || value <= 0 || maxValue <= 0) return 12;
  return Math.round(Math.max(12, Math.min(68, 12 + 56 * Math.sqrt(value / maxValue))));
}

function initials(name) {
  const parts = name.split(/[\s,]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

let ALL_DEPUTIES = [];
let PARTIES = {};
let activeParties = new Set();
let searchQuery = '';
let metric = 'venituri_ron';

function filteredDeputies() {
  return ALL_DEPUTIES.filter(d => {
    if (!activeParties.has(d.partid)) return false;
    if (searchQuery && !d.name.toLowerCase().includes(searchQuery)) return false;
    return true;
  });
}

function sortedDeputies(deps) {
  return [...deps].sort((a, b) => {
    const av = a[metric], bv = b[metric];
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;
    return bv - av;
  });
}

function render() {
  const deps = sortedDeputies(filteredDeputies());
  const grid = document.getElementById('circle-grid');

  const vals = deps.map(d => d[metric]).filter(v => v != null && v > 0);
  const maxVal = vals.length ? Math.max(...vals) : 1;

  document.getElementById('count-badge').textContent =
    deps.length + ' ' + (window.I18N_T?.('deputies_count') || 'deputați');

  if (!deps.length) {
    grid.innerHTML = '<p style="color:var(--text3);padding:40px 0">Niciun deputat.</p>';
    return;
  }

  grid.innerHTML = deps.map(d => {
    const v = d[metric];
    const sz = circleSize(v, maxVal);
    const isNull = v == null;
    const color = partyColor(d.partid);
    const logo = PARTIES[d.partid];
    const badgeHidden = sz < 14 ? 'display:none' : '';
    const detailUrl = `data/v1/declaratii-avere/legislatura-${LEG}/${d.cdep_idm}.json`;

    const badgeHtml = logo
      ? `<span class="dep-badge" style="background:${color};${badgeHidden}">
           <img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'">
           ${d.partid}
         </span>`
      : `<span class="dep-badge" style="background:${color};${badgeHidden}">${d.partid}</span>`;

    const circleContent = d.image
      ? `<img src="${d.image}" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
              alt="${d.name}">
         <div class="initials" style="--sz:${sz}px;background:${color};display:none">${initials(d.name)}</div>`
      : `<div class="initials" style="--sz:${sz}px;background:${color}">${initials(d.name)}</div>`;

    return `<div class="dep-item${isNull?' null-val':''}"
                 data-idm="${d.cdep_idm}"
                 data-name="${d.name.replace(/"/g,'&quot;')}"
                 data-value="${v ?? ''}"
                 data-partid="${d.partid}"
                 onclick="window.open('${detailUrl}','_blank')">
      <div class="dep-circle" style="width:${sz}px;height:${sz}px">
        ${circleContent}
        ${badgeHtml}
      </div>
      <div class="dep-name" style="max-width:${sz+8}px">${d.name.split(',')[0]}</div>
      <div class="dep-value">${isNull ? '—' : fmtVal(v, metric)}</div>
    </div>`;
  }).join('');
}

function buildPartyChips(partids) {
  const el = document.getElementById('party-chips');
  el.innerHTML = partids.map(p => {
    const logo = PARTIES[p];
    const color = partyColor(p);
    const img = logo
      ? `<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'">`
      : `<span style="width:10px;height:10px;border-radius:2px;background:${color};display:inline-block"></span>`;
    return `<span class="party-chip" data-partid="${p}" onclick="toggleParty('${p}')">
      ${img}${p}
    </span>`;
  }).join('');
}

function toggleParty(p) {
  if (activeParties.has(p)) activeParties.delete(p);
  else activeParties.add(p);
  document.querySelectorAll('.party-chip').forEach(el => {
    el.classList.toggle('off', !activeParties.has(el.dataset.partid));
  });
  render();
}

// Tooltip
const tooltip = document.getElementById('tooltip');
document.addEventListener('mouseover', e => {
  const item = e.target.closest('.dep-item');
  if (!item) { tooltip.style.display = 'none'; return; }
  const v = item.dataset.value;
  const label = fmtVal(v === '' ? null : Number(v), metric);
  tooltip.textContent = `${item.dataset.name} · ${item.dataset.partid} · ${label}`;
  tooltip.style.display = 'block';
});
document.addEventListener('mousemove', e => {
  tooltip.style.left = (e.clientX + 12) + 'px';
  tooltip.style.top = (e.clientY - 28) + 'px';
});
document.addEventListener('mouseout', e => {
  if (!e.target.closest('.dep-item')) tooltip.style.display = 'none';
});

async function load() {
  try {
    const res = await fetch(DATA_URL);
    if (!res.ok) throw new Error(res.statusText);
    const data = await res.json();
    ALL_DEPUTIES = data.deputies;
    PARTIES = data.parties || {};

    // Build unique party list (in order of frequency)
    const counts = {};
    ALL_DEPUTIES.forEach(d => counts[d.partid] = (counts[d.partid]||0) + 1);
    const partids = Object.keys(counts).sort((a,b) => counts[b]-counts[a]);
    activeParties = new Set(partids);

    buildPartyChips(partids);
    render();
  } catch(e) {
    document.getElementById('circle-grid').innerHTML =
      `<div class="error">Nu pot încărca ${DATA_URL} (${e.message}). Rulează <code>python scripts/build_avere_deputies.py --leg ${LEG}</code>.</div>`;
  }
}

document.getElementById('metric-select').addEventListener('change', e => {
  metric = e.target.value;
  render();
});
document.getElementById('search-input').addEventListener('input', e => {
  searchQuery = e.target.value.toLowerCase().trim();
  render();
});

// Expose i18n helper for count badge (set after i18n.js loads)
window.I18N_T = null;

load();
</script>
<script src="i18n.js"></script>
<script>
// Wire up I18N_T after i18n.js has loaded and applied translations
window.I18N_T = (key) => {
  const lang = localStorage.getItem('lang') || 'ro';
  return (window.I18N && window.I18N[lang] && window.I18N[lang][key]) || key;
};
// Re-render count badge with correct language
document.getElementById('count-badge').textContent =
  document.getElementById('count-badge').textContent.replace(
    /deputați|deputies/, window.I18N_T('deputies_count')
  );
</script>
</body>
</html>
```

- [ ] **Step 4.2: Verify HTML syntax**

```bash
python3 -c "
from html.parser import HTMLParser
class Check(HTMLParser): pass
p = Check()
p.feed(open('deputati-avere.html').read())
print('HTML parses OK')
"
```

- [ ] **Step 4.3: Commit**

```bash
git add deputati-avere.html
git commit -m "feat(avere-deputies): circle dashboard page deputati-avere.html"
```

---

## Task 5: Link from avere.html

**Files:**
- Modify: `avere.html`

- [ ] **Step 5.1: Find the right insertion point**

In `avere.html`, find the header section (around line 79):
```html
<a href="index.html" class="back" data-i18n="back">← Înapoi</a>
```

Add a link to the new page just before the lang toggle slot. Specifically, look for the line:
```html
<span id="lang-toggle-slot" ...
```

Insert before it:
```html
    <a href="deputati-avere.html" style="font-size:13px;color:var(--text2);padding:6px 12px;border-radius:var(--radius-sm)" onmouseover="this.style.background='var(--bg2)'" onmouseout="this.style.background=''">⬤ Vizualizare cercuri ↗</a>
```

- [ ] **Step 5.2: Edit avere.html**

In `avere.html`, locate the exact text (around line 79):
```html
    <span id="lang-toggle-slot" style="margin-left:8px;display:flex;align-items:center"></span>
```

Replace with:
```html
    <a href="deputati-avere.html" style="font-size:13px;color:var(--text2);padding:6px 12px;border-radius:var(--radius-sm)" onmouseover="this.style.background='var(--bg2)'" onmouseout="this.style.background=''">⬤ Vizualizare cercuri ↗</a>
    <span id="lang-toggle-slot" style="margin-left:8px;display:flex;align-items:center"></span>
```

- [ ] **Step 5.3: Commit**

```bash
git add avere.html
git commit -m "feat(avere-deputies): link from avere.html to circle dashboard"
```

---

## Task 6: Smoke test in browser

- [ ] **Step 6.1: Start dev server**

```bash
python -m http.server 8000
```

Open `http://localhost:8000/deputati-avere.html` in a browser.

- [ ] **Step 6.2: Run verification checklist**

Check each item visually:

1. Circles render — ~332 circles visible, sorted largest first
2. Switch metric (Conturi → Imobile) — circles re-sort and resize without reload
3. Toggle a party chip (e.g., PSD) — PSD deputies disappear/reappear
4. Type in search — only matching names shown, count badge updates
5. Hover over a circle — tooltip shows full name + value + party
6. Click a circle — opens detail JSON in new tab
7. Resize window to mobile width (375px) — grid wraps cleanly
8. Deputies with null metric — appear at end, greyed out, value shows "—"
9. `avere.html` header shows "⬤ Vizualizare cercuri ↗" link that navigates correctly

- [ ] **Step 6.3: Update activity log**

Add an entry to `docs/activity-log.md`:

```markdown
### 2026-05-29 — Deputies Avere Circle Dashboard

Built `deputati-avere.html` — per-deputy wealth visualization as a circle grid.
Each circle is sized by square-root of the selected metric (venituri/conturi/imobile/suprafata/auto/datorii),
scaled to the current filtered set's max. Party chip filters, name search, party logo badges,
photo fallback to initials. Null-value deputies shown greyed at minimum size.
New build script `scripts/build_avere_deputies.py` joins avere index + detail files + deputati index.
Output: `data/v1/stats/avere-deputies-2024.json`.
```

- [ ] **Step 6.4: Commit activity log**

```bash
git add docs/activity-log.md
git commit -m "docs: activity log — avere deputies circle dashboard"
```

---

## Self-Review Checklist

- [x] **Spec coverage:**
  - Data pipeline (`build_avere_deputies.py`) ✓
  - `parties` dict in output ✓
  - `deputies` array with all required fields ✓
  - Null handling (null for no-declaration deputies) ✓
  - Sticky toolbar (view toggle, metric, party chips, search, count badge) ✓
  - Circle sizing: √(value/max), clamped [12, 68]px ✓
  - Party badge hidden when circle < 14px ✓
  - Photo with initials fallback ✓
  - Hover tooltip ✓
  - Click links to detail JSON ✓
  - Null deputies greyed at end ✓
  - i18n keys ✓
  - Link from avere.html ✓
  - Liste view button present but disabled ✓

- [x] **No placeholders** — all code shown explicitly

- [x] **Type consistency** — `d[metric]` used consistently throughout JS, `circleSize(v, maxVal)` signature consistent

- [x] **Deferred items from spec** — Liste view: button present, `disabled` attribute, matches spec exactly
