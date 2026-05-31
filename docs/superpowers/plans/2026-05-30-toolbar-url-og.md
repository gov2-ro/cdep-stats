# Toolbar Redesign + URL State + OG Meta — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the metric `<select>` + party chips + search with metric buttons + party dropdown on both viz pages, add URL state persistence (`?metric=…&parties=…&view=…`), and add OG meta tags + screenshot script for all 6 main pages.

**Architecture:** All changes are inline in self-contained HTML files. Each page gets: new toolbar HTML, CSS additions, updated JS functions (`buildPartyDropdown`, `pushState`, `applyURLState`). OG tags are added directly to each page's `<head>`. A new `scripts/generate_og.py` screenshots all 6 pages with Playwright.

**Tech Stack:** Vanilla JS, inline CSS, Python + Playwright (OG script only).

---

## File Map

| File | Change |
|---|---|
| `deputati-avere.html` | CSS + toolbar HTML + JS: metric btns, party dropdown, remove search, URL state |
| `deputati-activitate.html` | Same changes |
| `avere.html` | Add OG meta tags |
| `interpelari-stats.html` | Add OG meta tags |
| `proiecte-stats.html` | Add OG meta tags |
| `index.html` | Update/complete existing partial OG meta tags |
| `deputati-avere.html` | Add OG meta tags (same task as above) |
| `deputati-activitate.html` | Add OG meta tags (same task as above) |
| `scripts/generate_og.py` | New: Playwright screenshot script |
| `requirements-dev.txt` | Add `playwright` |
| `docs/activity-log.md` | New entry |

---

### Task 1: `deputati-avere.html` — toolbar redesign + URL state

**Files:**
- Modify: `deputati-avere.html`

No unit tests — verification is browser-based (Step 10).

- [ ] **Step 1: Add CSS for metric buttons and party dropdown**

Find the line `.dep-table .null-val{color:var(--text3);font-style:italic;font-size:11px}` (the last CSS line before `</style>`) and insert these rules after it, just before `</style>`:

```css
/* Metric buttons */
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

@media(max-width:600px){
  .metric-btns{flex-wrap:wrap;gap:4px;border:none}
  .metric-btn{border-radius:var(--radius-sm);border:1px solid var(--border2)}
}
```

- [ ] **Step 2: Replace toolbar HTML**

Find and replace the entire toolbar-inner div. Old:

```html
  <div class="toolbar-inner">
    <div class="view-toggle" id="leg-toggle"></div>
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
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
    <input class="search-input" id="search-input" type="text" placeholder="Caută deputat…"
           data-i18n-attr="placeholder:search_deputies">
    <span class="count-badge" id="count-badge"></span>
  </div>
```

New:

```html
  <div class="toolbar-inner">
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
    </div>
    <div class="metric-btns" id="metric-btns">
      <button class="metric-btn active" data-metric="venituri_ron">Venituri</button>
      <button class="metric-btn" data-metric="conturi_ron">Conturi</button>
      <button class="metric-btn" data-metric="imobile_count">Imobile</button>
      <button class="metric-btn" data-metric="suprafata_mp">Suprafață</button>
      <button class="metric-btn" data-metric="auto_count">Auto</button>
      <button class="metric-btn" data-metric="datorii_ron">Datorii</button>
    </div>
    <div class="party-dd" id="party-dd">
      <button class="party-dd-btn" id="party-dd-btn">Partide <span id="party-dd-count"></span> ▾</button>
      <div class="party-dd-pop" id="party-dd-pop">
        <div class="party-dd-hdr">
          <span id="party-dd-total"></span>
          <a onclick="selectAllParties()">Toate</a>
          <a onclick="selectNoParties()">Niciuna</a>
        </div>
      </div>
    </div>
    <span class="count-badge" id="count-badge"></span>
    <div class="view-toggle" id="leg-toggle"></div>
  </div>
```

- [ ] **Step 3: Remove `query` from state and simplify `filtered()`**

Find and replace:

```javascript
let ALL=[],PARTIES={},activeParties=new Set(),query='',metric='venituri_ron';
```

→

```javascript
let ALL=[],PARTIES={},activeParties=new Set(),metric='venituri_ron';
```

Then find and replace the `filtered()` function:

```javascript
function filtered(){
  return ALL.filter(d=>{
    if(!activeParties.has(d.partid))return false;
    if(query&&!d.name.toLowerCase().includes(query))return false;
    return true;
  });
}
```

→

```javascript
function filtered(){
  return ALL.filter(d=>activeParties.has(d.partid));
}
```

- [ ] **Step 4: Replace `buildChips` with `buildPartyDropdown`**

Find and replace the entire `buildChips` function:

```javascript
function buildChips(partids){
  const el=document.getElementById('party-chips');
  el.innerHTML=partids.map(p=>{
    const logo=PARTIES[p];
    const color=partyColor(p);
    const img=logo
      ?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" alt="">`
      :`<span style="width:10px;height:10px;border-radius:2px;background:${color};display:inline-block;flex-shrink:0"></span>`;
    return`<span class="party-chip" data-partid="${p}" onclick="toggleParty('${p}')">${img}${p}</span>`;
  }).join('');
}
```

→

```javascript
function buildPartyDropdown(partids){
  document.getElementById('party-dd-total').textContent=partids.length+' partide';
  const pop=document.getElementById('party-dd-pop');
  pop.querySelectorAll('.party-dd-row').forEach(r=>r.remove());
  partids.forEach(p=>{
    const color=partyColor(p);
    const logo=PARTIES[p];
    const count=ALL.filter(d=>d.partid===p).length;
    const row=document.createElement('div');
    row.className='party-dd-row';
    row.innerHTML=`<input type="checkbox" data-partid="${p}"${activeParties.has(p)?' checked':''}>`
      +(logo?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" style="width:14px;height:14px;object-fit:contain;flex-shrink:0">`:'')
      +`<span class="party-dd-dot" style="background:${color}"></span>`
      +`<span>${p}</span><span class="party-dd-count-label">${count} dep.</span>`;
    row.querySelector('input').addEventListener('change',()=>toggleParty(p));
    row.addEventListener('click',e=>{
      if(e.target.tagName!=='INPUT'){row.querySelector('input').click();}
    });
    pop.appendChild(row);
  });
  updatePartyDropdownBtn();
}
```

- [ ] **Step 5: Replace `toggleParty`, add helpers**

Find and replace the `toggleParty` function:

```javascript
function toggleParty(p){
  if(activeParties.has(p))activeParties.delete(p);
  else activeParties.add(p);
  document.querySelectorAll('.party-chip').forEach(el=>{
    el.classList.toggle('off',!activeParties.has(el.dataset.partid));
  });
  render();
}
```

→

```javascript
function updatePartyDropdownBtn(){
  const total=[...new Set(ALL.map(d=>d.partid))].length;
  const sel=activeParties.size;
  document.getElementById('party-dd-count').textContent=sel<total?`(${sel}/${total})`:'';
}

function toggleParty(p){
  if(activeParties.has(p))activeParties.delete(p);
  else activeParties.add(p);
  const cb=document.querySelector(`.party-dd-row input[data-partid="${p}"]`);
  if(cb)cb.checked=activeParties.has(p);
  updatePartyDropdownBtn();
  render();
  pushState();
}

function selectAllParties(){
  activeParties=new Set(ALL.map(d=>d.partid));
  document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{
    cb.checked=activeParties.has(cb.dataset.partid);
  });
  updatePartyDropdownBtn();
  render();
  pushState();
}

function selectNoParties(){
  activeParties=new Set();
  document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{cb.checked=false;});
  updatePartyDropdownBtn();
  render();
  pushState();
}
```

- [ ] **Step 6: Add `pushState` and `applyURLState` functions**

Insert these two functions immediately before `function render(){`:

```javascript
function pushState(){
  const params=new URLSearchParams();
  const leg=getParam('leg');
  if(leg&&leg!=='2024')params.set('leg',leg);
  if(metric!==COLUMNS[0].key)params.set('metric',metric);
  const allKeys=[...activeParties].sort().join(',');
  const fullKeys=[...new Set(ALL.map(d=>d.partid))].sort().join(',');
  if(allKeys!==fullKeys)params.set('parties',[...activeParties].sort().join(','));
  if(viewMode!=='circles')params.set('view',viewMode);
  const qs=params.toString();
  history.replaceState(null,'',qs?'?'+qs:location.pathname);
}

function applyURLState(){
  const params=new URLSearchParams(location.search);
  if(params.has('metric')){
    const m=params.get('metric');
    if(COLUMNS.some(c=>c.key===m)){
      metric=m;
      document.querySelectorAll('.metric-btn').forEach(b=>
        b.classList.toggle('active',b.dataset.metric===metric));
    }
  }
  if(params.has('parties')){
    const requested=new Set(params.get('parties').split(',').filter(Boolean));
    activeParties=new Set([...requested].filter(p=>ALL.some(d=>d.partid===p)));
    document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{
      cb.checked=activeParties.has(cb.dataset.partid);
    });
    updatePartyDropdownBtn();
  }
  if(params.get('view')==='table'){
    viewMode='table';
    document.getElementById('btn-table').classList.add('active');
    document.getElementById('btn-circles').classList.remove('active');
    document.getElementById('metric-btns').style.display='none';
    if(!sortKey)sortKey=metric;
  }
}

```

- [ ] **Step 7: Update `load()` — replace `buildChips` call, add `applyURLState`**

Find inside the `load()` try block:

```javascript
    buildChips(partids);
    render();
```

Replace with:

```javascript
    buildPartyDropdown(partids);
    applyURLState();
    render();
```

- [ ] **Step 8: Replace all event listeners at the bottom of the script**

Find and replace this entire block (from the metric-select listener through `load()`):

```javascript
document.getElementById('metric-select').addEventListener('change',e=>{
  metric=e.target.value;
  render();
});
document.getElementById('search-input').addEventListener('input',e=>{
  query=e.target.value.toLowerCase().trim();
  render();
});

document.getElementById('btn-circles').addEventListener('click',()=>{
  if(viewMode==='circles')return;
  viewMode='circles';
  document.getElementById('btn-circles').classList.add('active');
  document.getElementById('btn-table').classList.remove('active');
  document.getElementById('metric-select').style.display='';
  const metricKeys=COLUMNS.map(c=>c.key);
  if(sortKey&&metricKeys.includes(sortKey)){
    metric=sortKey;
    document.getElementById('metric-select').value=metric;
  }
  render();
});

document.getElementById('btn-table').addEventListener('click',()=>{
  if(viewMode==='table')return;
  viewMode='table';
  document.getElementById('btn-table').classList.add('active');
  document.getElementById('btn-circles').classList.remove('active');
  document.getElementById('metric-select').style.display='none';
  if(!sortKey)sortKey=metric;
  render();
});

document.getElementById('circle-grid').addEventListener('click',e=>{
  const th=e.target.closest('[data-sort]');
  if(!th)return;
  const key=th.dataset.sort;
  if(sortKey===key){
    if(sortDir==='desc')sortDir='asc';
    else{sortKey=null;sortDir='desc';}
  }else{sortKey=key;sortDir='desc';}
  render();
});

load();
```

→

```javascript
document.getElementById('metric-btns').addEventListener('click',e=>{
  const btn=e.target.closest('.metric-btn');
  if(!btn)return;
  metric=btn.dataset.metric;
  document.querySelectorAll('.metric-btn').forEach(b=>b.classList.toggle('active',b===btn));
  render();
  pushState();
});

document.getElementById('btn-circles').addEventListener('click',()=>{
  if(viewMode==='circles')return;
  viewMode='circles';
  document.getElementById('btn-circles').classList.add('active');
  document.getElementById('btn-table').classList.remove('active');
  document.getElementById('metric-btns').style.display='';
  const metricKeys=COLUMNS.map(c=>c.key);
  if(sortKey&&metricKeys.includes(sortKey)){
    metric=sortKey;
    document.querySelectorAll('.metric-btn').forEach(b=>
      b.classList.toggle('active',b.dataset.metric===metric));
  }
  render();
  pushState();
});

document.getElementById('btn-table').addEventListener('click',()=>{
  if(viewMode==='table')return;
  viewMode='table';
  document.getElementById('btn-table').classList.add('active');
  document.getElementById('btn-circles').classList.remove('active');
  document.getElementById('metric-btns').style.display='none';
  if(!sortKey)sortKey=metric;
  render();
  pushState();
});

document.getElementById('circle-grid').addEventListener('click',e=>{
  const th=e.target.closest('[data-sort]');
  if(!th)return;
  const key=th.dataset.sort;
  if(sortKey===key){
    if(sortDir==='desc')sortDir='asc';
    else{sortKey=null;sortDir='desc';}
  }else{sortKey=key;sortDir='desc';}
  render();
});

document.getElementById('party-dd-btn').addEventListener('click',e=>{
  e.stopPropagation();
  document.getElementById('party-dd-pop').classList.toggle('open');
});
document.addEventListener('click',e=>{
  if(!document.getElementById('party-dd').contains(e.target)){
    document.getElementById('party-dd-pop').classList.remove('open');
  }
});

load();
```

- [ ] **Step 9: Commit**

```bash
git add deputati-avere.html
git commit -m "feat(avere): toolbar redesign — metric buttons, party dropdown, URL state"
```

- [ ] **Step 10: Verify in browser**

```bash
python -m http.server 8000
```

Open `http://localhost:8000/deputati-avere.html`:
- Toolbar shows: `[⬤ Cercuri | ≡ Tabel]  [Venituri|Conturi|Imobile|Suprafață|Auto|Datorii]  [Partide ▾]  N dep.  [2024|2020]`
- No search input visible
- Click `Datorii` button — it highlights blue, circles re-sort by datorii
- URL changes to `?metric=datorii_ron`
- Click `Partide ▾` — dropdown opens with checkboxes and party color dots
- Uncheck `AUR` — circles update, button shows `(N/total)`, URL gains `?parties=...`
- Click outside dropdown — it closes
- Click `Toate` — all parties re-selected, badge clears
- Click `Niciuna` — zero deputies shown
- Click `≡ Tabel` — metric buttons disappear, table renders, URL gains `?view=table`
- Reload `?metric=datorii_ron&parties=AUR,PSD&view=table` — page loads in that exact state
- Mobile 375px — metric buttons wrap as individual pills
- Year toggle is at far right

Kill server with Ctrl+C.

---

### Task 2: `deputati-activitate.html` — toolbar redesign + URL state

**Files:**
- Modify: `deputati-activitate.html`

Same pattern as Task 1. Differences: COLUMNS uses `activitate_*` keys and `fmtVal(v)` with no metric arg; first metric key is `activitate_sedinte`.

- [ ] **Step 1: Add CSS for metric buttons and party dropdown**

Find the line `.dep-table .null-val{color:var(--text3);font-style:italic;font-size:11px}` (last CSS before `</style>`) and insert these rules after it, before `</style>`:

```css
/* Metric buttons */
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

@media(max-width:600px){
  .metric-btns{flex-wrap:wrap;gap:4px;border:none}
  .metric-btn{border-radius:var(--radius-sm);border:1px solid var(--border2)}
}
```

- [ ] **Step 2: Replace toolbar HTML**

Find and replace the entire toolbar-inner div. Old:

```html
  <div class="toolbar-inner">
    <div class="view-toggle" id="leg-toggle"></div>
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
    </div>
    <select class="metric-select" id="metric-select">
      <option value="activitate_sedinte">Ședințe (prezență)</option>
      <option value="activitate_luari_cuvant">Luări de cuvânt</option>
      <option value="activitate_propuneri_legislative">Propuneri legislative</option>
      <option value="activitate_legi_promulgate">Legi promulgate</option>
      <option value="activitate_declaratii_politice">Declarații politice</option>
      <option value="activitate_intrebari_interpelari">Întrebări / interpelări</option>
    </select>
    <div class="party-chips" id="party-chips"></div>
    <input class="search-input" id="search-input" type="text" placeholder="Caută deputat…"
           data-i18n-attr="placeholder:search_deputies">
    <span class="count-badge" id="count-badge"></span>
  </div>
```

New:

```html
  <div class="toolbar-inner">
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
    </div>
    <div class="metric-btns" id="metric-btns">
      <button class="metric-btn active" data-metric="activitate_sedinte">Ședințe</button>
      <button class="metric-btn" data-metric="activitate_luari_cuvant">Cuvânt</button>
      <button class="metric-btn" data-metric="activitate_propuneri_legislative">Propuneri</button>
      <button class="metric-btn" data-metric="activitate_legi_promulgate">Legi</button>
      <button class="metric-btn" data-metric="activitate_declaratii_politice">Declarații</button>
      <button class="metric-btn" data-metric="activitate_intrebari_interpelari">Întrebări</button>
    </div>
    <div class="party-dd" id="party-dd">
      <button class="party-dd-btn" id="party-dd-btn">Partide <span id="party-dd-count"></span> ▾</button>
      <div class="party-dd-pop" id="party-dd-pop">
        <div class="party-dd-hdr">
          <span id="party-dd-total"></span>
          <a onclick="selectAllParties()">Toate</a>
          <a onclick="selectNoParties()">Niciuna</a>
        </div>
      </div>
    </div>
    <span class="count-badge" id="count-badge"></span>
    <div class="view-toggle" id="leg-toggle"></div>
  </div>
```

- [ ] **Step 3: Remove `query` from state and simplify `filtered()`**

Find and replace:

```javascript
let ALL=[],PARTIES={},activeParties=new Set(),query='',metric='activitate_sedinte';
```

→

```javascript
let ALL=[],PARTIES={},activeParties=new Set(),metric='activitate_sedinte';
```

Then find and replace:

```javascript
function filtered(){
  return ALL.filter(d=>activeParties.has(d.partid)&&(!query||d.name.toLowerCase().includes(query)));
}
```

→

```javascript
function filtered(){
  return ALL.filter(d=>activeParties.has(d.partid));
}
```

- [ ] **Step 4: Replace `buildChips` with `buildPartyDropdown`**

Find and replace:

```javascript
function buildChips(partids){
  document.getElementById('party-chips').innerHTML=partids.map(p=>{
    const logo=PARTIES[p],color=partyColor(p);
    const img=logo
      ?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" alt="">`
      :`<span style="width:10px;height:10px;border-radius:2px;background:${color};display:inline-block;flex-shrink:0"></span>`;
    return`<span class="party-chip" data-partid="${p}" onclick="toggleParty('${p}')">${img}${p}</span>`;
  }).join('');
}
```

→

```javascript
function buildPartyDropdown(partids){
  document.getElementById('party-dd-total').textContent=partids.length+' partide';
  const pop=document.getElementById('party-dd-pop');
  pop.querySelectorAll('.party-dd-row').forEach(r=>r.remove());
  partids.forEach(p=>{
    const color=partyColor(p);
    const logo=PARTIES[p];
    const count=ALL.filter(d=>d.partid===p).length;
    const row=document.createElement('div');
    row.className='party-dd-row';
    row.innerHTML=`<input type="checkbox" data-partid="${p}"${activeParties.has(p)?' checked':''}>`
      +(logo?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" style="width:14px;height:14px;object-fit:contain;flex-shrink:0">`:'')
      +`<span class="party-dd-dot" style="background:${color}"></span>`
      +`<span>${p}</span><span class="party-dd-count-label">${count} dep.</span>`;
    row.querySelector('input').addEventListener('change',()=>toggleParty(p));
    row.addEventListener('click',e=>{
      if(e.target.tagName!=='INPUT'){row.querySelector('input').click();}
    });
    pop.appendChild(row);
  });
  updatePartyDropdownBtn();
}
```

- [ ] **Step 5: Replace `toggleParty`, add helpers**

Find and replace:

```javascript
function toggleParty(p){
  if(activeParties.has(p))activeParties.delete(p); else activeParties.add(p);
  document.querySelectorAll('.party-chip').forEach(el=>el.classList.toggle('off',!activeParties.has(el.dataset.partid)));
  render();
}
```

→

```javascript
function updatePartyDropdownBtn(){
  const total=[...new Set(ALL.map(d=>d.partid))].length;
  const sel=activeParties.size;
  document.getElementById('party-dd-count').textContent=sel<total?`(${sel}/${total})`:'';
}

function toggleParty(p){
  if(activeParties.has(p))activeParties.delete(p);
  else activeParties.add(p);
  const cb=document.querySelector(`.party-dd-row input[data-partid="${p}"]`);
  if(cb)cb.checked=activeParties.has(p);
  updatePartyDropdownBtn();
  render();
  pushState();
}

function selectAllParties(){
  activeParties=new Set(ALL.map(d=>d.partid));
  document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{
    cb.checked=activeParties.has(cb.dataset.partid);
  });
  updatePartyDropdownBtn();
  render();
  pushState();
}

function selectNoParties(){
  activeParties=new Set();
  document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{cb.checked=false;});
  updatePartyDropdownBtn();
  render();
  pushState();
}
```

- [ ] **Step 6: Add `pushState` and `applyURLState` before `render()`**

Insert these two functions immediately before `function render(){`:

```javascript
function pushState(){
  const params=new URLSearchParams();
  const leg=getParam('leg');
  if(leg&&leg!=='2024')params.set('leg',leg);
  if(metric!==COLUMNS[0].key)params.set('metric',metric);
  const allKeys=[...activeParties].sort().join(',');
  const fullKeys=[...new Set(ALL.map(d=>d.partid))].sort().join(',');
  if(allKeys!==fullKeys)params.set('parties',[...activeParties].sort().join(','));
  if(viewMode!=='circles')params.set('view',viewMode);
  const qs=params.toString();
  history.replaceState(null,'',qs?'?'+qs:location.pathname);
}

function applyURLState(){
  const params=new URLSearchParams(location.search);
  if(params.has('metric')){
    const m=params.get('metric');
    if(COLUMNS.some(c=>c.key===m)){
      metric=m;
      document.querySelectorAll('.metric-btn').forEach(b=>
        b.classList.toggle('active',b.dataset.metric===metric));
    }
  }
  if(params.has('parties')){
    const requested=new Set(params.get('parties').split(',').filter(Boolean));
    activeParties=new Set([...requested].filter(p=>ALL.some(d=>d.partid===p)));
    document.querySelectorAll('.party-dd-row input[type=checkbox]').forEach(cb=>{
      cb.checked=activeParties.has(cb.dataset.partid);
    });
    updatePartyDropdownBtn();
  }
  if(params.get('view')==='table'){
    viewMode='table';
    document.getElementById('btn-table').classList.add('active');
    document.getElementById('btn-circles').classList.remove('active');
    document.getElementById('metric-btns').style.display='none';
    if(!sortKey)sortKey=metric;
  }
}

```

- [ ] **Step 7: Update `load()` — replace `buildChips` call, add `applyURLState`**

Find inside the `load()` try block:

```javascript
    buildChips(partids);
    render();
```

Replace with:

```javascript
    buildPartyDropdown(partids);
    applyURLState();
    render();
```

- [ ] **Step 8: Replace all event listeners**

Find and replace from the metric-select listener through `load()`:

```javascript
document.getElementById('metric-select').addEventListener('change',e=>{metric=e.target.value;render();});
document.getElementById('search-input').addEventListener('input',e=>{query=e.target.value.toLowerCase().trim();render();});

document.getElementById('btn-circles').addEventListener('click',()=>{
  if(viewMode==='circles')return;
  viewMode='circles';
  document.getElementById('btn-circles').classList.add('active');
  document.getElementById('btn-table').classList.remove('active');
  document.getElementById('metric-select').style.display='';
  const metricKeys=COLUMNS.map(c=>c.key);
  if(sortKey&&metricKeys.includes(sortKey)){
    metric=sortKey;
    document.getElementById('metric-select').value=metric;
  }
  render();
});

document.getElementById('btn-table').addEventListener('click',()=>{
  if(viewMode==='table')return;
  viewMode='table';
  document.getElementById('btn-table').classList.add('active');
  document.getElementById('btn-circles').classList.remove('active');
  document.getElementById('metric-select').style.display='none';
  if(!sortKey)sortKey=metric;
  render();
});

document.getElementById('circle-grid').addEventListener('click',e=>{
  const th=e.target.closest('[data-sort]');
  if(!th)return;
  const key=th.dataset.sort;
  if(sortKey===key){
    if(sortDir==='desc')sortDir='asc';
    else{sortKey=null;sortDir='desc';}
  }else{sortKey=key;sortDir='desc';}
  render();
});

load();
```

→

```javascript
document.getElementById('metric-btns').addEventListener('click',e=>{
  const btn=e.target.closest('.metric-btn');
  if(!btn)return;
  metric=btn.dataset.metric;
  document.querySelectorAll('.metric-btn').forEach(b=>b.classList.toggle('active',b===btn));
  render();
  pushState();
});

document.getElementById('btn-circles').addEventListener('click',()=>{
  if(viewMode==='circles')return;
  viewMode='circles';
  document.getElementById('btn-circles').classList.add('active');
  document.getElementById('btn-table').classList.remove('active');
  document.getElementById('metric-btns').style.display='';
  const metricKeys=COLUMNS.map(c=>c.key);
  if(sortKey&&metricKeys.includes(sortKey)){
    metric=sortKey;
    document.querySelectorAll('.metric-btn').forEach(b=>
      b.classList.toggle('active',b.dataset.metric===metric));
  }
  render();
  pushState();
});

document.getElementById('btn-table').addEventListener('click',()=>{
  if(viewMode==='table')return;
  viewMode='table';
  document.getElementById('btn-table').classList.add('active');
  document.getElementById('btn-circles').classList.remove('active');
  document.getElementById('metric-btns').style.display='none';
  if(!sortKey)sortKey=metric;
  render();
  pushState();
});

document.getElementById('circle-grid').addEventListener('click',e=>{
  const th=e.target.closest('[data-sort]');
  if(!th)return;
  const key=th.dataset.sort;
  if(sortKey===key){
    if(sortDir==='desc')sortDir='asc';
    else{sortKey=null;sortDir='desc';}
  }else{sortKey=key;sortDir='desc';}
  render();
});

document.getElementById('party-dd-btn').addEventListener('click',e=>{
  e.stopPropagation();
  document.getElementById('party-dd-pop').classList.toggle('open');
});
document.addEventListener('click',e=>{
  if(!document.getElementById('party-dd').contains(e.target)){
    document.getElementById('party-dd-pop').classList.remove('open');
  }
});

load();
```

- [ ] **Step 9: Commit**

```bash
git add deputati-activitate.html
git commit -m "feat(activitate): toolbar redesign — metric buttons, party dropdown, URL state"
```

- [ ] **Step 10: Verify in browser**

```bash
python -m http.server 8000
```

Open `http://localhost:8000/deputati-activitate.html`:
- Toolbar: `[⬤ Cercuri | ≡ Tabel]  [Ședințe|Cuvânt|Propuneri|Legi|Declarații|Întrebări]  [Partide ▾]  N dep.  [2024|2020]`
- No search input visible
- Click `Întrebări` — active blue, circles re-sort
- URL: `?metric=activitate_intrebari_interpelari`
- Party dropdown open/close/filter works same as avere
- `≡ Tabel` hides metric btns, shows table
- `?metric=activitate_legi_promulgate&parties=USR&view=table` loads in that state
- Mobile 375px: metric buttons wrap as pills

Kill server.

---

### Task 3: OG meta tags for all 6 pages

**Files:**
- Modify: `deputati-avere.html`, `deputati-activitate.html`, `avere.html`, `interpelari-stats.html`, `proiecte-stats.html`, `index.html`

No tests — verification is view-source after changes.

- [ ] **Step 1: Add OG tags to `deputati-avere.html`**

Find and replace the existing description meta:

```html
<meta name="description" content="Fiecare deputat ca un cerc — mărimea proporțională cu averea declarată. Filtrare pe partid și metrică.">
```

→

```html
<meta name="description" content="Fiecare deputat ca un cerc: avere declarată, venituri, imobile, datorii · Camera Deputaților 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="Averi deputați — vizualizare">
<meta property="og:description" content="Fiecare deputat ca un cerc: avere declarată, venituri, imobile, datorii · Camera Deputaților 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/deputati-avere.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/deputati-avere.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 2: Add OG tags to `deputati-activitate.html`**

Find and replace:

```html
<meta name="description" content="Fiecare deputat ca un cerc — mărimea proporțională cu activitatea parlamentară selectată.">
```

→

```html
<meta name="description" content="Fiecare deputat ca un cerc: prezență, propuneri legislative, interpelări · Camera Deputaților 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="Activitate parlamentară — vizualizare">
<meta property="og:description" content="Fiecare deputat ca un cerc: prezență, propuneri legislative, interpelări · Camera Deputaților 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/deputati-activitate.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/deputati-activitate.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 3: Add OG tags to `avere.html`**

Find and replace the existing description meta (line 7):

```html
<meta name="description" content="Dashboard averi deputați: top conturi, venituri, datorii, imobile, evoluție în mandat, comparație pe partide. Date din declarațiile ANI.">
```

→

```html
<meta name="description" content="Top averi, venituri și datorii declarate · comparații pe partide · Camera Deputaților 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="Averi deputați — statistici">
<meta property="og:description" content="Top averi, venituri și datorii declarate · comparații pe partide · Camera Deputaților 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/avere.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/avere.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 4: Add OG tags to `interpelari-stats.html`**

Find and replace:

```html
<meta name="description" content="Statistici interpelări: cine întreabă cel mai mult, care ministere primesc cele mai multe întrebări, rata de răspuns.">
```

→

```html
<meta name="description" content="Statistici interpelări adresate deputaților · Camera Deputaților 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="Interpelări — statistici">
<meta property="og:description" content="Statistici interpelări adresate deputaților · Camera Deputaților 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/interpelari-stats.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/interpelari-stats.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 5: Add OG tags to `proiecte-stats.html`**

Find and replace:

```html
<meta name="description" content="Statistici proiecte legislative: câte au fost promulgate, rata de succes pe partid, evoluție lunară.">
```

→

```html
<meta name="description" content="Statistici proiecte legislative · Camera Deputaților 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="Proiecte legislative — statistici">
<meta property="og:description" content="Statistici proiecte legislative · Camera Deputaților 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/proiecte-stats.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/proiecte-stats.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 6: Update OG tags on `index.html`**

`index.html` already has partial OG tags. Find and replace them (lines 7–12):

```html
<meta name="description" content="API REST public pentru date parlamentare: voturi, proiecte legislative, interpelări, moțiuni, comisii. JSON structurat din cdep.ro.">
<meta property="og:title" content="Camera Deputaților — API Deschis">
<meta property="og:description" content="API REST public pentru date parlamentare. JSON structurat, accesibil oricui.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/">
<meta name="twitter:card" content="summary">
```

→

```html
<meta name="description" content="Date deschise despre Camera Deputaților: avere, activitate, interpelări, proiecte · 2024">
<meta property="og:type" content="website">
<meta property="og:title" content="cdep-api stats">
<meta property="og:description" content="Date deschise despre Camera Deputaților: avere, activitate, interpelări, proiecte · 2024">
<meta property="og:url" content="https://endimion2k.github.io/cdep-api-poc/index.html">
<meta property="og:image" content="https://endimion2k.github.io/cdep-api-poc/data/assets/og/index.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

- [ ] **Step 7: Commit**

```bash
git add deputati-avere.html deputati-activitate.html avere.html interpelari-stats.html proiecte-stats.html index.html
git commit -m "feat(og): add OG meta tags to all 6 main pages"
```

- [ ] **Step 8: Quick verify**

```bash
grep -n "og:image" deputati-avere.html deputati-activitate.html avere.html interpelari-stats.html proiecte-stats.html index.html
```

Expected: each file shows its correct `og:image` URL ending in the page's name.

---

### Task 4: `scripts/generate_og.py` + `requirements-dev.txt`

**Files:**
- Create: `scripts/generate_og.py`
- Modify: `requirements-dev.txt`

- [ ] **Step 1: Create `scripts/generate_og.py`**

```python
#!/usr/bin/env python3
"""Generate OG screenshot images for all main pages.

Usage:
    python scripts/generate_og.py

Requires: pip install playwright && playwright install chromium
Output:  data/assets/og/{page}.png  (1200×630 px)
"""
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "assets" / "og"
PORT = 9998

PAGES = [
    ("deputati-avere", "deputati-avere.html", ".dep-item"),
    ("deputati-activitate", "deputati-activitate.html", ".dep-item"),
    ("avere", "avere.html", ".section"),
    ("interpelari-stats", "interpelari-stats.html", ".section"),
    ("proiecte-stats", "proiecte-stats.html", ".section"),
    ("index", "index.html", "body"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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
                page.screenshot(
                    path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 630}
                )
                print("✓")
            browser.close()
    finally:
        server.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Add `playwright` to `requirements-dev.txt`**

Find and replace the last line of `requirements-dev.txt`:

```
types-python-dateutil==2.9.0.20241003
```

→

```
types-python-dateutil==2.9.0.20241003

# OG screenshot generation
playwright>=1.44
```

- [ ] **Step 3: Commit**

```bash
git add scripts/generate_og.py requirements-dev.txt
git commit -m "feat(og): add Playwright screenshot script for OG images"
```

- [ ] **Step 4: Verify script runs (optional — requires network for cdep.ro data)**

If local data is available:

```bash
pip install playwright && playwright install chromium
PYTHONPATH=. python scripts/generate_og.py
ls -la data/assets/og/
```

Expected: 6 PNG files ~1200×630 px each.

---

### Task 5: Activity log

**Files:**
- Modify: `docs/activity-log.md`

- [ ] **Step 1: Add entry**

In `docs/activity-log.md`, add a new `### 2026-05-30 — ...` entry under the most recent section heading:

```markdown
### 2026-05-30 — Toolbar redesign, URL state, OG meta tags

**What was done**
- Replaced `<select id="metric-select">` with a connected segmented button strip (`.metric-btns`) on both `deputati-avere.html` and `deputati-activitate.html`. Active metric highlights blue; on mobile (≤600px) buttons wrap as individual pills.
- Replaced party-chips inline display with a compact `[Partide ▾]` dropdown (`.party-dd`): shows party color dot, logo, name, deputy count, checkbox per row. Button label updates to `(N/total)` when filtered. Closes on outside click.
- Removed search input and `query` state from both pages entirely.
- Moved year toggle to far right of toolbar via DOM reorder (count badge keeps `margin-left:auto`).
- Added `pushState()` / `applyURLState()` to both pages: params `metric`, `parties`, `view` persisted via `history.replaceState`. `leg` param carried forward if non-default.
- Added OG meta tags (`og:title`, `og:description`, `og:url`, `og:image` 1200×630, `twitter:card: summary_large_image`) to all 6 main pages. Updated existing partial tags on `index.html`.
- Added `scripts/generate_og.py`: starts a local HTTP server, screenshots all 6 pages at 1200×630 with Playwright, saves to `data/assets/og/`.

**Decisions**
- `pushState` preserves `?leg=` param so leg-2020 URLs remain stable across metric/party changes.
- OG image paths use the GitHub Pages base URL; screenshots need to be committed to `data/assets/og/` for them to resolve.
- Search removed completely — no hidden input kept, per spec.
```

- [ ] **Step 2: Commit**

```bash
git add docs/activity-log.md
git commit -m "docs: activity log for toolbar redesign, URL state, OG meta"
```
