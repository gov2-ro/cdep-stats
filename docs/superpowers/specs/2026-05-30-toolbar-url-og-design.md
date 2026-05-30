# Design Spec: Toolbar Redesign + URL State + OG Meta

**Date:** 2026-05-30
**Status:** Approved

---

## Context

Applies to `deputati-avere.html` and `deputati-activitate.html`. Three improvements:
1. Toolbar redesign — explicit metric buttons, compact party checkbox dropdown, year last, no search
2. URL state — `replaceState` so any view is shareable/bookmarkable
3. OG meta tags + Playwright screenshots for all 6 main pages

---

## 1. Toolbar Redesign

### Desktop order (left → right)

```
[⬤ Cercuri | ≡ Tabel]  [Venituri | Conturi | Imobile | Suprafață | Auto | Datorii]  [Partide ▾]  N dep.  [2024 | 2020]
```

**View toggle** — unchanged (`btn-circles` / `btn-table`).

**Metric buttons** — replace the `<select id="metric-select">` with a `<div class="metric-btns" id="metric-btns">` containing one `<button class="metric-btn" data-metric="{key}">` per metric. Active button gets class `active`. Click sets `metric` state variable and re-renders. Labels are short: Venituri / Conturi / Imobile / Suprafață / Auto / Datorii (avere) and Ședințe / Cuvânt / Propuneri / Legi / Declarații / Întrebări (activitate).

**Party dropdown** — replaces `<div id="party-chips">`. New HTML:
```html
<div class="party-dd" id="party-dd">
  <button class="party-dd-btn" id="party-dd-btn">Partide <span id="party-dd-count"></span> ▾</button>
  <div class="party-dd-pop" id="party-dd-pop">
    <div class="party-dd-hdr">
      <span id="party-dd-total">8 partide</span>
      <a onclick="selectAllParties()">Toate</a>
      <a onclick="selectNoParties()">Niciuna</a>
    </div>
    <!-- rows injected by buildPartyDropdown() -->
  </div>
</div>
```

Button label: `Partide` when all selected; `Partide (N/total)` when filtered. Popover shows party color swatch + name + deputy count + checkbox per row. Rows sorted by count descending (same order as current chips). Popover opens/closes on button click; closes on outside click via `document.addEventListener('click', ...)`. `position: absolute` below the button, `z-index: 50`.

**Search** — removed from toolbar HTML entirely (`<input id="search-input">` deleted). The `query` state variable and `search-input` event listener are also removed. `filtered()` simplifies to `ALL.filter(d => activeParties.has(d.partid))`.

**Party dropdown JS** — `buildChips(partids)` is renamed to `buildPartyDropdown(partids)` and populates the dropdown rows instead of inline chips. `toggleParty(p)` remains but also calls `pushState()`. `selectAllParties()` sets `activeParties = new Set(ALL.map(d => d.partid))` and re-renders. `selectNoParties()` sets `activeParties = new Set()` and re-renders. Both update checkbox state and call `pushState()`.

**Count badge** — unchanged (`id="count-badge"`).

**Year toggle** — moved to far right with `margin-left: auto` on its container.

### Mobile (≤600px)

Metric buttons switch from connected segmented strip to wrapping individual pills:

```css
@media(max-width:600px){
  .metric-btns{display:flex;flex-wrap:wrap;gap:4px}
  .metric-btn{border-radius:var(--radius-sm);border:1px solid var(--border2)}
  /* remove connected border logic */
}
```

### CSS additions

```css
/* Metric buttons — desktop: connected strip */
.metric-btns{display:flex;border:1px solid var(--border2);border-radius:var(--radius-sm);overflow:hidden;flex-shrink:0}
.metric-btn{padding:5px 10px;font-size:12px;border:none;background:var(--bg);color:var(--text2);cursor:pointer;white-space:nowrap;border-right:1px solid var(--border2)}
.metric-btn:last-child{border-right:none}
.metric-btn.active{background:var(--blue-bg);color:var(--blue-text);font-weight:600}

/* Party dropdown */
.party-dd{position:relative;flex-shrink:0}
.party-dd-btn{padding:5px 10px;font-size:12px;border:1px solid var(--border2);border-radius:var(--radius-sm);background:var(--bg);color:var(--text);cursor:pointer}
.party-dd-pop{display:none;position:absolute;top:calc(100% + 4px);left:0;z-index:50;background:var(--bg);border:1px solid var(--border2);border-radius:var(--radius);min-width:200px;box-shadow:0 8px 24px rgba(0,0,0,.15)}
.party-dd-pop.open{display:block}
.party-dd-hdr{display:flex;align-items:center;gap:8px;padding:7px 12px;border-bottom:1px solid var(--border);font-size:11px;color:var(--text3)}
.party-dd-hdr a{cursor:pointer;color:var(--blue)}
.party-dd-hdr a:last-child{color:var(--text3)}
.party-dd-row{display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;border-bottom:1px solid var(--border);font-size:12px}
.party-dd-row:last-child{border-bottom:none}
.party-dd-row input[type=checkbox]{flex-shrink:0;accent-color:var(--blue);cursor:pointer}
.party-dd-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.party-dd-count-label{margin-left:auto;font-size:10px;color:var(--text3)}
```

---

## 2. URL State Persistence

### Params

| State | Param | Default (omit when) |
|---|---|---|
| Active metric | `metric=venituri_ron` | First metric in the list |
| Active parties | `parties=PSD,PNL` | All parties selected |
| View mode | `view=table` | Circles |

`leg` stays as-is (page reload on change, already works).

### Write state

Called after every state change (metric click, party toggle, view toggle):

```javascript
function pushState() {
  const params = new URLSearchParams();
  if (metric !== COLUMNS[0].key) params.set('metric', metric);
  const allKeys = [...activeParties].sort().join(',');
  const fullKeys = [...new Set(ALL.map(d => d.partid))].sort().join(',');
  if (allKeys !== fullKeys) params.set('parties', [...activeParties].sort().join(','));
  if (viewMode !== 'circles') params.set('view', viewMode);
  const qs = params.toString();
  history.replaceState(null, '', qs ? '?' + qs : location.pathname);
}
```

### Read state on load

Called inside `load()` after `ALL` and `PARTIES` are populated, before first `render()`:

```javascript
function applyURLState() {
  const params = new URLSearchParams(location.search);
  if (params.has('metric')) {
    const m = params.get('metric');
    if (COLUMNS.some(c => c.key === m)) {
      metric = m;
      // Update active metric button
      document.querySelectorAll('.metric-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.metric === metric));
    }
  }
  if (params.has('parties')) {
    const requested = new Set(params.get('parties').split(',').filter(Boolean));
    activeParties = new Set([...requested].filter(p => ALL.some(d => d.partid === p)));
  }
  if (params.get('view') === 'table') {
    viewMode = 'table';
    document.getElementById('btn-table').classList.add('active');
    document.getElementById('btn-circles').classList.remove('active');
    document.getElementById('metric-btns').style.display = 'none';
  }
}
```

---

## 3. OG Meta Tags

### Tags added to each page

```html
<meta name="description" content="{page description}">
<meta property="og:type" content="website">
<meta property="og:title" content="{page title}">
<meta property="og:description" content="{page description}">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/{page}.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/{page}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

### Pages and their descriptions

| Page | og:title | og:description |
|---|---|---|
| `deputati-avere.html` | Averi deputați — vizualizare | Fiecare deputat ca un cerc: avere declarată, venituri, imobile, datorii · Camera Deputaților 2024 |
| `deputati-activitate.html` | Activitate parlamentară — vizualizare | Fiecare deputat ca un cerc: prezență, propuneri legislative, interpelări · Camera Deputaților 2024 |
| `avere.html` | Averi deputați — statistici | Top averi, venituri și datorii declarate · comparații pe partide · Camera Deputaților 2024 |
| `interpelari-stats.html` | Interpelări — statistici | Statistici interpelări adresate deputaților · Camera Deputaților 2024 |
| `proiecte-stats.html` | Proiecte legislative — statistici | Statistici proiecte legislative · Camera Deputaților 2024 |
| `index.html` | cdep-api stats | Date deschise despre Camera Deputaților: avere, activitate, interpelări, proiecte · 2024 |

### Screenshot script (`scripts/generate_og.py`)

```python
#!/usr/bin/env python3
"""Generate OG screenshot images for all main pages.

Usage:
    python scripts/generate_og.py

Requires: pip install playwright && playwright install chromium
Output:  data/assets/og/{page}.png  (1200×630 px)
"""
import subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "data" / "assets" / "og"
PORT = 9998

PAGES = [
    ("deputati-avere",      "deputati-avere.html",      ".dep-item"),
    ("deputati-activitate", "deputati-activitate.html", ".dep-item"),
    ("avere",               "avere.html",               ".section"),
    ("interpelari-stats",   "interpelari-stats.html",   ".section"),
    ("proiecte-stats",      "proiecte-stats.html",      ".section"),
    ("index",               "index.html",               "body"),
]

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1.5)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport={"width": 1200, "height": 630})
            for name, path, selector in PAGES:
                url = f"http://localhost:{PORT}/{path}"
                print(f"  {url} → {name}.png", end=" ", flush=True)
                page.goto(url, wait_until="networkidle")
                page.wait_for_selector(selector, timeout=15_000)
                out = OUT / f"{name}.png"
                page.screenshot(path=str(out), clip={"x":0,"y":0,"width":1200,"height":630})
                print("✓")
            browser.close()
    finally:
        server.terminate()
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

`playwright` added to `requirements-dev.txt`.

---

## Scope

**In scope:**
- `deputati-avere.html` and `deputati-activitate.html`: toolbar redesign + URL state
- All 6 main pages: OG meta tags + screenshot assets
- `scripts/generate_og.py` + `requirements-dev.txt`

**Out of scope:**
- i18n keys for new metric button labels (hardcode Romanian for now)
- Search functionality (removed entirely — no hidden input kept)
- OG for legislatura 2020 pages (use 2024 screenshots for both)

---

## Verification

1. Open `deputati-avere.html` — toolbar shows metric buttons, no search, year at right
2. Click a metric button — active state highlights blue, circles re-sort
3. Click `Partide ▾` — dropdown opens with checkboxes; uncheck a party — circles update, button shows `(N/total)`; click outside — dropdown closes
4. Click `≡ Tabel` — metric buttons hidden, table renders
5. Reload page after navigating — URL params restored, same state
6. Open `?metric=datorii_ron&parties=AUR&view=table` — page loads in that exact state
7. Mobile 375px — metric buttons wrap as individual pills
8. Run `python scripts/generate_og.py` — 6 PNG files created in `data/assets/og/`
9. Open any page — view-source confirms OG tags present with correct image path
