# Stats Landing Page Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) to implement this plan task-by-task.

**Goal:** Transform index.html from API documentation focus to a clean stats dashboard landing page with simplified navigation and links to available statistics.

**Architecture:** Single-file modification. Remove API documentation sections (hero, sidebar, endpoint cards, demo panels) and simplify layout to show stats bar + minimal link list. Simplify navigation bar by removing info dropdown and search.

**Tech Stack:** HTML, CSS (inline), vanilla JavaScript

---

## File Structure

**Modify:**
- `index.html` — Remove hero section, sidebar, API docs content; simplify nav bar; update main content area

---

## Tasks

### Task 1: Update Navigation Bar — Logo & Title

**Files:**
- Modify: `index.html:200-202`

- [ ] **Step 1: Find the logo section**

In index.html around line 200-202, locate:
```html
<span class="logo" aria-label="cdep API logo">cdep<span>.api</span></span>
<span class="badge">v1.0 DRAFT</span>
```

- [ ] **Step 2: Replace with new title**

Change to:
```html
<span class="logo" aria-label="cdep stats">cdep<span>-api</span> <em>*stats*</em></span>
```

(Note: Use `<em>` instead of `<span>` to emphasize *stats* styling if desired, but keep it simple)

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(nav): change title to 'cdep-api *stats*'"
```

---

### Task 2: Remove Info Dropdown Button & Related Menu

**Files:**
- Modify: `index.html:204-216`

- [ ] **Step 1: Find the info dropdown section**

Locate the nav-dd div starting around line 204:
```html
<div class="nav-dd" id="info-dd">
  <button class="info-btn" id="info-btn" ...>
    ⓘ <span class="info-caret">▾</span>
  </button>
  <div class="info-menu" id="info-menu">
    <a href="#" class="active" onclick="showPage('docs',this)" ...>Documentație</a>
    ...
  </div>
</div>
```

- [ ] **Step 2: Delete the entire nav-dd block**

Remove lines 204-216 completely.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(nav): remove info dropdown menu"
```

---

### Task 3: Remove Search Link from Navigation

**Files:**
- Modify: `index.html:222` (after Task 2, line numbers shift)

- [ ] **Step 1: Find the search link**

Locate:
```html
<a href="search.html" data-i18n="search">Caută</a>
```

- [ ] **Step 2: Delete the search link**

Remove the entire line.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(nav): remove search link"
```

---

### Task 4: Add Date & Source Link to Navigation

**Files:**
- Modify: `index.html:221-223` (current location of lang-toggle)

- [ ] **Step 1: Find the lang-toggle span**

Locate:
```html
<span id="lang-toggle-slot" style="margin-left:6px;display:flex;align-items:center"></span>
```

- [ ] **Step 2: Add source link before lang toggle**

Insert before the lang-toggle span:
```html
<span style="margin-left:auto;font-size:13px;color:var(--text2)">
  date: <a href="https://endimion2k.github.io/cdep-api-poc" target="_blank" style="color:var(--blue)">cdep-api ↗</a>
</span>
```

Result should be:
```html
<span style="margin-left:auto;font-size:13px;color:var(--blue)">
  date: <a href="https://endimion2k.github.io/cdep-api-poc" target="_blank" style="color:var(--blue)">cdep-api ↗</a>
</span>
<span id="lang-toggle-slot" style="margin-left:6px;display:flex;align-items:center"></span>
```

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat(nav): add date and source link"
```

---

### Task 5: Remove Hero Section

**Files:**
- Modify: `index.html:228-236`

- [ ] **Step 1: Find the hero section**

Locate:
```html
<section class="hero">
  <h1><span data-i18n="hero_title_1">Date parlamentare,</span><br><em data-i18n="hero_title_2">deschise pentru toți</em></h1>
  <p data-i18n="hero_desc">...</p>
  <div class="hero-actions">
    ...
  </div>
</section>
```

- [ ] **Step 2: Delete the entire hero section**

Remove the entire `<section class="hero">` and all its contents.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: remove hero section"
```

---

### Task 6: Simplify Main Content Layout

**Files:**
- Modify: `index.html:250-286` (after hero removal, sidebar section)

- [ ] **Step 1: Find the main content area**

Locate:
```html
<div class="main" id="main-content">
  <aside class="sidebar" ...>
    ...
  </aside>

  <main class="content">
    <!-- DOCS PAGE -->
    <div id="page-docs">
      ...
    </div>
```

- [ ] **Step 2: Replace entire main section with simple layout**

Replace the entire `<div class="main">` section with:
```html
<div style="max-width:600px;margin:0 auto;padding:32px 24px">
  <h2 style="font-size:20px;font-weight:600;margin-bottom:24px">Statistici disponibile</h2>
  
  <ul style="list-style:none;padding:0;margin:0">
    <li style="margin-bottom:12px"><a href="avere.html">Averi</a></li>
    <li style="margin-bottom:12px"><a href="deputati-avere.html">Cercuri avere</a></li>
    <li style="margin-bottom:12px"><a href="deputati-activitate.html">Activitate</a></li>
    <li style="margin-bottom:12px"><a href="interpelari-stats.html">Interpelări</a></li>
    <li style="margin-bottom:12px"><a href="proiecte-stats.html">Proiecte</a></li>
  </ul>
</div>
```

This removes the sidebar, all API documentation, and replaces with minimal link list.

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: replace main content with stats links"
```

---

### Task 7: Remove Unused CSS Rules

**Files:**
- Modify: `index.html:70-193` (styles section)

- [ ] **Step 1: Locate and remove hero CSS**

Find and remove:
```css
/* Hero */
.hero{max-width:1100px;margin:0 auto;padding:48px 24px 32px}
.hero h1{font-size:28px;font-weight:600;line-height:1.3;margin-bottom:12px}
.hero h1 em{font-style:normal;color:var(--green)}
.hero p{font-size:15px;color:var(--text2);max-width:580px;line-height:1.7;margin-bottom:24px}
.hero-actions{display:flex;gap:10px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;border-radius:var(--radius-sm);font-size:14px;font-weight:500;cursor:pointer;border:none;text-decoration:none}
.btn-primary{background:var(--text);color:var(--bg)}
.btn-primary:hover{opacity:0.85;text-decoration:none}
.btn-secondary{background:transparent;border:1px solid var(--border2);color:var(--text)}
.btn-secondary:hover{background:var(--bg2);text-decoration:none}
```

- [ ] **Step 2: Remove sidebar CSS**

Find and remove:
```css
/* Sidebar */
.sidebar{position:sticky;top:24px;align-self:start}
.sidebar-section{margin-bottom:24px}
.sidebar-label{font-size:11px;font-weight:600;color:var(--text3);text-transform:uppercase;letter-spacing:0.6px;margin-bottom:8px}
.sidebar-item{display:block;font-size:13px;padding:6px 10px;border-radius:var(--radius-sm);color:var(--text2);margin-bottom:2px;cursor:pointer;border:none;background:none;width:100%;text-align:left}
.sidebar-item:hover{background:var(--bg2);color:var(--text)}
.sidebar-item.active{background:var(--bg3);color:var(--text);font-weight:500}
```

- [ ] **Step 3: Remove main grid layout**

Find and modify:
```css
/* Main layout */
.main{max-width:1100px;margin:0 auto;padding:32px 24px;display:grid;grid-template-columns:220px 1fr;gap:32px}
@media(max-width:700px){.main{grid-template-columns:1fr}}
```

To just:
```css
/* Main layout */
.main{display:none}
```

(Hide it rather than delete in case any JavaScript references it)

- [ ] **Step 4: Remove endpoint/demo CSS**

Find and remove:
```css
/* Endpoint cards */
.endpoint{...}
.ep-header{...}
/* ... all endpoint-related styles ... */

/* Demo panel */
.demo-panel{display:none}
.demo-panel.active{display:block}
/* ... all demo-related styles ... */
```

(Search for `.endpoint`, `.ep-`, `.demo-` classes and remove those blocks)

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "style: remove unused hero, sidebar, endpoint, and demo CSS"
```

---

### Task 8: Remove Unused JavaScript Functions

**Files:**
- Modify: `index.html` (script section at bottom)

- [ ] **Step 1: Locate JavaScript block**

Find the `<script>` section near the end of the file (after footer).

- [ ] **Step 2: Remove page switching functions**

Delete these functions if present:
- `showPage(id, link)` — used to switch between docs/demo/stats tabs
- `scrollTo(id)` — used to scroll to endpoint sections
- `toggleInfo(event)` — used to toggle info menu open/close
- `closeInfo()` — used to close info menu

- [ ] **Step 3: Remove info menu event listeners**

Delete:
```javascript
document.addEventListener('click', () => closeInfo());
```

- [ ] **Step 4: Keep stats loading**

Keep the `loadData()` function and any code that fetches and populates stats numbers. Example:
```javascript
async function loadData() {
  const data = await fetch('data/v1/status.json').then(r => r.json());
  document.getElementById('stat-deputati').textContent = data.deputati || '…';
  // ... etc
}
loadData();
```

If this doesn't exist, you can skip this step.

- [ ] **Step 5: Commit**

```bash
git add index.html
git commit -m "refactor: remove unused page switching and info menu JavaScript"
```

---

### Task 9: Manual Testing & Verification

**Files:**
- Test: `index.html` (open in browser)

- [ ] **Step 1: Open index.html in browser**

```bash
open index.html
# or navigate to http://localhost:8000 if using Python server
```

- [ ] **Step 2: Verify nav bar**

- ✓ Title shows "cdep-api *stats*" (no "v1.0 DRAFT" badge)
- ✓ No (i) info dropdown button visible
- ✓ No "Caută" search link
- ✓ "date: cdep-api ↗" link appears at right of nav (links to endimion2k.github.io)
- ✓ These links still present: Averi, Cercuri avere, Activitate, Interpelări, Proiecte

- [ ] **Step 3: Verify stats bar**

- ✓ Stats bar displays with numbers (Deputați, Voturi, Proiecte de lege, Interpelări, Comisii, Moțiuni, Ședințe plen, Declarații avere)
- ✓ Stats are styled correctly (unchanged from before)

- [ ] **Step 4: Verify main content**

- ✓ "Statistici disponibile" heading visible
- ✓ All 5 links present and styled correctly:
  - Averi (blue, clickable, links to avere.html)
  - Cercuri avere (blue, clickable, links to deputati-avere.html)
  - Activitate (blue, clickable, links to deputati-activitate.html)
  - Interpelări (blue, clickable, links to interpelari-stats.html)
  - Proiecte (blue, clickable, links to proiecte-stats.html)
- ✓ Content is centered and not too wide
- ✓ No sidebar visible
- ✓ No API documentation visible
- ✓ No hero section visible
- ✓ No demo panel visible

- [ ] **Step 5: Verify footer**

- ✓ Footer displays with credits and "Date din cdep-api..." text
- ✓ Links in footer work

- [ ] **Step 6: Test responsive design**

Resize browser to mobile width (375px):
- ✓ Layout remains readable
- ✓ Nav bar wraps or stays on one line (acceptable either way)
- ✓ Stats bar displays vertically or wraps nicely
- ✓ Links list is readable

- [ ] **Step 7: Check browser console**

Open DevTools (F12) → Console tab:
- ✓ No JavaScript errors
- ✓ No 404s or missing resource warnings
- ✓ Stats load successfully (check Network tab if stats numbers are placeholders)

- [ ] **Step 8: Test navigation**

Click each link:
- ✓ Averi → opens avere.html
- ✓ Cercuri avere → opens deputati-avere.html
- ✓ Activitate → opens deputati-activitate.html
- ✓ Interpelări → opens interpelari-stats.html
- ✓ Proiecte → opens proiecte-stats.html

- [ ] **Step 9: Commit verification**

```bash
git add -A
git commit -m "test: verify stats landing page design and functionality"
```

---

## Summary

This plan modifies index.html across 9 tasks:
1. Update nav title
2. Remove info dropdown
3. Remove search link
4. Add date/source link
5. Remove hero section
6. Simplify main content layout
7. Remove unused CSS
8. Remove unused JavaScript
9. Manual testing & verification

Total scope: Single-file modification with incremental commits at each logical step.
