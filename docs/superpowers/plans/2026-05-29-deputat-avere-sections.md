# Deputat Avere Sections — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 5 avere (wealth declaration) sections to the bottom of the existing `deputat.html` deputy profile page, loading per-deputy JSON from `data/v1/declaratii-avere/legislatura-{leg}/{idm}.json`.

**Architecture:** Single file change — `deputat.html`. Add two number-formatting helpers, extend the existing `Promise.all` fetch with a 4th avere URL, implement a `renderAvere(avere)` function that returns HTML for 5 sections (stat cards, imobile by category, vehicule, plasamente, bunuri înstrăinate), and append its output to the existing content render.

**Tech Stack:** Vanilla JS, HTML, existing CSS variables from deputat.html

---

## File Map

| File | Change |
|---|---|
| `deputat.html` | Add `fmtRON()`, `fmtMP()`, `renderAvere()` functions; extend `Promise.all`; append avere HTML to content |

---

## Task 1 — Add helpers + avere fetch + renderAvere + wire into HTML

**Files:**
- Modify: `deputat.html`

- [ ] **Step 1: Read the current file**

```bash
cat -n /Users/pax/devbox/gov2/cdep-api-poc/deputat.html
```

Locate exactly:
- The line `function getParam(name) {` (around line 125) — insert helpers before this
- The line `const [depResp, intResp, motResp] = await Promise.all([` (around line 144) — extend this
- The closing `` `;`` of the `document.getElementById('content').innerHTML = `` block (around line 248) — append `${renderAvere(avereResp)}` before it

- [ ] **Step 2: Insert `fmtRON`, `fmtMP`, `renderAvere` before `function getParam`**

Find the line `function getParam(name) {` and insert this block immediately before it:

```javascript
function fmtRON(v) {
  if (!v || v === 0) return '0 RON';
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M RON';
  if (v >= 10_000) return Math.round(v / 1_000) + 'K RON';
  return Math.round(v).toLocaleString('ro-RO') + ' RON';
}

function fmtMP(v) {
  if (!v || v === 0) return '0 m²';
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M m²';
  if (v >= 10_000) return Math.round(v / 1_000) + 'K m²';
  return Math.round(v).toLocaleString('ro-RO') + ' m²';
}

function renderAvere(avere) {
  if (!avere?.data?.declaratii?.length) return '';
  const decl = avere.data.declaratii[avere.data.declaratii.length - 1];

  // ── Section 1: Stat cards ────────────────────────────────────────────────
  const cardDefs = [
    { num: fmtRON(decl.total_active_monetare_ron), lbl: 'Total active' },
    { num: fmtRON(decl.avere_neta_ron), lbl: 'Avere netă', red: (decl.avere_neta_ron || 0) < 0 },
    { num: (decl.terenuri_count || 0) + (decl.cladiri_count || 0), lbl: 'Nr. imobile' },
    { num: fmtMP(decl.suprafata_total_mp), lbl: 'Suprafață totală' },
    { num: fmtRON(decl.venituri_anuale_ron), lbl: 'Venituri anuale' },
    { num: fmtRON(decl.conturi_total_ron), lbl: 'Conturi bancare' },
    ...((decl.bijuterii_total_ron || 0) > 0 ? [{ num: fmtRON(decl.bijuterii_total_ron), lbl: 'Bijuterii / artă' }] : []),
    { num: decl.auto_count || 0, lbl: 'Vehicule' },
  ];
  const cardsHtml = cardDefs.map(c => `
    <div class="act-card">
      <div class="act-num"${c.red ? ' style="color:var(--red-text)"' : ''}>${c.num}</div>
      <div class="act-lbl">${c.lbl}</div>
    </div>`).join('');

  const meta = [
    decl.an_prima_proprietate ? `Prima proprietate: ${decl.an_prima_proprietate}` : '',
    (decl.nr_judete || 0) > 0 ? `${decl.nr_judete} județe` : '',
    (decl.nr_companii || 0) > 0 ? `${decl.nr_companii} companii` : '',
  ].filter(Boolean).join(' · ');

  const sec1 = `
    <div class="section">
      <h2>Declarație de avere <span style="font-weight:400;color:var(--text3);font-size:14px">· ${decl.data_depunere || ''} · <a href="${decl.pdf_url || '#'}" target="_blank" rel="noopener">PDF ↗</a></span></h2>
      <div class="activitate">${cardsHtml}</div>
      ${meta ? `<div style="font-size:13px;color:var(--text3);margin-top:8px">${meta}</div>` : ''}
    </div>`;

  // ── Section 2: Imobile by category ───────────────────────────────────────
  const nrImobile = (decl.terenuri_count || 0) + (decl.cladiri_count || 0);
  const CAT_LABEL = {
    forestier: 'Terenuri forestiere', agricol: 'Terenuri agricole',
    extravilan: 'Terenuri extravilane', intravilan: 'Terenuri intravilane',
    luciu_apa: 'Luciu de apă', locuinta: 'Clădiri — locuință',
    apartament: 'Clădiri — apartament', comercial: 'Clădiri — comerciale',
    vacanta: 'Clădiri — vacanță', alte_cladiri: 'Clădiri — alte categorii',
    necunoscuta: 'Imobile — categorie necunoscută',
  };
  let sec2 = '';
  if (nrImobile > 0) {
    const catMap = {};
    for (const im of (decl.imobile_detaliate || [])) {
      const cat = im.categorie || 'necunoscuta';
      if (!catMap[cat]) catMap[cat] = { count: 0, mp: 0 };
      catMap[cat].count++;
      catMap[cat].mp += im.suprafata_mp || 0;
    }
    const imRows = Object.entries(catMap)
      .sort((a, b) => b[1].mp - a[1].mp)
      .map(([cat, { count, mp }]) => `
        <div class="list-item" style="display:flex;align-items:baseline;gap:8px">
          <span>${CAT_LABEL[cat] || cat}</span>
          <span style="color:var(--text3);font-size:13px">${count} parcele</span>
          <span style="margin-left:auto;font-size:13px;color:var(--text2)">${fmtMP(mp)}</span>
        </div>`).join('');
    const judetNote = (decl.nr_judete || 0) > 0
      ? `<div style="font-size:13px;color:var(--text3);margin-top:8px">Județe: ${decl.nr_judete}</div>` : '';
    sec2 = `
      <div class="section">
        <h2>Imobile (${nrImobile})</h2>
        ${imRows}
        ${judetNote}
      </div>`;
  }

  // ── Section 3: Vehicule ───────────────────────────────────────────────────
  let sec3 = '';
  if ((decl.vehicule || []).length > 0) {
    const vRows = decl.vehicule.map(v => `
      <div class="list-item" style="display:flex;align-items:baseline;gap:8px">
        <span>${v.natura}</span>
        ${v.marca ? `<span style="color:var(--text3);font-size:13px">${v.marca}</span>` : ''}
        ${v.an_fabricatie ? `<span style="margin-left:auto;font-size:13px;color:var(--text3)">${v.an_fabricatie}</span>` : ''}
      </div>`).join('');
    sec3 = `
      <div class="section">
        <h2>Vehicule (${decl.vehicule.length})</h2>
        ${vRows}
      </div>`;
  }

  // ── Section 4: Plasamente ─────────────────────────────────────────────────
  let sec4 = '';
  if ((decl.plasamente_detaliate || []).length > 0) {
    const TIP = { imprumut: 'Împrumut', actiuni: 'Acțiuni', parti_sociale: 'Părți sociale', titluri_stat: 'Titluri stat' };
    const pRows = decl.plasamente_detaliate.map(p => `
      <div class="list-item" style="display:flex;align-items:baseline;gap:8px;flex-wrap:wrap">
        <span>${p.emitent || '—'}</span>
        ${p.tip ? `<span style="font-size:11px;padding:2px 8px;border-radius:3px;background:var(--bg3);color:var(--text2)">${TIP[p.tip] || p.tip}</span>` : ''}
        <span style="margin-left:auto;font-size:13px;color:var(--text2)">${fmtRON(p.valoare_ron)}</span>
      </div>`).join('');
    sec4 = `
      <div class="section">
        <h2>Plasamente &amp; investiții (${decl.plasamente_detaliate.length})</h2>
        ${pRows}
      </div>`;
  }

  // ── Section 5: Bunuri înstrăinate ─────────────────────────────────────────
  let sec5 = '';
  if ((decl.bunuri_instrainate_count || 0) > 0) {
    sec5 = `
      <div class="section">
        <h2>Bunuri înstrăinate în ultimele 12 luni (${decl.bunuri_instrainate_count})</h2>
        <div class="list-item" style="display:flex;justify-content:space-between">
          <span>${decl.bunuri_instrainate_count} bunuri</span>
          <span style="font-size:13px;color:var(--text2)">total ${fmtRON(decl.bunuri_instrainate_total_ron)}</span>
        </div>
      </div>`;
  }

  return sec1 + sec2 + sec3 + sec4 + sec5;
}

```

- [ ] **Step 3: Extend the Promise.all to fetch avere data**

Find this exact block in `loadDeputat()`:
```javascript
  let dep, allInterpelari, allMotiuni;
  try {
    const [depResp, intResp, motResp] = await Promise.all([
      fetch(jsonUrl).then(r => r.json()),
      fetch(`data/v1/interpelari/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/motiuni/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
    ]);
```

Replace it with:
```javascript
  let dep, allInterpelari, allMotiuni, avereResp;
  try {
    const [depResp, intResp, motResp, avereJson] = await Promise.all([
      fetch(jsonUrl).then(r => r.json()),
      fetch(`data/v1/interpelari/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/motiuni/legislatura-${leg}.json`).then(r => r.json()).catch(() => null),
      fetch(`data/v1/declaratii-avere/legislatura-${leg}/${parseInt(id)}.json`).then(r => r.json()).catch(() => null),
    ]);
    avereResp = avereJson;
```

Note: the existing `const idNum = parseInt(id);` line follows after the destructuring — leave it in place.

- [ ] **Step 4: Append `renderAvere` output to the content innerHTML**

Find the closing of the `document.getElementById('content').innerHTML = \`` block. It ends with something like:

```javascript
        <a class="cross-link" href="${jsonUrl}">
          <strong data-i18n="raw_json">Date raw JSON</strong>
          <span data-i18n="full_profile">Profil complet în format API</span>
        </a>
      </div>
    </div>
  `;
```

Change the closing `` `; `` to:

```javascript
        <a class="cross-link" href="${jsonUrl}">
          <strong data-i18n="raw_json">Date raw JSON</strong>
          <span data-i18n="full_profile">Profil complet în format API</span>
        </a>
      </div>
    </div>
    ${renderAvere(avereResp)}
  `;
```

- [ ] **Step 5: Verify the page loads without JS errors**

```bash
cd /Users/pax/devbox/gov2/cdep-api-poc && python3 -m http.server 8000 &
```

Open http://localhost:8000/deputat.html?id=153 in a browser. Open DevTools console. Expected: no JS errors; page loads normally; avere sections appear at the bottom.

- [ ] **Step 6: Verify avere sections with real data**

Check http://localhost:8000/deputat.html?id=153 (Iordache Ion — heavy avere data). Expected:
- **Declarație de avere** section with 8 stat cards, PDF link, "Prima proprietate: 2001 · 5 județe" note
- **Imobile (83)** section with rows grouped by category, sorted by suprafata descending
- **Vehicule (10)** section with 10 rows
- **Plasamente & investiții** section absent (0 entries)
- **Bunuri înstrăinate** section with 2 entries summary

Check http://localhost:8000/deputat.html?id=23 (Becali — has plasamente). Expected: **Plasamente & investiții** section appears with company entries.

Check http://localhost:8000/deputat.html?id=1 (a deputy without avere data or minimal data). Expected: no JS errors; avere sections simply absent.

- [ ] **Step 7: Kill the dev server**

```bash
kill %1 2>/dev/null || pkill -f "python3 -m http.server 8000"
```

---

## Task 2 — Activity log + commit

**Files:**
- Modify: `docs/activity-log.md`
- Modify: `deputat.html` (committed)

- [ ] **Step 1: Add activity log entry**

In `docs/activity-log.md`, add at the top of `## Dashboards`:

```markdown
### 2026-05-29 — Avere sections on deputy profile page

Added 5 wealth declaration sections to the bottom of `deputat.html`, loading `data/v1/declaratii-avere/legislatura-{leg}/{idm}.json` in the existing `Promise.all`. New `renderAvere()` function generates: (1) stat cards grid with total active, avere netă, nr imobile, suprafață, venituri, conturi, bijuterii, vehicule; (2) imobile grouped by category from `imobile_detaliate[]`; (3) vehicule list; (4) plasamente list (hidden when empty); (5) bunuri înstrăinate summary (hidden when empty). Missing avere file → all sections silently absent.
```

- [ ] **Step 2: Commit**

```bash
cd /Users/pax/devbox/gov2/cdep-api-poc
git add deputat.html docs/activity-log.md
git commit -m "feat(deputat): add avere sections — stat cards, imobile, vehicule, plasamente"
```

---

## Self-Review

**Spec coverage:**
- ✅ Fetch `declaratii-avere/{leg}/{idm}.json` in parallel — Task 1 Step 3
- ✅ Use last declaration — `decl = avere.data.declaratii[avere.data.declaratii.length - 1]`
- ✅ Section 1: stat cards (8 cards, fmtRON/fmtMP, bijuterii hidden if 0) — Task 1 Step 2
- ✅ Section 1: meta line (an_prima_proprietate, nr_judete, nr_companii) — Task 1 Step 2
- ✅ Section 1: date + PDF link in heading — Task 1 Step 2
- ✅ Section 2: imobile grouped by category from imobile_detaliate[], sorted by suprafata — Task 1 Step 2
- ✅ Section 2: hidden if nrImobile === 0 — Task 1 Step 2
- ✅ Section 3: vehicule list (natura + marca + an_fabricatie), hidden if empty — Task 1 Step 2
- ✅ Section 4: plasamente list (emitent + tip tag + fmtRON), hidden if empty — Task 1 Step 2
- ✅ Section 5: bunuri înstrăinate summary, hidden if count === 0 — Task 1 Step 2
- ✅ Avere fetch fails → `null` → `renderAvere(null)` returns `''` — guard at top of function
- ✅ No new files, no new build scripts — spec confirmed

**Placeholder scan:** None found.

**Type consistency:** `fmtRON` and `fmtMP` defined in Task 1 Step 2 and used throughout `renderAvere` in the same step. `avereResp` declared in Task 1 Step 3, used in Task 1 Step 4.
