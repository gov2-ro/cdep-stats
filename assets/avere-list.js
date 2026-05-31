/**
 * Shared avere deputy-list renderer.
 *
 * Used by two pages:
 *   - avere.html           — merged wealth page, shows a Top 50 / Bottom 50 subset.
 *   - deputati-avere.html  — full list of every deputy.
 *
 * The module is pure: it exposes formatting helpers and two render functions
 * (`renderTable`, `renderCircles`) that take a deputy array + options and return
 * an HTML string. Each page owns its own toolbar state, event wiring and tooltip.
 * Extracting it here keeps the table/circle markup in one place (the two pages
 * used to carry diverging copies).
 *
 * Deputy record shape (data/v1/stats/avere-deputies-{leg}.json → deputies[]):
 *   cdep_idm, name, partid, image,
 *   venituri_ron, conturi_ron, imobile_count, suprafata_mp, auto_count, datorii_ron,
 *   delta_conturi_ron, delta_imobile   (last two null unless ≥2 declarations)
 */
(function (global) {
  "use strict";

  // Party hex colors for badge backgrounds; unknown → #777
  const PARTY_COLORS = {
    PSD: "#185FA5", PNL: "#993C1D", USR: "#3B6D11", AUR: "#854F0B",
    UDMR: "#5F5E5A", SOSRO: "#A32D2D", POT: "#553378", PMP: "#6D5A9E",
    FDREPTEI: "#2a6496", APP: "#6a4c93", Neafiliat: "#777",
  };
  function partyColor(p) { return PARTY_COLORS[p] || "#777"; }

  // Logo filename for a party, or null. "lipsa.jpg" is the ANI placeholder for
  // "no logo" — treat it as absent so we don't request a 404.
  function logoOf(parties, p) {
    const l = parties[p];
    return l && l !== "lipsa.jpg" ? l : null;
  }

  const MONEY_METRICS = new Set([
    "venituri_ron", "conturi_ron", "datorii_ron", "delta_conturi_ron",
  ]);

  // Compact value formatter (e.g. 384.5M RON, 45.300 RON, 150 mp, 3)
  function fmtVal(v, metric) {
    if (v == null) return "—";
    if (MONEY_METRICS.has(metric)) {
      const a = Math.abs(v), s = v < 0 ? "-" : "";
      if (a >= 1e6) return s + (a / 1e6).toFixed(a >= 1e7 ? 0 : 1) + "M RON";
      if (a >= 1e3) return s + Math.round(a).toLocaleString("ro-RO") + " RON";
      return s + Math.round(a) + " RON";
    }
    if (metric === "suprafata_mp") return Math.round(v).toLocaleString("ro-RO") + " mp";
    return v.toLocaleString("ro-RO");
  }

  // Like fmtVal but wraps the numeric part in <b> (used by circle labels)
  function fmtValHtml(v, metric) {
    if (v == null) return "—";
    if (MONEY_METRICS.has(metric)) {
      const a = Math.abs(v), s = v < 0 ? "-" : "";
      if (a >= 1e6) return s + "<b>" + (a / 1e6).toFixed(a >= 1e7 ? 0 : 1) + "M</b> RON";
      if (a >= 1e3) return "<b>" + s + Math.round(a).toLocaleString("ro-RO") + "</b> RON";
      return "<b>" + s + Math.round(a) + "</b> RON";
    }
    if (metric === "suprafata_mp") return "<b>" + Math.round(v).toLocaleString("ro-RO") + "</b> mp";
    return "<b>" + v.toLocaleString("ro-RO") + "</b>";
  }

  // Decade group (floor of log10) for circle magnitude breaks; null for 0/null
  function magGroup(v) {
    if (v == null || v <= 0) return null;
    return Math.floor(Math.log10(v));
  }

  // ── Circle size tuning ──────────────────────────────────────────────
  const CIRCLE_SCALE = 2.5;
  const CIRC_MIN = 12 * CIRCLE_SCALE; // ~30 px (null / zero value)
  const CIRC_MAX = 68 * CIRCLE_SCALE; // ~170 px (largest value)
  function circleSize(v, maxV) {
    if (v == null || v <= 0 || maxV <= 0) return CIRC_MIN;
    return Math.round(
      Math.max(CIRC_MIN, Math.min(CIRC_MAX, CIRC_MIN + (CIRC_MAX - CIRC_MIN) * Math.sqrt(v / maxV)))
    );
  }

  function initials(name) {
    const parts = name.split(/[\s,]+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }

  // The 6 base metrics that drive the metric selector, circle sizing and
  // Top/Bottom-50 ranking. Evolution deltas are table-only columns.
  const METRIC_KEYS = [
    "venituri_ron", "conturi_ron", "imobile_count",
    "suprafata_mp", "auto_count", "datorii_ron",
  ];

  // Table columns: 6 base metrics + 3 mandate-evolution columns.
  // `get` derives a value (for the evolution columns); otherwise d[key] is used.
  const COLUMNS = [
    { key: "venituri_ron",  label: "Venituri",         money: true },
    { key: "conturi_ron",   label: "Conturi",          money: true },
    { key: "imobile_count", label: "Imobile" },
    { key: "suprafata_mp",  label: "Suprafață",        mp: true },
    { key: "auto_count",    label: "Auto" },
    { key: "datorii_ron",   label: "Datorii",          money: true, isDebt: true },
    {
      key: "crestere", label: "Creștere conturi", money: true,
      get: (d) => (d.delta_conturi_ron != null && d.delta_conturi_ron > 0 ? d.delta_conturi_ron : null),
    },
    {
      key: "scadere", label: "Scădere conturi", money: true, isDebt: true,
      get: (d) => (d.delta_conturi_ron != null && d.delta_conturi_ron < 0 ? d.delta_conturi_ron : null),
    },
    {
      key: "imobile_noi", label: "Imobile noi",
      get: (d) => (d.delta_imobile != null && d.delta_imobile !== 0 ? d.delta_imobile : null),
    },
  ];

  function colVal(d, c) { return c.get ? c.get(d) : d[c.key]; }
  function fmtCol(v, c) {
    if (v == null) return "—";
    if (c.money) return fmtVal(v, "conturi_ron");
    if (c.mp) return fmtVal(v, "suprafata_mp");
    return Number(v).toLocaleString("ro-RO");
  }

  /**
   * Sortable table of deputies. Caller passes the already-filtered/subset list.
   * opts: { parties, leg, sortKey, sortDir }
   */
  function renderTable(deps, opts) {
    opts = opts || {};
    const parties = opts.parties || {};
    const leg = opts.leg != null ? opts.leg : 2024;
    const sk = opts.sortKey || COLUMNS[0].key;
    const sortDir = opts.sortDir || "desc";
    if (!deps.length) return '<p style="color:var(--text3);padding:40px 0">Niciun deputat.</p>';

    const sortCol = COLUMNS.find((c) => c.key === sk) || COLUMNS[0];
    const rows = [...deps].sort((a, b) => {
      const av = colVal(a, sortCol) ?? null, bv = colVal(b, sortCol) ?? null;
      if (av === null && bv === null) return 0;
      if (av === null) return 1;
      if (bv === null) return -1;
      return sortDir === "asc" ? av - bv : bv - av;
    });

    const maxes = Object.fromEntries(
      COLUMNS.map((c) => [c.key, Math.max(0, ...deps.map((d) => Math.abs(colVal(d, c) ?? 0)))])
    );

    const headers = COLUMNS.map((c) => {
      const active = c.key === sk;
      const arrow = active ? (sortDir === "desc" ? " ↓" : " ↑") : "";
      return `<th class="dep-table-th${active ? " sort-active" : ""}" data-sort="${c.key}" style="min-width:90px">${c.label}${arrow}</th>`;
    }).join("");

    const bodyRows = rows.map((d) => {
      const url = `deputat.html?id=${d.cdep_idm}&leg=${leg}`;
      const color = partyColor(d.partid);
      const logo = logoOf(parties, d.partid);
      const ini = initials(d.name);
      const shortName = d.name.split(",")[0].trim();
      const photoHtml = d.image
        ? `<img src="${d.image}" alt="" onerror="this.style.display='none';this.nextSibling.style.display='flex'" style="width:28px;height:28px;border-radius:50%;object-fit:cover;flex-shrink:0"><div style="display:none;width:28px;height:28px;border-radius:50%;background:${color};align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`
        : `<div style="width:28px;height:28px;border-radius:50%;background:${color};display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#fff;flex-shrink:0">${ini}</div>`;
      const badgeImg = logo
        ? `<img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" style="width:10px;height:10px;object-fit:contain;margin-right:2px;vertical-align:middle">`
        : "";

      const cells = COLUMNS.map((c) => {
        const v = colVal(d, c);
        const active = c.key === sk;
        if (v == null) return `<td class="dep-table-td"><span class="null-val">—</span></td>`;
        const mx = maxes[c.key];
        const barW = mx > 0 ? Math.min(100, (Math.abs(v) / mx) * 100).toFixed(1) : 0;
        const valColor = active ? "var(--blue)" : c.isDebt && v > 0 ? "var(--red-text)" : "var(--text2)";
        const fillColor = active ? "var(--blue)" : c.isDebt ? "var(--red-text)" : "var(--border2)";
        return `<td class="dep-table-td">
          <div class="bar-cell-val" style="color:${valColor}">${fmtCol(v, c)}</div>
          <div class="bar-cell-track"><div class="bar-cell-fill" style="width:${barW}%;background:${fillColor}"></div></div>
        </td>`;
      }).join("");

      return `<tr class="dep-table-row" onclick="location.href='${url}'">
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
    }).join("");

    return `<div class="dep-table-wrap">
      <table class="dep-table">
        <thead><tr>
          <th class="dep-table-th sort-name">Deputat</th>${headers}
        </tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>`;
  }

  /**
   * Circle grid of deputies sized by `metric`. Caller passes the already
   * filtered/subset list; this function sorts it descending by metric.
   * opts: { metric, parties, leg }
   */
  function renderCircles(deps, opts) {
    opts = opts || {};
    const metric = opts.metric || "venituri_ron";
    // valueFn drives circle size/sort (so derived metrics like Scădere can size
    // by magnitude); fmtMetric drives the label format.
    const fmtMetric = opts.fmtMetric || metric;
    const valueFn = opts.valueFn || ((d) => d[metric]);
    const parties = opts.parties || {};
    const leg = opts.leg != null ? opts.leg : 2024;

    if (!deps.length) return '<p style="color:var(--text3);padding:40px 0">Niciun deputat.</p>';

    const sortedDeps = [...deps].sort((a, b) => {
      const av = valueFn(a), bv = valueFn(b);
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      return bv - av;
    });
    const vals = sortedDeps.map(valueFn).filter((v) => v != null && v > 0);
    const maxV = vals.length ? Math.max(...vals) : 1;

    const parts = [];
    let prevMag;
    for (const d of sortedDeps) {
      const v = valueFn(d);
      const mg = magGroup(v);
      if (prevMag !== undefined && mg !== prevMag) parts.push('<div class="mag-break"></div>');
      prevMag = mg;

      const sz = circleSize(v, maxV);
      const isNull = v == null;
      const color = partyColor(d.partid);
      const logo = logoOf(parties, d.partid);
      const showBadge = sz >= 14;
      const detailUrl = `deputat.html?id=${d.cdep_idm}&leg=${leg}`;
      const fontSize = Math.max(8, Math.round(sz * 0.3));

      const badgeHtml = showBadge
        ? logo
          ? `<span class="dep-badge" style="background:${color}"><img src="data/assets/imagini/partide/${logo}" onerror="this.style.display='none'" alt="">${d.partid}</span>`
          : `<span class="dep-badge" style="background:${color}">${d.partid}</span>`
        : "";

      const circleInner = d.image
        ? `<img src="${d.image}" alt="${d.name.replace(/"/g, "&quot;")}"
               onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
           <div class="dep-initials" style="font-size:${fontSize}px;background:${color};display:none">${initials(d.name)}</div>`
        : `<div class="dep-initials" style="font-size:${fontSize}px;background:${color}">${initials(d.name)}</div>`;

      const nameShort = d.name.split(",")[0].trim();
      const maxW = sz + 8;

      parts.push(`<a class="dep-item${isNull ? " null-val" : ""}"
                href="${detailUrl}"
                data-name="${d.name.replace(/"/g, "&quot;")}"
                data-value="${v ?? ""}"
                data-partid="${d.partid}">
        <div class="dep-circle" style="width:${sz}px;height:${sz}px">
          <div class="dep-circle-inner" style="width:${sz}px;height:${sz}px">${circleInner}</div>
          ${badgeHtml}
        </div>
        <div class="dep-name" style="max-width:${maxW}px">${nameShort}</div>
        <div class="dep-value">${isNull ? "—" : fmtValHtml(v, fmtMetric)}</div>
      </a>`);
    }
    return parts.join("");
  }

  global.AVERE = {
    PARTY_COLORS, partyColor, logoOf,
    fmtVal, fmtValHtml, magGroup, circleSize, initials,
    METRIC_KEYS, COLUMNS, colVal, fmtCol,
    renderTable, renderCircles,
  };
})(window);
