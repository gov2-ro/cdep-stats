# Stats Landing Page Design

**Date:** 2026-05-29  
**Scope:** Redesign index.html from API documentation focus to stats dashboard landing page

## Overview

Transform the current index.html from an API reference documentation page into a clean, focused landing page for the cdep-api stats dashboards. The page will highlight key parliamentary statistics and provide navigation to available data visualizations.

## Target Users

- Citizens wanting a quick overview of parliamentary activity
- Researchers looking for links to specific stats dashboards
- Anyone discovering the project for the first time

## Page Structure

### 1. Navigation Bar (Header)

**Current state:** Logo, info dropdown (i), nav links, search, language toggle  
**Changes:**
- Logo text: Change `cdep.api [v1.0 DRAFT]` to `cdep-api *stats*`
- Remove the (i) dropdown entirely (no Documentație, Demo, Statistici, Swagger UI menu)
- Keep nav links: Averi, Cercuri avere, Activitate, Interpelări, Proiecte
- Remove the Search/Caută link
- Add at the end of nav: `date: <a href="https://endimion2k.github.io/cdep-api-poc" target="_blank">cdep-api ↗</a>` (using U+2197 NORTHEAST ARROW for external link indicator)
- Keep language toggle if present

### 2. Hero Section

**Current state:** Large heading + description paragraph + CTA buttons  
**Action:** Remove entirely
- Delete the h1, p, and .hero-actions (Explorează API, Caută, Descarcă OpenAPI spec)
- No replacement needed

### 3. Stats Bar

**Current state:** Existing stats display  
**Action:** Keep as-is
- Remains the visual anchor of the page
- Shows: Deputați, Voturi, Proiecte de lege, Interpelări, Comisii, Moțiuni, Ședințe plen, Declarații avere
- No style changes needed

### 4. Main Content Area

**Current state:** Two-column layout (sidebar + API docs)  
**New design:**
- Remove sidebar entirely
- Use full-width vertical layout
- Simple centered container with modest max-width (similar to hero width)

**Content structure:**

Main content div: single column, centered, max-width ~600px, padding 32px 24px

```
[STATS BAR - unchanged]

[Main content area]

<h2>Statistici disponibile</h2>

<ul style="list-style: none; padding: 0;">
  <li><a href="avere.html">Averi</a></li>
  <li><a href="deputati-avere.html">Cercuri avere</a></li>
  <li><a href="deputati-activitate.html">Activitate</a></li>
  <li><a href="interpelari-stats.html">Interpelări</a></li>
  <li><a href="proiecte-stats.html">Proiecte</a></li>
</ul>

[Footer - keep as-is]
```

**Link styling:**
- Simple <a> elements, inherit blue color from global --blue CSS variable
- Each link on its own line (list items or divs)
- Hover effects work naturally from existing CSS
- No card styling or additional decoration

### 5. Footer

**Current state:** Footer with credits and license  
**Action:** Keep unchanged
- Footer already has correct attribution: "Date din cdep-api..." with links
- Just ensure no API-specific text is in footer

### 6. Remove

- Entire sidebar (sidebar, sidebar-section, sidebar-item elements)
- All #page-docs, #page-demo content (API endpoint cards, endpoint details, try-it sections, params tables)
- Demo panel styling if present
- Any JavaScript related to page switching (showPage, scrollTo functions related to demo/docs)
- Search functionality references
- Info dropdown menu styling and behavior
- Hero section (.hero element and contents)

## Technical Notes

- Keep all i18n attributes in remaining content for translation support
- Simplify JavaScript: remove info menu toggle, page switching logic, sidebar interactions
- Keep stats loading logic (the data fetching that populates stat numbers)
- Keep footer attribution
- Keep header styling, just hide the elements via display:none or remove from DOM

## Success Criteria

- Page loads with clean, focused navigation
- Stats bar displays with live data
- All 5 links (Averi, Cercuri avere, Activitate, Interpelări, Proiecte) work and point to correct pages
- Footer shows credits and cdep-api link
- No API documentation visible
- Mobile responsive (1-column on small screens)
- No console errors from removed JavaScript functions
