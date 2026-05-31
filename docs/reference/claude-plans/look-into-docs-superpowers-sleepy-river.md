# Dashboard & Stats Pipeline — Status & Next Steps

## Context

User asked what dashboards/stats pages have been planned. We have four plans in `docs/superpowers/plans/`. Three are substantially complete; one hasn't been started. This plan summarizes status and identifies the clearest next tasks.

---

## Current Status

| Plan | Status | Remaining |
|---|---|---|
| **Deputat Avere Sections** (`deputat.html`) | ✅ 100% done | — |
| **Avere PDF Full Extraction** (`parsers/avere_pdf.py`) | ✅ ~95% done | Activity log + backlog update only |
| **Deputies Avere Dashboard** (`deputati-avere.html`) | 🔶 ~85% done | Smoke test (Task 6) — browser verify only |
| **Stats Landing Page** (`index.html`) | ❌ 0% done | All 9 tasks |

---

## Recommended Next: Stats Landing Page Redesign

**Plan file:** `docs/superpowers/plans/2026-05-29-stats-landing-page.md`  
**Target file:** `index.html`

### What it does
Transforms `index.html` from an API reference page into a focused stats hub landing page. The full plan is already written and approved.

### 9 tasks (all pending - [ ])
1. Simplify nav bar (title → "cdep-api *stats*", remove (i) dropdown and search, add source link)
2. Remove hero section entirely
3. Keep stats bar as-is
4. Replace main content with centered list of 5 dashboard links (Averi, Averi ALT, Activitate, Interpelări, Proiecte)
5. Clean up sidebar CSS
6. Remove API docs / endpoint card HTML
7. Remove demo panel JS
8. Remove page-switching JS
9. Smoke test — verify in browser, mobile responsive

### Key constraints from the design spec (`docs/superpowers/specs/2026-05-29-stats-landing-page-design.md`)
- Nav title: `cdep-api <em>stats</em>` (italic "stats")
- Max-width ~600px centered container for link list
- 5 links: Averi, Averi<sup>ALT</sup>, Activitate, Interpelări, Proiecte
- Keep footer, language toggle, stats bar
- Remove: hero, sidebar, API docs, endpoint cards, demo panels, page-switching JS, info dropdown

---

## Also available: Deputies Avere Dashboard smoke test

**Plan file:** `docs/superpowers/plans/2026-05-29-avere-deputies-dashboard.md`  
**Target file:** `deputati-avere.html`  
**Remaining:** Task 6 only — open in browser, verify circles render, metric selector works, party filter works, null deputies greyed out. No code changes expected.

---

## Verification

- `python -m http.server 8000` → open `http://localhost:8000` to verify landing page
- Check all 5 dashboard links navigate correctly
- Verify mobile layout at ~375px width
- Run smoke test on `deputati-avere.html` while server is up
