# Sortable Table View — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sortable table view (inline bars per cell, sticky name column) to `deputati-avere.html` and `deputati-activitate.html`, toggled via a `⬤ Cercuri | ≡ Tabel` button in each toolbar.

**Architecture:** Each page gets identical CSS classes and a `renderTable()` function that reads the same module-level state already used by the circle renderer (`filtered()`, `PARTIES`, `LEG`). A new `COLUMNS` constant defines per-page column metadata (key, label, format function, debt flag). The existing `render()` function gains a `viewMode` branch — circles path unchanged, table path calls `renderTable()`. No shared files; both pages are self-contained.

**Tech Stack:** Vanilla JS, inline `<style>` CSS, no new dependencies, no build step.

---

## File Map

| File | Change |
|---|---|
| `deputati-avere.html` | Add CSS; add `COLUMNS`, `viewMode`, `sortKey`, `sortDir` state; add `renderTable()`; modify `render()`; enable + relabel view toggle; wire event handlers |
| `deputati-activitate.html` | Same pattern + add view toggle to toolbar |
| `docs/activity-log.md` | New entry |

---

### Task 1: `deputati-avere.html` — table view

**Files:**
- Modify: `deputati-avere.html`

No unit tests — verification is browser-based (Step 6).

- [ ] **Step 1: Add CSS inside the `<style>` block**

Find the closing `</style>` tag (line 76) and insert these rules just before it:

```css
.dep-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dep-table{width:100%;border-collapse:collapse;font-size:12px;min-width:680px}
.dep-table thead th{padding:9px 10px;background:var(--bg2);border-bottom:2px solid var(--border);font-weight:500;color:var(--text3);cursor:pointer;white-space:nowrap;user-select:none;text-align:left}
.dep-table thead th.sort-active{color:var(--blue);border-bottom-color:var(--blue)}
.dep-table thead th.sort-name{cursor:default;min-width:160px;position:sticky;left:0;z-index:1;background:var(--bg2)}
.dep-table tbody tr{border-bottom:1px solid var(--border);cursor:pointer}
.dep-table tbody tr:hover{background:var(--bg2)}
.dep-table tbody td{padding:6px 10px;vertical-align:middle}
.dep-table td.td-name{position:sticky;left:0;background:var(--bg);white-space:nowrap;z-index:1}
.dep-table tbody tr:hover td.td-name{background:var(--bg2)}
.bar-cell-val{font-size:11px;margin-bottom:3px;font-variant-numeric:tabular-nums}
.bar-cell-track{height:3px;background:var(--bg3);border-radius:2px;width:80px}
.bar-cell-fill{height:100%;border-radius:2px;opacity:0.75}
.dep-table .null-val{color:var(--text3);font-style:italic;font-size:11px}
```

- [ ] **Step 2: Enable the view toggle in the HTML**

Find lines 98–101 (the existing view-toggle div):
```html
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles" data-i18n="view_circles">Cercuri</button>
      <button class="view-btn" id="btn-list" disabled data-i18n="view_list">Listă</button>
    </div>
```

Replace with:
```html
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
    </div>
```

Changes: remove `disabled` from list button, rename `id="btn-list"` → `id="btn-table"`, update labels, remove `data-i18n` attrs (these buttons are visual controls, not text content).

- [ ] **Step 3: Add state variables and COLUMNS constant**

Find line 212 in the `<script>` block:
```javascript
let ALL=[],PARTIES={},activeParties=new Set(),query='',metric='venituri_ron';
```

Add these lines immediately after it:
```javascript
let viewMode='circles', sortKey=null, sortDir='desc';

const COLUMNS=[
  {key:'venituri_ron',  label:'Venituri',  fmt:v=>fmtVal(v,'venituri_ron'),  isDebt:false},
  {key:'conturi_ron',   label:'Conturi',   fmt:v=>fmtVal(v,'conturi_ron'),   isDebt:false},
  {key:'imobile_count', label:'Imobile',   fmt:v=>String(v),                 isDebt:false},
  {key:'suprafata_mp',  label:'Suprafață', fmt:v=>fmtVal(v,'suprafata_mp'),  isDebt:false},
  {key:'auto_count',    label:'Auto',      fmt:v=>String(v),                 isDebt:false},
  {key:'datorii_ron',   label:'Datorii',   fmt:v=>fmtVal(v,'datorii_ron'),   isDebt:true},
];
```

- [ ] **Step 4: Add `renderTable()` function**

Insert this function immediately before the existing `function render(){` (line 237):

```javascript
function renderTable(){
  const deps=filtered();
  if(!deps.length)return'<p style="color:var(--text3);padding:40px 0">Niciun deputat.</p>';

  const sk=sortKey||COLUMNS[0].key;
  const rows=[...deps].sort((a,b)=>{
    const av=a[sk]??null,bv=b[sk]??null;
    if(av===null&&bv===null)return 0;
    if(av===null)return 1;
    if(bv===null)return-1;
    return sortDir==='asc'?av-bv:bv-av;
  });

  const maxes=Object.fromEntries(COLUMNS.map(c=>[c.key,Math.max(0,...deps.map(d=>d[c.key]??0))]));

  const headers=COLUMNS.map(c=>{
    const active=c.key===sk;
    const arrow=active?(sortDir==='desc'?' ↓':' ↑'):'';
    return`<th class="dep-table-th${active?' sort-active':''}" data-sort="${c.key}" style="min-width:90px">${c.label}${arrow}</th>`;
  }).join('');

  const bodyRows=rows.map(d=>{
    const url=`deputat.html?id=${d.cdep_idm}&leg=${LEG}`;
    const color=partyColor(d.partid);
    const logo=PARTIES[d.partid];
    const ini=initials(d.name);
    const shortName=d.name.split(',')[0].trim();
    const photoHtml=d.image
      ?`<img src="${d.image}" alt="" onerror="this.style.display='none';this.nextSibling.style.display='flex'" style="width:28px;height:28px;border-radius:50%;object-fit:cover;flex-shrink:0"><div style="display:none;width:28px;height:28px;border-radius:50%;background:${color};align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`
      :`<div style="width:28px;height:28px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`;
    const badgeImg=logo?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" style="width:10px;height:10px;object-fit:contain;margin-right:2px;vertical-align:middle">`:'';

    const cells=COLUMNS.map(c=>{
      const v=d[c.key];
      const active=c.key===sk;
      if(v==null)return`<td class="dep-table-td"><span class="null-val">—</span></td>`;
      const mx=maxes[c.key];
      const barW=mx>0?Math.min(100,v/mx*100).toFixed(1):0;
      const valColor=active?'var(--blue)':(c.isDebt&&v>0?'var(--red-text)':'var(--text2)');
      const fillColor=active?'var(--blue)':(c.isDebt?'var(--red-text)':'var(--border2)');
      return`<td class="dep-table-td">
        <div class="bar-cell-val" style="color:${valColor}">${c.fmt(v)}</div>
        <div class="bar-cell-track"><div class="bar-cell-fill" style="width:${barW}%;background:${fillColor}"></div></div>
      </td>`;
    }).join('');

    return`<tr class="dep-table-row" onclick="location.href='${url}'">
      <td class="dep-table-td td-name">
        <div style="display:flex;align-items:center;gap:8px">
          ${photoHtml}
          <div>
            <div style="font-size:12px;color:var(--text);font-weight:500">${shortName}</div>
            <span style="font-size:10px;padding:1px 5px;border-radius:3px;background:${color}22;color:${color}">${badgeImg}${d.partid}</span>
          </div>
        </div>
      </td>${cells}
    </tr>`;
  }).join('');

  return`<div class="dep-table-wrap">
    <table class="dep-table">
      <thead><tr>
        <th class="dep-table-th sort-name">Deputat</th>${headers}
      </tr></thead>
      <tbody>${bodyRows}</tbody>
    </table>
  </div>`;
}
```

- [ ] **Step 5: Modify `render()` to dispatch on `viewMode`**

Find the existing `function render(){` and its first two lines:
```javascript
function render(){
  const deps=sorted(filtered());
  const grid=document.getElementById('circle-grid');
  const vals=deps.map(d=>d[metric]).filter(v=>v!=null&&v>0);
  const maxV=vals.length?Math.max(...vals):1;

  document.getElementById('count-badge').textContent=deps.length+' '+t('deputies_count');
```

Replace those opening lines (up to and including the count-badge line) with:
```javascript
function render(){
  const unfiltered=filtered();
  document.getElementById('count-badge').textContent=unfiltered.length+' '+t('deputies_count');
  const grid=document.getElementById('circle-grid');

  if(viewMode==='table'){grid.innerHTML=renderTable();return;}

  const deps=sorted(unfiltered);
  const vals=deps.map(d=>d[metric]).filter(v=>v!=null&&v>0);
  const maxV=vals.length?Math.max(...vals):1;
```

The rest of the circle-rendering code below (the `if(!deps.length)` block, the `parts` loop, `grid.innerHTML=parts.join('')`) stays **unchanged**.

- [ ] **Step 6: Wire toggle click handlers and sort delegation**

Find the block of event listeners near the bottom of the script (around line 356):
```javascript
document.getElementById('metric-select').addEventListener('change',e=>{
  metric=e.target.value;
  render();
});
document.getElementById('search-input').addEventListener('input',e=>{
  query=e.target.value.toLowerCase().trim();
  render();
});

load();
```

Insert the following between the search-input listener and `load()`:

```javascript
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
```

- [ ] **Step 7: Verify in browser**

```bash
python -m http.server 8000
```

Open `http://localhost:8000/deputati-avere.html`:
- Click `≡ Tabel`: metric dropdown disappears, table renders with all deputies
- Each column shows value + 3px bar; bars scale to column max
- Active sort column header is blue with `↓`
- Click same header: `↑` (ascending)
- Click again: resets to default sort (Venituri ↓)
- Type in search: rows filter, bar widths rescale
- Deselect a party chip: rows filter
- Click a row: navigates to `deputat.html?id=...`
- Click `⬤ Cercuri`: circles return, metric dropdown reappears
- Check dark mode: table and bars readable
- Check mobile 375px: horizontal scroll, name column stays fixed

Kill server with Ctrl+C after testing.

- [ ] **Step 8: Commit**

```bash
git add deputati-avere.html
git commit -m "feat(avere): add sortable table view with inline bars"
```

---

### Task 2: `deputati-activitate.html` — table view

**Files:**
- Modify: `deputati-activitate.html`

Same pattern as Task 1. Differences: (a) no existing view toggle → add it to HTML, (b) `fmtVal(v)` takes no metric arg, (c) no `isDebt` column, (d) no `null-val` cases (0 is valid data).

- [ ] **Step 1: Add CSS inside the `<style>` block**

Find the closing `</style>` tag (line 72) and insert the **exact same CSS block** as Task 1 Step 1 just before it:

```css
.dep-table-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}
.dep-table{width:100%;border-collapse:collapse;font-size:12px;min-width:680px}
.dep-table thead th{padding:9px 10px;background:var(--bg2);border-bottom:2px solid var(--border);font-weight:500;color:var(--text3);cursor:pointer;white-space:nowrap;user-select:none;text-align:left}
.dep-table thead th.sort-active{color:var(--blue);border-bottom-color:var(--blue)}
.dep-table thead th.sort-name{cursor:default;min-width:160px;position:sticky;left:0;z-index:1;background:var(--bg2)}
.dep-table tbody tr{border-bottom:1px solid var(--border);cursor:pointer}
.dep-table tbody tr:hover{background:var(--bg2)}
.dep-table tbody td{padding:6px 10px;vertical-align:middle}
.dep-table td.td-name{position:sticky;left:0;background:var(--bg);white-space:nowrap;z-index:1}
.dep-table tbody tr:hover td.td-name{background:var(--bg2)}
.bar-cell-val{font-size:11px;margin-bottom:3px;font-variant-numeric:tabular-nums}
.bar-cell-track{height:3px;background:var(--bg3);border-radius:2px;width:80px}
.bar-cell-fill{height:100%;border-radius:2px;opacity:0.75}
.dep-table .null-val{color:var(--text3);font-style:italic;font-size:11px}
```

- [ ] **Step 2: Add the view toggle to the toolbar HTML**

Find lines 93–94 (the toolbar, after the leg-toggle):
```html
    <div class="view-toggle" id="leg-toggle"></div>
    <select class="metric-select" id="metric-select">
```

Insert the view toggle between them:
```html
    <div class="view-toggle" id="leg-toggle"></div>
    <div class="view-toggle">
      <button class="view-btn active" id="btn-circles">⬤ Cercuri</button>
      <button class="view-btn" id="btn-table">≡ Tabel</button>
    </div>
    <select class="metric-select" id="metric-select">
```

- [ ] **Step 3: Add state variables and COLUMNS constant**

Find line 172:
```javascript
let ALL=[],PARTIES={},activeParties=new Set(),query='',metric='activitate_sedinte';
```

Add immediately after:
```javascript
let viewMode='circles', sortKey=null, sortDir='desc';

const COLUMNS=[
  {key:'activitate_sedinte',               label:'Ședințe',    fmt:v=>fmtVal(v), isDebt:false},
  {key:'activitate_luari_cuvant',          label:'Cuvânt',     fmt:v=>fmtVal(v), isDebt:false},
  {key:'activitate_propuneri_legislative', label:'Propuneri',  fmt:v=>fmtVal(v), isDebt:false},
  {key:'activitate_legi_promulgate',       label:'Legi',       fmt:v=>fmtVal(v), isDebt:false},
  {key:'activitate_declaratii_politice',   label:'Declarații', fmt:v=>fmtVal(v), isDebt:false},
  {key:'activitate_intrebari_interpelari', label:'Întrebări',  fmt:v=>fmtVal(v), isDebt:false},
];
```

- [ ] **Step 4: Add `renderTable()` function**

Insert this function immediately before the existing `function render(){` (line 181). It is identical to Task 1's `renderTable()` with one difference: activitate has no null values (deputies always have a record), so the `v==null` check still works correctly but will rarely fire.

```javascript
function renderTable(){
  const deps=filtered();
  if(!deps.length)return'<p style="color:var(--text3);padding:40px 0">Niciun deputat.</p>';

  const sk=sortKey||COLUMNS[0].key;
  const rows=[...deps].sort((a,b)=>{
    const av=a[sk]??null,bv=b[sk]??null;
    if(av===null&&bv===null)return 0;
    if(av===null)return 1;
    if(bv===null)return-1;
    return sortDir==='asc'?av-bv:bv-av;
  });

  const maxes=Object.fromEntries(COLUMNS.map(c=>[c.key,Math.max(0,...deps.map(d=>d[c.key]??0))]));

  const headers=COLUMNS.map(c=>{
    const active=c.key===sk;
    const arrow=active?(sortDir==='desc'?' ↓':' ↑'):'';
    return`<th class="dep-table-th${active?' sort-active':''}" data-sort="${c.key}" style="min-width:90px">${c.label}${arrow}</th>`;
  }).join('');

  const bodyRows=rows.map(d=>{
    const url=`deputat.html?id=${d.cdep_idm}&leg=${LEG}`;
    const color=partyColor(d.partid);
    const logo=PARTIES[d.partid];
    const ini=initials(d.name);
    const shortName=d.name.split(',')[0].trim();
    const photoHtml=d.image
      ?`<img src="${d.image}" alt="" onerror="this.style.display='none';this.nextSibling.style.display='flex'" style="width:28px;height:28px;border-radius:50%;object-fit:cover;flex-shrink:0"><div style="display:none;width:28px;height:28px;border-radius:50%;background:${color};align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`
      :`<div style="width:28px;height:28px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`;
    const badgeImg=logo?`<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" style="width:10px;height:10px;object-fit:contain;margin-right:2px;vertical-align:middle">`:'';

    const cells=COLUMNS.map(c=>{
      const v=d[c.key];
      const active=c.key===sk;
      if(v==null)return`<td class="dep-table-td"><span class="null-val">—</span></td>`;
      const mx=maxes[c.key];
      const barW=mx>0?Math.min(100,v/mx*100).toFixed(1):0;
      const valColor=active?'var(--blue)':(c.isDebt&&v>0?'var(--red-text)':'var(--text2)');
      const fillColor=active?'var(--blue)':(c.isDebt?'var(--red-text)':'var(--border2)');
      return`<td class="dep-table-td">
        <div class="bar-cell-val" style="color:${valColor}">${c.fmt(v)}</div>
        <div class="bar-cell-track"><div class="bar-cell-fill" style="width:${barW}%;background:${fillColor}"></div></div>
      </td>`;
    }).join('');

    return`<tr class="dep-table-row" onclick="location.href='${url}'">
      <td class="dep-table-td td-name">
        <div style="display:flex;align-items:center;gap:8px">
          ${photoHtml}
          <div>
            <div style="font-size:12px;color:var(--text);font-weight:500">${shortName}</div>
            <span style="font-size:10px;padding:1px 5px;border-radius:3px;background:${color}22;color:${color}">${badgeImg}${d.partid}</span>
          </div>
        </div>
      </td>${cells}
    </tr>`;
  }).join('');

  return`<div class="dep-table-wrap">
    <table class="dep-table">
      <thead><tr>
        <th class="dep-table-th sort-name">Deputat</th>${headers}
      </tr></thead>
      <tbody>${bodyRows}</tbody>
    </table>
  </div>`;
}
```

- [ ] **Step 5: Modify `render()` to dispatch on `viewMode`**

Find the existing `function render(){` and its opening lines:
```javascript
function render(){
  const deps=sorted(filtered());
  const grid=document.getElementById('circle-grid');
  const vals=deps.map(d=>d[metric]||0).filter(v=>v>0);
  const maxV=vals.length?Math.max(...vals):1;

  document.getElementById('count-badge').textContent=deps.length+' deputați';
  document.getElementById('page-sub').textContent=
    `Fiecare cerc = un deputat · ${METRIC_LABELS[metric]||metric} · legislatura ${LEG}`;
```

Replace those opening lines with:
```javascript
function render(){
  const unfiltered=filtered();
  document.getElementById('count-badge').textContent=unfiltered.length+' deputați';
  const grid=document.getElementById('circle-grid');

  if(viewMode==='table'){grid.innerHTML=renderTable();return;}

  document.getElementById('page-sub').textContent=
    `Fiecare cerc = un deputat · ${METRIC_LABELS[metric]||metric} · legislatura ${LEG}`;
  const deps=sorted(unfiltered);
  const vals=deps.map(d=>d[metric]||0).filter(v=>v>0);
  const maxV=vals.length?Math.max(...vals):1;
```

The rest of the circle code below stays unchanged.

- [ ] **Step 6: Wire toggle and sort listeners**

Find the event listeners near the bottom of the script:
```javascript
document.getElementById('metric-select').addEventListener('change',e=>{metric=e.target.value;render();});
document.getElementById('search-input').addEventListener('input',e=>{query=e.target.value.toLowerCase().trim();render();});

load();
```

Insert between the search-input listener and `load()`:

```javascript
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
```

- [ ] **Step 7: Verify in browser**

```bash
python -m http.server 8000
```

Open `http://localhost:8000/deputati-activitate.html`:
- Toggle button visible next to leg toggle (both pages now have it)
- Click `≡ Tabel`: metric dropdown disappears, table with 6 activity columns renders
- Column headers: Ședințe ↓, Cuvânt, Propuneri, Legi, Declarații, Întrebări
- Active sort column blue, others grey
- All values are integers (no RON formatting)
- Bar scaling works per column
- Sort / filter / navigation all work as in avere
- Circle view returns when clicking `⬤ Cercuri`

Kill server after testing.

- [ ] **Step 8: Commit**

```bash
git add deputati-activitate.html
git commit -m "feat(activitate): add sortable table view with inline bars"
```

---

### Task 3: Activity log

**Files:**
- Modify: `docs/activity-log.md`

- [ ] **Step 1: Add entry**

In `docs/activity-log.md`, add a new section under the most recent entry:

```markdown
### 2026-05-30 — Sortable table view for deputati-avere and deputati-activitate

**What was done**
- Added `≡ Tabel` toggle button to both `deputati-avere.html` and `deputati-activitate.html` toolbars. The avere page already had a disabled list button; it was enabled and repurposed.
- In table view: all 6 metric columns shown simultaneously (vs. one at a time in circle view), each cell shows value above a 3px inline bar scaled to the column max.
- Clicking any column header sorts the table; clicking twice flips to ascending; clicking a third time resets to default.
- The metric dropdown is hidden in table view (redundant when all columns are visible). Switching back to circles syncs the dropdown to the last sort column.
- Name column is sticky-left for horizontal scroll on narrow screens.

**Decisions**
- No shared JS file — both pages are self-contained to match existing project conventions.
- Bar width scales to column max within the current filtered set — rescales when search/party filters change.
- Datorii column value text is red (debt stands out) unless it is the active sort column, in which case blue (sort state takes priority).
```

- [ ] **Step 2: Commit**

```bash
git add docs/activity-log.md
git commit -m "docs: activity log entry for table view feature"
```
