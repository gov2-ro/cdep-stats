(function (global) {
  "use strict";

  const NAV_LINKS = [
    { href: "avere.html",             label: "Averi",       keys: ["avere.html", "deputati-avere.html"] },
    { href: "deputati-activitate.html", label: "Activitate" },
    { href: "comisii.html",           label: "Comisii" },
    { href: "interpelari-stats.html", label: "Interpelări" },
    { href: "voturi.html",            label: "Voturi",      keys: ["voturi.html", "vot.html"] },
    { href: "proiecte-stats.html",    label: "Proiecte" },
    { href: "proiect.html",           label: "Legi" },
    { href: "motiuni.html",           label: "Moțiuni" },
    { href: "ordine-zi.html",         label: "Agendă" },
    { href: "interese.html",          label: "Interese" },
    { href: "partide.html",           label: "Partide",     keys: ["partide.html", "partid.html"] },
    { href: "judete.html",            label: "Județe" },
  ];

  function _activeHref() {
    const file = window.location.pathname.split("/").pop() || "index.html";
    for (const link of NAV_LINKS) {
      const keys = link.keys || [link.href];
      if (keys.includes(file)) return link.href;
    }
    return null;
  }

  function renderHeader() {
    const active = _activeHref();
    const links = NAV_LINKS.map(l =>
      `<a href="${l.href}"${l.href === active ? ' class="active"' : ""}>${l.label}</a>`
    ).join("");
    document.getElementById("site-header").innerHTML = `
<style>
/* nav layout — injected by nav.js, overrides per-page defaults */
.header-inner{display:flex!important;flex-wrap:wrap!important;align-items:center!important;justify-content:flex-start!important;gap:2px!important;padding:6px 16px!important}
.logo{white-space:nowrap!important;flex-shrink:0;font-size:14px!important;margin-right:4px;padding:3px 6px!important;line-height:1.4}
.nav{display:contents}
.nav a{font-size:12px!important;padding:3px 7px!important;white-space:nowrap}
#lang-toggle-slot{display:inline-flex!important;align-items:center}
#lang-toggle-slot button,#lang-toggle-slot a{font-size:11px!important;padding:2px 4px!important}
</style>
<header class="header">
  <div class="header-inner">
    <a href="index.html" class="logo">CDEP<span> stats</span></a>
    <nav class="nav">${links}</nav>
    <a href="https://endimion2k.github.io/cdep-api-poc" target="_blank" style="font-size:11px;padding:2px 6px;border-radius:4px;white-space:nowrap;color:rgba(255,255,255,.5)">cdep-api ↗</a>
    <span id="lang-toggle-slot" style="display:inline-flex;align-items:center"></span>
  </div>
</header>`;
  }

  const FOOTER_LINKS = [
    { href: "avere.html",             label: "Averi" },
    { href: "deputati-activitate.html", label: "Activitate" },
    { href: "comisii.html",           label: "Comisii" },
    { href: "interpelari-stats.html", label: "Interpelări" },
    { href: "voturi.html",            label: "Voturi" },
    { href: "proiecte-stats.html",    label: "Proiecte" },
    { href: "proiect.html",           label: "Legi" },
    { href: "motiuni.html",           label: "Moțiuni" },
    { href: "ordine-zi.html",         label: "Agendă" },
    { href: "interese.html",          label: "Interese" },
    { href: "partide.html",           label: "Partide" },
    { href: "judete.html",            label: "Județe" },
  ];

  function renderFooter(extraHtml) {
    const pageLinks = FOOTER_LINKS.map(l => `<a href="${l.href}">${l.label}</a>`).join(" · ");
    document.getElementById("site-footer").innerHTML = `
<footer class="footer">
  <div style="margin-bottom:10px">${pageLinks}</div>
  <span><span data-i18n="data_from">Date din</span> <a href="https://cdep.ro" target="_blank">cdep.ro</a>, via CDEP API: <a href="https://github.com/Endimion2k/cdep-api-poc" target="_blank">Endimion2k/cdep-api-poc</a> · <span data-i18n="license">Licență</span>: Open Government License v3.0</span>
  ${extraHtml ? `<div style="margin-top:6px">${extraHtml}</div>` : ""}
</footer>
<!-- 100% privacy-first analytics -->
<script async src="https://scripts.simpleanalyticscdn.com/latest.js"></script>

`;
  }

  function renderLegToggle(currentLeg, pageName, legislatures = [2024, 2020]) {
    return legislatures.map(l =>
      `<button class="view-btn${l === currentLeg ? ' active' : ''}" onclick="location.href='${pageName}?leg=${l}'">${l}</button>`
    ).join('');
  }

  function renderPageMeta(config) {
    const { jsonUrl, legislatures, currentLeg, pageName } = config;
    let html = '';
    if (legislatures && pageName) {
      html += `<div class="view-toggle">${renderLegToggle(currentLeg, pageName, legislatures)}</div>`;
    }
    if (jsonUrl) {
      html += `<span data-i18n="source">Sursă JSON</span>: <a href="${jsonUrl}">${jsonUrl}</a>`;
    }
    return html;
  }

  global.NAV = { renderHeader, renderFooter, renderLegToggle, renderPageMeta };
})(window);
