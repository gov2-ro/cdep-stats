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
    ).join("\n      ");
    document.getElementById("site-header").innerHTML = `
<header class="header">
  <div class="header-inner">
    <a href="index.html" class="logo">CDEP<span> stats</span></a>
    <nav class="nav">
      ${links}
      <span style="margin-left:auto;font-size:13px;color:var(--text2)"><a href="https://endimion2k.github.io/cdep-api-poc" target="_blank" style="color:var(--blue)">cdep-api ↗</a></span>
      <span id="lang-toggle-slot" style="margin-left:4px;display:flex;align-items:center"></span>
    </nav>
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
