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
    (r"privind aprobarea Ordonanței de urgență a Guvernului", "aprobare_oug"),
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
_ACT_PATTERNS: list[tuple[str, str, bool]] = [
    (r"Ordonanț(?:a|ei?|[ăe])\s+de\s+urgență\s+a\s+Guvernului\s+nr\.(\d+)/(\d{4})", "OUG", True),
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

_SUBJECT_PREFIX_TEXT = {
    **_ITEM_TYPE_PREFIX_TEXT,
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


def extract_subject(plain_text: str, item_type: str | None) -> str | None:
    if item_type in _NO_SUBJECT_TYPES:
        return None
    norm = _normalize_ro(plain_text).strip()
    # Strip item-type prefix
    if item_type in _SUBJECT_PREFIX_TEXT:
        prefix = _normalize_ro(_SUBJECT_PREFIX_TEXT[item_type])
        if norm.startswith(prefix):
            norm = norm[len(prefix):].lstrip(" ,\n")
    # Cut at registration number "(PL-x 123/2024)"
    norm = _REG_NR_PAT.sub("", norm, count=1)
    # Cut at law category marker " - lege organică/ordinară"
    norm = re.sub(r"\s*-\s*lege\s+(?:organic[ăa]|ordinar[ăa]).*$", "", norm, flags=re.DOTALL | re.IGNORECASE)
    # Take only the first line (procedural metadata follows on subsequent lines)
    norm = norm.split("\n")[0].strip().rstrip(".")
    return norm or None


# ---------------------------------------------------------------------------
# Top-level extractor
# ---------------------------------------------------------------------------


def extract_entities(descriere: str) -> OrdineZiItemEntities:
    """Extract all entities from a single OrdineZiItem.descriere field."""
    plain = _strip_html(descriere)
    item_type = extract_item_type(plain)
    group, count, itype = extract_initiator(plain)
    return OrdineZiItemEntities(
        item_type=item_type,
        action=extract_action(plain, item_type),
        law_category=extract_law_category(descriere),  # use raw HTML for bold-tag hints
        flags=extract_flags(plain),
        senate_adoption_date=extract_senate_date(plain),
        referenced_acts=extract_referenced_acts(plain),
        commissions=extract_commissions(plain),
        initiator_group=group,
        initiator_count=count,
        initiator_type=itype,
        subject=extract_subject(plain, item_type),
    )
