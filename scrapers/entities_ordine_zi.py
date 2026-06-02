"""Entity extraction from OrdineZiItem.descriere fields.

All extraction is regex/string-based — Romanian parliamentary language uses
highly formulaic phrasing that makes NLP/LLM unnecessary.
"""

from __future__ import annotations

import re
from datetime import date

from schemas.ordine_zi_entities import OrdineZiItemEntities, ReferencedAct


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _normalize_ro(text: str) -> str:
    """Normalize Romanian diacritics to comma-below (canonical) form."""
    return (
        text.replace("ş", "ș")  # ş → ș
        .replace("Ş", "Ș")  # Ş → Ș
        .replace("ţ", "ț")  # ţ → ț
        .replace("Ţ", "Ț")  # Ţ → Ț
    )


def _strip_html(html: str) -> str:
    """Strip HTML tags, converting <br> to newline."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Item type
# ---------------------------------------------------------------------------

_ITEM_TYPE_PREFIXES: list[tuple[str, str]] = [
    # Most specific first
    ("Declarația Parlamentului", "declaratie"),
    ("Dezbaterea și votul asupra moțiunii de cenzură", "motiune_cenzura"),
    ("Dezbaterea moțiunii de cenzură", "motiune_cenzura"),
    ("Dezbaterea moțiunii simple", "motiune_simpla"),
    ("Proiectul de Lege", "proiect_lege"),
    ("Proiectul Legii", "proiect_lege"),              # genitive form: "Proiectul Legii X"
    ("Proiectul de Hotărâre", "proiect_hotarare"),
    ("Proiectul de Hotărare", "proiect_hotarare"),   # cdep.ro variant without â
    ("Propunerea legislativă", "propunere_legislativa"),
    ("Propunere legislativă", "propunere_legislativa"),  # indefinite form
    ("Reexaminarea", "reexaminare"),
    ("Angajarea răspunderii", "angajare_raspundere"),
    ("Dezbateri politice", "dezbateri_politice"),
    ("Dezbateri asupra", "dezbateri"),
    ("Informare privind distribuirea unor documente", "informare_casete"),
    ("Informare", "informare"),
    ("Raportul", "raport"),
    ("Solicitarea", "solicitare"),
    ("Vacantarea", "vacantare"),
    ("Alegerea", "alegere"),
    ("Numirea", "numire"),
    ("Constituirea", "constituire"),
    ("Alocuțiunea", "alocutiune"),
    ("Intervenția", "interventie"),
    ("Mesaje", "mesaj"),
    ("Ședința solemnă", "sedinta_solemna"),
    ("Prezentarea unor alocuțiuni", "alocutiuni"),
    ("Prezentarea", "prezentare"),
    ("Votul asupra", "vot"),
    ("Păstrarea unui moment de reculegere", "moment_reculegere"),
]

# Lowercase versions of prefixes for case-insensitive matching
_ITEM_TYPE_PREFIXES_LOWER = [(p.lower(), slug) for p, slug in _ITEM_TYPE_PREFIXES]


def extract_item_type(plain_text: str) -> str | None:
    # Strip leading dash-bullets from investiture/special sessions
    norm = _normalize_ro(plain_text).lstrip()
    norm_stripped = re.sub(r"^-\s+", "", norm)
    norm_lower = norm_stripped.lower()
    for prefix_lower, slug in _ITEM_TYPE_PREFIXES_LOWER:
        if norm_lower.startswith(prefix_lower):
            return slug
    return None


# ---------------------------------------------------------------------------
# Action (legislative verb phrase)
# ---------------------------------------------------------------------------

# (pattern, slug) — matched against text with item-type prefix stripped, normalized
_ACTION_PATTERNS: list[tuple[str, str]] = [
    (r"privind aprobarea Ordonanței de urgență", "aprobare_oug"),   # "a Guvernului" optional
    (r"privind aprobarea Ordonanței Guvernului", "aprobare_og"),
    (r"(?:pentru|privind) modificarea și completarea", "modificare_si_completare"),
    (r"(?:pentru|privind) modificarea anexei", "modificare_anexa"),
    (r"(?:pentru|privind) modificarea", "modificare"),
    (r"(?:pentru|privind) completarea", "completare"),
    (r"privind abilitarea Guvernului", "abilitare"),
    (r"privind constituirea", "constituire"),
    (r"privind aprobarea componentei nominale", "aprobare_componenta"),
    (r"privind aprobarea structurii", "aprobare"),
    (r"privind aprobarea", "aprobare"),
    (r"privind revocarea", "revocare"),
    (r"privind vacantarea", "vacantare_act"),
    (r"privind transmiterea", "transmitere"),
    (r"privind prorogarea", "prorogare"),
    (r"privind ratificarea", "ratificare"),
    (r"privind instituirea", "instituire"),
    (r"privind declararea", "declarare"),
    (r"privind adoptarea\s+opiniei", "adoptare_opinie"),
]

# Item types where action extraction makes sense (legislative bill types)
_ITEM_TYPE_PREFIX_TEXT: dict[str, str] = {
    "proiect_lege": "Proiectul de Lege",
    "proiect_hotarare": "Proiectul de Hotărâre",
    "propunere_legislativa": "Propunerea legislativă",
    "reexaminare": "Reexaminarea",
}


def extract_action(plain_text: str, item_type: str | None) -> str | None:
    # Only extract action for bill-type items
    if item_type not in _ITEM_TYPE_PREFIX_TEXT:
        return None
    norm = _normalize_ro(plain_text)
    # Strip item-type prefix (case-insensitive by matching from start)
    prefix = _normalize_ro(_ITEM_TYPE_PREFIX_TEXT[item_type])
    norm = re.sub(r"^" + re.escape(prefix) + r"\s*", "", norm, count=1, flags=re.IGNORECASE).lstrip()
    for pattern, slug in _ACTION_PATTERNS:
        if re.search(pattern, norm, re.IGNORECASE):
            return slug
    if re.search(r"\bprivind\b", norm, re.IGNORECASE):
        return "privind"
    return None


# ---------------------------------------------------------------------------
# Law category
# ---------------------------------------------------------------------------


def extract_law_category(raw_html: str) -> str | None:
    norm = _normalize_ro(raw_html)
    if re.search(r"lege\s+organic[ăa]", norm, re.IGNORECASE):
        return "lege_organica"
    if re.search(r"lege\s+ordinar[ăa]", norm, re.IGNORECASE):
        return "lege_ordinara"
    return None


# ---------------------------------------------------------------------------
# Procedural flags
# ---------------------------------------------------------------------------

_FLAG_PATTERNS: list[tuple[str, str]] = [
    (r"Procedur[ăa]\s+de\s+urgență", "procedura_urgenta"),
    (r"Prioritate\s+legislativ[ăa]", "prioritate_legislativa"),
    (r"Camer[ăa]\s+decizional[ăa]", "camera_decizionala"),
    (r"Se\s+dezbate\s+sub\s+rezerva", "rezerva_raport"),
    (r"Retrimis\s+la\s+comisie", "retrimis_comisie"),
    (r"Vot\s+secret\s+cu\s+bile", "vot_secret_bile"),
    (r"Vot\s+deschis\s+electronic", "vot_deschis_electronic"),
    (r"condi[tț]iile\s+articolului\s+115", "adoptat_art115"),
    (r"Sesizare\s+de\s+neconstitu[tț]ionalitate", "sesizare_neconstitutionalitate"),
    (r"cerer(?:ea|ii|e)\s+de\s+reexaminare", "cerere_reexaminare"),
    (r"complex(?:itate)?\s+deosebit[ăa]", "complexitate_deosebita"),
]


def extract_flags(text: str) -> list[str]:
    norm = _normalize_ro(text)
    return [slug for pattern, slug in _FLAG_PATTERNS if re.search(pattern, norm, re.IGNORECASE)]


# ---------------------------------------------------------------------------
# Senate adoption date
# ---------------------------------------------------------------------------


def extract_senate_date(plain_text: str) -> date | None:
    norm = _normalize_ro(plain_text)
    m = re.search(r"[Aa]doptat\s+de\s+[Ss]enat\s*[-–]\s*(\d{1,2})\.(\d{2})\.(\d{4})", norm)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            return None
    return None


# ---------------------------------------------------------------------------
# Referenced acts
# ---------------------------------------------------------------------------

# (pattern, act_type, has_year_group)
# Patterns handle all grammatical forms: nom. (Legea), gen./dat. (Legii), indef. (Lege)
# OUG: "a Guvernului" is optional — cdep.ro sometimes omits it
_ACT_PATTERNS: list[tuple[str, str, bool]] = [
    (r"Ordonanț(?:a|ei?|[ăe])\s+de\s+urgență(?:\s+a\s+Guvernului)?\s+nr\.(\d+)/(\d{4})", "OUG", True),
    (r"Ordonanț(?:a|ei?|[ăe])\s+Guvernului\s+nr\.(\d+)/(\d{4})", "OG", True),
    (r"Leg(?:ea|ii?|e)\s+nr\.(\d+)/(\d{4})", "Lege", True),
    (r"Hotărâr(?:ea|ii?|e)\s+Parlamentului\s+României\s+nr\.(\d+)/(\d{4})", "HotarareParlament", True),
    (r"Hotărâr(?:ea|ii?|e)\s+Camerei\s+Deputaților\s+nr\.(\d+)/(\d{4})", "HotarareCamDepuati", True),
    (r"Deciz(?:ia|iei?|ie)\s+Curții\s+Constituționale\s+nr\.(\d+)", "CCR", False),
]


def extract_referenced_acts(plain_text: str) -> list[ReferencedAct]:
    norm = _normalize_ro(plain_text)
    seen: set[tuple[str, str, int | None]] = set()
    results: list[ReferencedAct] = []
    for pattern, act_type, has_year in _ACT_PATTERNS:
        for m in re.finditer(pattern, norm, re.IGNORECASE):
            nr = m.group(1)
            year: int | None = int(m.group(2)) if has_year else None
            key = (act_type, nr, year)
            if key not in seen:
                seen.add(key)
                results.append(ReferencedAct(act_type=act_type, nr=nr, year=year, raw=m.group(0)))
    return results


# ---------------------------------------------------------------------------
# Commissions
# ---------------------------------------------------------------------------


# Commission slug mapping: (fragment in normalized commission name, slug)
_COMMISSION_SLUG_MAP: list[tuple[str, str]] = [
    ("juridic", "juridica"),
    ("constituționalitate", "constitutionalitate"),
    ("buget", "buget_finante"),
    ("muncă", "munca"),
    ("sănătate", "sanatate"),
    ("învățământ", "invatamant"),
    ("economică", "economica"),
    ("industrii", "industrii"),
    ("agricultură", "agricultura"),
    ("mediu", "mediu"),
    ("transporturi", "transporturi"),
    ("apărare", "aparare"),
    ("politică externă", "politica_externa"),
    ("administrație publică", "administratie_publica"),
    ("drepturile omului", "drepturile_omului"),
    ("egalitate", "egalitate"),
    ("tineretul", "tineret"),
    ("cultură", "cultura"),
    ("tehnologia informației", "it_comunicatii"),
    ("știință", "stiinta"),
    ("violenței domestice", "violenta_domestica"),
    ("specială comună", "speciala_comuna"),
]


def extract_commissions(plain_text: str) -> list[str]:
    """Extract commission names from 'Raport [comun] - Comisia X [și Comisia Y]' patterns."""
    norm = _normalize_ro(plain_text)
    commissions: list[str] = []
    for m in re.finditer(
        r"Raport\s+(?:comun)?\s*[-–]?\s*(Comisia.+?)(?:\s*\(Adoptare\)|\s*\(Aviz\)|\s*distribuit|\s*$)",
        norm,
        re.IGNORECASE | re.MULTILINE,
    ):
        clause = m.group(1).strip()
        # Split on " și Comisia" or ", Comisia" — but only when "Comisia" starts the next token
        parts = re.split(r"\s+și\s+(?=Comisia)|\s*,\s*(?=Comisia)", clause)
        for p in parts:
            p = p.strip().rstrip(",").strip()
            if p:
                commissions.append(p)
    return commissions


def normalize_commission_slug(name: str) -> str | None:
    """Map a commission name to its slug. Returns None if no match found."""
    norm = _normalize_ro(name.lower())
    for fragment, slug in _COMMISSION_SLUG_MAP:
        if fragment in norm:
            return slug
    return None


# ---------------------------------------------------------------------------
# Initiator
# ---------------------------------------------------------------------------


def extract_initiator(plain_text: str) -> tuple[str | None, int | None, str | None]:
    """Returns (group_name, initiator_count, initiator_type)."""
    norm = _normalize_ro(plain_text)

    # "la solicitarea Grupului parlamentar X[, cu tema...]"
    m = re.search(r"solicitarea\s+Grupului\s+parlamentar\s+(.+)", norm, re.IGNORECASE)
    if m:
        raw = m.group(1)
        raw = re.sub(r"\s*,\s+cu\s+tema.*$", "", raw, flags=re.DOTALL)
        return raw.strip().rstrip(".,"), None, None

    # Motions: "inițiate/inițiată de N de deputați și senatori"
    m = re.search(r"inițiat[ăe]\s+de\s+(\d+)\s+de\s+deputați\s+și\s+senatori", norm, re.IGNORECASE)
    if m:
        return None, int(m.group(1)), "deputati_si_senatori"

    m = re.search(r"inițiat[ăe]\s+de\s+(\d+)\s+de\s+senatori", norm, re.IGNORECASE)
    if m:
        return None, int(m.group(1)), "senatori"

    m = re.search(r"inițiat[ăe]\s+de\s+(\d+)\s+de\s+deputați", norm, re.IGNORECASE)
    if m:
        return None, int(m.group(1)), "deputati"

    return None, None, None


# ---------------------------------------------------------------------------
# Subject
# ---------------------------------------------------------------------------

_SUBJECT_PREFIX_TEXT: dict[str, str] = {
    "motiune_simpla": "Dezbaterea moțiunii simple",
    "motiune_cenzura": "Dezbaterea și votul asupra moțiunii de cenzură",
    "informare": "Informare",
    "declaratie": "Declarația Parlamentului",
    "dezbateri_politice": "Dezbateri politice",
    "raport": "Raportul",
    "solicitare": "Solicitarea",
    "vacantare": "Vacantarea",
    "alocutiuni": "Prezentarea unor alocuțiuni",
}

# Items where subject is always the same procedural text — not worth storing
_NO_SUBJECT_TYPES = {"informare_casete", "moment_reculegere"}

# Registration number patterns that mark the end of the subject clause
_REG_NR_PAT = re.compile(
    r"\s*\((?:PL-x|PH\s*CD|PHCD|MS|MC|LP|BP|B)\s*\d+/\d+\)", re.IGNORECASE
)

# Bill item types — for these we extract the topical noun phrase specifically
_BILL_TYPES = frozenset({"proiect_lege", "propunere_legislativa", "reexaminare", "proiect_hotarare"})

# Regex strip patterns for bill-type prefixes (handle case and spelling variants)
_BILL_PREFIX_RE: dict[str, re.Pattern[str]] = {
    "proiect_lege": re.compile(r"^proiectul(?:\s+de\s+lege|\s+legii)\s*", re.IGNORECASE),
    "proiect_hotarare": re.compile(r"^proiectul\s+de\s+hot[ăa]r[âa]?re\s*", re.IGNORECASE),
    "propunere_legislativa": re.compile(r"^propunere[a]?\s+legislativ[ăa]\s*", re.IGNORECASE),
    "reexaminare": re.compile(r"^reexaminarea\s*", re.IGNORECASE),
}


def extract_subject(plain_text: str, item_type: str | None) -> str | None:
    """Extract the topical noun phrase — what the item is substantively about.

    For legislative bills: strips verb and act-reference clauses, returns the
    'privind X' (subject matter) clause that follows the last act number.
    For other items: returns the cleaned first-line description.
    """
    if item_type in _NO_SUBJECT_TYPES:
        return None
    norm = _normalize_ro(plain_text).strip()

    # Strip item-type prefix
    if item_type in _BILL_PREFIX_RE:
        norm = _BILL_PREFIX_RE[item_type].sub("", norm).lstrip(" ,\n")
    elif item_type in _SUBJECT_PREFIX_TEXT:
        prefix = _normalize_ro(_SUBJECT_PREFIX_TEXT[item_type])
        norm = re.sub(r"^" + re.escape(prefix) + r"\s*", "", norm, flags=re.IGNORECASE).lstrip(" ,\n")

    # Cut at registration number and law category marker; take first line
    norm = _REG_NR_PAT.sub("", norm).strip()
    norm = re.sub(r"\s*-\s*lege\s+(?:organic[ăa]|ordinar[ăa]).*$", "", norm, flags=re.DOTALL | re.IGNORECASE)
    norm = norm.split("\n")[0].strip().rstrip(".")
    if not norm:
        return None

    if item_type in _BILL_TYPES:
        # Find the last act number (nr.X/YYYY) — the topic follows it
        last_act: re.Match[str] | None = None
        for m in re.finditer(r"\bnr\.\d+/\d{4}\b", norm, re.IGNORECASE):
            last_act = m
        if last_act:
            remainder = norm[last_act.end():].strip().lstrip(",;")
            # "privind X" clause
            m_p = re.search(r"\bprivind\s+(.+)$", remainder, re.IGNORECASE)
            if m_p:
                return m_p.group(1).strip().rstrip(".")
            # "pentru X" clause (e.g. OUG approved "pentru stabilirea unor măsuri...")
            m_pt = re.search(r"\bpentru\s+(.+)$", remainder, re.IGNORECASE)
            if m_pt:
                return m_pt.group(1).strip().rstrip(".")
            # Act referenced but no descriptive clause in this excerpt
            return None
        # No act reference — strip leading preposition, rest is the topic
        m_v = re.search(r"^(?:privind|pentru|referitoare\s+la)\s+", norm, re.IGNORECASE)
        if m_v:
            return norm[m_v.end():].strip().rstrip(".")

    return norm or None


# ---------------------------------------------------------------------------
# Institutions
# ---------------------------------------------------------------------------

# (label, pattern) — order matters for labelling; most specific first
_INSTITUTION_PATTERNS: list[tuple[str, str]] = [
    # EU institutions — handle both nominative and genitive Romanian forms
    ("Comisia Europeană",
     r"Comisi(?:a|ei)\s+Europe(?:an(?:[aă])?|ne)"),
    ("Parlamentul European",
     r"Parlamentul(?:ui)?\s+European"),
    ("Comitetul Regiunilor",
     r"Comitetul(?:ui)?\s+Regiunilor"),
    ("CESE",
     r"Comitetul(?:ui)?\s+Economic\s+[șsş]i\s+Social\s+European"),
    ("Consiliul UE",
     r"Consiliul(?:ui)?\s+(?:Uniunii\s+Europene|UE)\b"),
    ("Curtea de Justiție UE",
     r"Curtea\s+de\s+Justi[tț]ie\s+(?:a\s+)?Uniunii\s+Europene"),
    ("Banca Centrală Europeană",
     r"B[aă]nc(?:a|ii)\s+Central(?:[aă]|e)\s+European(?:[aă]|e)"),
    # Romanian national institutions — nominative + genitive + no-diacritics
    ("BNR",
     r"B[aă]nc(?:a|ii)\s+Na[tț]ional(?:[aă]|e)\s+a\s+Rom[aâ]niei|BNR\b"),
    ("CSM",
     r"Consiliul(?:ui)?\s+Superior\s+al\s+Magistraturii|CSM\b"),
    ("CCR",
     r"Curtea\s+Constitu[tț]ional(?:[aă]|e)\s+a\s+Rom[aâ]niei|CCR\b"),
    ("Curtea de Conturi",
     r"Curtea\s+de\s+Conturi\b"),
    ("Consiliul Concurenței",
     r"Consiliul(?:ui)?\s+Concuren[tț]ei"),
    ("Consiliul Fiscal",
     r"Consiliul(?:ui)?\s+Fiscal\b"),
    ("Consiliul Legislativ",
     r"Consiliul(?:ui)?\s+Legislativ\b"),
    ("CES România",
     r"Consiliul(?:ui)?\s+Economic\s+[șsş]i\s+Social\b(?!\s+European)"),
    ("ANCOM",                r"\bANCOM\b"),
    ("ANPC",                 r"\bANPC\b"),
    ("Loteria Română",       r"Loteria\s+Rom[aâ]n(?:[aă])?"),
    # Specialized bodies
    ("Inspecția Muncii",
     r"Inspecți(?:a|ei)\s+Muncii"),
    ("Academia de Științe Agricole",
     r"Academi(?:a|ei)\s+de\s+[Șș]tiin[țt]e\s+Agricole(?:\s+[șs]i\s+Silvice)?|ASAS\b"),
    ("RA-APPS",
     r"Regia\s+Autonom[aă]\s+Administrați(?:a|ei)\s+Patrimoniului\s+Protocolului\s+de\s+Stat|RA-APPS\b"),
]

_INSTITUTION_RE: list[tuple[str, re.Pattern[str]]] = [
    (label, re.compile(pat, re.IGNORECASE))
    for label, pat in _INSTITUTION_PATTERNS
]


def extract_institutions(plain_text: str) -> list[str]:
    """Return deduplicated list of institution labels found in the text."""
    norm = _normalize_ro(plain_text)
    return [label for label, rx in _INSTITUTION_RE if rx.search(norm)]


# ---------------------------------------------------------------------------
# Top-level extractor
# ---------------------------------------------------------------------------


def extract_entities(descriere: str) -> OrdineZiItemEntities:
    """Extract all entities from a single OrdineZiItem.descriere field."""
    plain = _strip_html(descriere)
    item_type = extract_item_type(plain)
    group, count, itype = extract_initiator(plain)
    commissions = extract_commissions(plain)
    commission_slugs = [s for c in commissions if (s := normalize_commission_slug(c)) is not None]
    return OrdineZiItemEntities(
        item_type=item_type,
        action=extract_action(plain, item_type),
        law_category=extract_law_category(descriere),  # use raw HTML for bold-tag hints
        flags=extract_flags(plain),
        senate_adoption_date=extract_senate_date(plain),
        referenced_acts=extract_referenced_acts(plain),
        commissions=commissions,
        commission_slugs=commission_slugs,
        institutions=extract_institutions(plain),
        initiator_group=group,
        initiator_count=count,
        initiator_type=itype,
        subject=extract_subject(plain, item_type),
    )
