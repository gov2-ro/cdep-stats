/**
 * Sistem i18n minimal pentru cdep-api-poc.
 *
 * Traduce UI chrome (nav, butoane, label-uri, footer). Datele propriu-zise
 * (nume deputați, titluri proiecte, descrieri voturi) rămân în română —
 * ele provin direct de la cdep.ro și au valoare de sursă oficială.
 *
 * Folosire în HTML:
 *   <span data-i18n="search">Caută</span>
 *   <button data-i18n-attr="aria-label:close">×</button>
 *   <input data-i18n-attr="placeholder:search_placeholder">
 *
 * Limba e persistentă în localStorage și se aplică la fiecare load.
 */

const I18N = {
  ro: {
    // Nav
    back: "← Înapoi",
    home: "Pagina principală",
    docs: "Documentație",
    demo: "Demo",
    stats: "Statistici",
    nav_avere: "Averi",
    search: "Caută",
    swagger: "Swagger UI",
    status: "Status API",
    open_data: "Date deschise",

    // Common labels
    loading: "Se încarcă...",
    error: "Eroare",
    no_results: "Niciun rezultat",
    not_found: "Nu a fost găsit",
    source: "Sursa",
    page_main: "Pagina principală",

    // Profile pages
    legislatura: "Legislatura",
    party: "Partid",
    group: "Grup parlamentar",
    county: "Județ",
    role: "Rol",
    activity: "Activitate",
    committees: "Comisii",
    delegations: "Delegații",
    friendship_groups: "Grupuri de prietenie",
    profile_official: "Profil oficial cdep.ro",

    // Vote page
    vote_final: "Vot final",
    for: "Pentru",
    against: "Contra",
    abstain: "Abțineri",
    not_voted: "Nu au votat",
    present: "Prezenți",
    adopted: "Adoptat",
    rejected: "Respins",
    distribution_votes: "Distribuție voturi",
    distribution_parties: "Distribuție pe partide",
    nominal_votes: "Voturi nominale",
    by_party: "Defalcare pe partide",
    name: "Nume",
    vote: "Vot",
    filter_name: "Caută nume...",
    all_parties: "Toate partidele",
    all_options: "Toate opțiunile",

    // Projects
    project: "Proiect",
    timeline: "Timeline procedural",
    initiator: "Inițiator",
    decisional_chamber: "Cameră decizională",
    stage: "Stadiu",
    promulgated: "Promulgat",
    in_progress: "În lucru",
    urgency: "Procedură urgență",
    amendments: "Amendamente",
    accepted: "admise",
    declined: "respinse",
    deadline: "Termen depunere",
    pdf_documents: "Documente PDF",
    full_committee_report: "Lista completă în raportul comisiei (PDF)",

    // Motiuni
    motion_simple: "Moțiune simplă",
    motion_censure: "Moțiune de cenzură",
    signers: "Semnatari",
    in_procedure: "În procedură",
    withdrawn: "Retrasă",

    // Sanctions
    sanction: "Sancțiune",
    sanction_diminuare: "Diminuare indemnizație",
    sanction_avertisment: "Avertisment scris",
    sanction_chemare: "Chemare la ordine",
    sanction_retragere: "Retragere cuvânt",
    sanction_other: "Altă sancțiune",
    description: "Descriere",
    decision: "Decizia",
    date: "Data",

    // Status
    operational: "Sistem operațional",
    freshness: "prospețime",
    total_entities: "Entități totale",
    total_files: "Fișiere JSON",
    total_size: "Total date",
    build_version: "Build version",
    endpoints: "Endpoint-uri",
    infrastructure: "Infrastructură",
    records: "Records",
    files: "Fișiere",
    size: "Mărime",

    // Footer
    data_from: "Date din",
    license: "Licență",

    // Landing page
    hero_title_1: "Date parlamentare,",
    hero_title_2: "deschise pentru toți",
    hero_desc:
      "API REST public pentru datele Camerei Deputaților. Voturi, prezențe, proiecte legislative — în format JSON, accesibil oricui. Dezvoltat în colaborare cu Comisia pentru Tehnologia Informației și Comunicațiilor pentru transparentizarea activității parlamentare.",
    hero_btn_explore: "Explorează API",
    hero_btn_search: "Caută în date",
    hero_btn_download: "Descarcă OpenAPI spec",
    stat_deputati: "Deputați",
    stat_voturi: "Voturi",
    stat_proiecte: "Proiecte de lege",
    stat_interpelari: "Interpelări",
    stat_comisii: "Comisii",
    stat_sanctiuni: "Sancțiuni",
    sidebar_endpoints: "Endpoint-uri",
    sidebar_resources: "Resurse",
    sidebar_info: "Info",
    info_text:
      "Inițiativă pentru transparentizare guvernamentală. Date: publice, sursă cdep.ro. Autor: Cătălin Popa. În colaborare cu Comisia pentru Tehnologia Informației și Comunicațiilor",
    api_reference: "Referință API",
    api_reference_desc: "Toate endpoint-urile returnează JSON. Autentificare: nu este necesară (date publice).",
    footer_text:
      "cdep.api — Inițiativă pentru transparentizare guvernamentală · În colaborare cu Comisia pentru Tehnologia Informației și Comunicațiilor · Cătălin Popa",

    // Search page
    search_title: "Caută în Camera Deputaților",
    search_subtitle:
      "API public open-data · deputați, voturi, sancțiuni, interpelări · date din cdep.ro",
    search_examples: "Exemple căutări",

    // Profile common
    contact: "Contact",
    biography: "Biografie",
    raw_json: "Date raw JSON",
    full_profile: "Profil complet în format API",
    motions_signed: "moțiuni semnate",
    interpellations_addressed: "interpelări adresate",
    with_signature: "Cu semnătura acestui deputat",
    addressed_to: "Adresate de acest deputat",
    documents: "Documente",
    full_text: "Text complet",
    proj_data: "Date proiect",
    details: "Detalii",
  },
  en: {
    // Nav
    back: "← Back",
    home: "Home",
    docs: "Documentation",
    demo: "Demo",
    stats: "Statistics",
    nav_avere: "Wealth",
    search: "Search",
    swagger: "Swagger UI",
    status: "API Status",
    open_data: "Open data",

    // Common labels
    loading: "Loading...",
    error: "Error",
    no_results: "No results",
    not_found: "Not found",
    source: "Source",
    page_main: "Home page",

    // Profile pages
    legislatura: "Legislature",
    party: "Party",
    group: "Parliamentary group",
    county: "County",
    role: "Role",
    activity: "Activity",
    committees: "Committees",
    delegations: "Delegations",
    friendship_groups: "Friendship groups",
    profile_official: "Official profile cdep.ro",

    // Vote page
    vote_final: "Final vote",
    for: "For",
    against: "Against",
    abstain: "Abstentions",
    not_voted: "Did not vote",
    present: "Present",
    adopted: "Adopted",
    rejected: "Rejected",
    distribution_votes: "Vote distribution",
    distribution_parties: "Distribution by party",
    nominal_votes: "Nominal votes",
    by_party: "Breakdown by party",
    name: "Name",
    vote: "Vote",
    filter_name: "Search name...",
    all_parties: "All parties",
    all_options: "All options",

    // Projects
    project: "Project",
    timeline: "Procedural timeline",
    initiator: "Initiator",
    decisional_chamber: "Decisional chamber",
    stage: "Stage",
    promulgated: "Promulgated",
    in_progress: "In progress",
    urgency: "Urgency procedure",
    amendments: "Amendments",
    accepted: "accepted",
    declined: "declined",
    deadline: "Submission deadline",
    pdf_documents: "PDF documents",
    full_committee_report: "Full list in committee report (PDF)",

    // Motiuni
    motion_simple: "Simple motion",
    motion_censure: "Motion of censure",
    signers: "Signers",
    in_procedure: "In procedure",
    withdrawn: "Withdrawn",

    // Sanctions
    sanction: "Sanction",
    sanction_diminuare: "Allowance reduction",
    sanction_avertisment: "Written warning",
    sanction_chemare: "Call to order",
    sanction_retragere: "Speech retraction",
    sanction_other: "Other sanction",
    description: "Description",
    decision: "Decision",
    date: "Date",

    // Status
    operational: "System operational",
    freshness: "freshness",
    total_entities: "Total entities",
    total_files: "JSON files",
    total_size: "Total data",
    build_version: "Build version",
    endpoints: "Endpoints",
    infrastructure: "Infrastructure",
    records: "Records",
    files: "Files",
    size: "Size",

    // Footer
    data_from: "Data from",
    license: "License",

    // Landing page
    hero_title_1: "Parliamentary data,",
    hero_title_2: "open to everyone",
    hero_desc:
      "Public REST API for the Romanian Chamber of Deputies. Votes, attendance, legislative projects — in JSON, accessible to all. Developed in collaboration with the Committee for Information Technology and Communications to make parliamentary activity more transparent.",
    hero_btn_explore: "Explore API",
    hero_btn_search: "Search in data",
    hero_btn_download: "Download OpenAPI spec",
    stat_deputati: "Deputies",
    stat_voturi: "Votes",
    stat_proiecte: "Bills",
    stat_interpelari: "Interpellations",
    stat_comisii: "Committees",
    stat_sanctiuni: "Sanctions",
    sidebar_endpoints: "Endpoints",
    sidebar_resources: "Resources",
    sidebar_info: "Info",
    info_text:
      "An initiative for governmental transparency. Data: public, source cdep.ro. Author: Cătălin Popa. In collaboration with the Committee for Information Technology and Communications",
    api_reference: "API reference",
    api_reference_desc: "All endpoints return JSON. Authentication: none required (public data).",
    footer_text:
      "cdep.api — An initiative for governmental transparency · In collaboration with the Committee for Information Technology and Communications · Cătălin Popa",

    // Search page
    search_title: "Search the Chamber of Deputies",
    search_subtitle:
      "Public open-data API · deputies, votes, sanctions, interpellations · data from cdep.ro",
    search_examples: "Search examples",

    // Profile common
    contact: "Contact",
    biography: "Biography",
    raw_json: "Raw JSON data",
    full_profile: "Full profile in API format",
    motions_signed: "motions signed",
    interpellations_addressed: "interpellations addressed",
    with_signature: "With this deputy's signature",
    addressed_to: "Addressed by this deputy",
    documents: "Documents",
    full_text: "Full text",
    proj_data: "Project data",
    details: "Details",
  },
};

const I18N_LANG_KEY = "cdep_lang";

function getLang() {
  return localStorage.getItem(I18N_LANG_KEY) || "ro";
}

function setLang(lang) {
  if (lang !== "ro" && lang !== "en") return;
  localStorage.setItem(I18N_LANG_KEY, lang);
  document.documentElement.lang = lang;
  applyI18n();
  // Notifică pagini dinamice că s-a schimbat limba
  document.dispatchEvent(new CustomEvent("langchange", { detail: { lang } }));
}

function t(key) {
  const lang = getLang();
  return (I18N[lang] && I18N[lang][key]) || (I18N.ro[key] || key);
}

function applyI18n() {
  // Text content: data-i18n="key"
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    if (key) el.textContent = t(key);
  });
  // Attribute: data-i18n-attr="placeholder:key" sau "aria-label:key,title:key"
  document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
    const spec = el.getAttribute("data-i18n-attr");
    spec.split(",").forEach((pair) => {
      const [attr, key] = pair.split(":").map((s) => s.trim());
      if (attr && key) el.setAttribute(attr, t(key));
    });
  });
}

function injectLangToggle() {
  // Inserează butonul în nav (header) dacă există un slot dedicat
  const slot = document.getElementById("lang-toggle-slot");
  if (!slot) return;

  const lang = getLang();
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "lang-toggle";
  btn.textContent = lang === "ro" ? "EN" : "RO";
  btn.setAttribute("aria-label", lang === "ro" ? "Switch to English" : "Schimbă în română");
  btn.title = btn.getAttribute("aria-label");
  btn.style.cssText =
    "background:transparent;border:1px solid currentColor;color:inherit;font-size:11px;font-weight:600;padding:4px 10px;border-radius:4px;cursor:pointer;font-family:inherit;letter-spacing:0.5px";
  btn.addEventListener("click", () => {
    sessionStorage.setItem("i18n_transitioning", "1");
    document.body.style.transition = "opacity 0.25s ease";
    document.body.style.opacity = "0";
    setTimeout(() => {
      setLang(lang === "ro" ? "en" : "ro");
      location.reload();
    }, 250);
  });
  slot.appendChild(btn);
}

function fadeInIfTransitioning() {
  if (sessionStorage.getItem("i18n_transitioning") !== "1") return;
  sessionStorage.removeItem("i18n_transitioning");
  document.body.style.opacity = "0";
  requestAnimationFrame(() => {
    document.body.style.transition = "opacity 0.4s ease";
    document.body.style.opacity = "1";
  });
}

// Auto-init la load
document.addEventListener("DOMContentLoaded", () => {
  document.documentElement.lang = getLang();
  applyI18n();
  injectLangToggle();
  fadeInIfTransitioning();
});
