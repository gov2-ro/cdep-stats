"""PDF parser pentru declarații de interese ANI.

Funcția principală: parse_pdf(pdf_path) -> dict
Returnează un dict cu câmpurile InteresDeclaratie (fără pdf_url/data_depunere).

Structura PDF-ului ANI (formular standardizat, 2 pagini):
  §1  Asociat/Acționar la societăți comerciale / ONG-uri
  §2  Calitatea de conducere/administrare
  §3  Asociații profesionale/sindicale
  §4  Funcții în partide politice
  §5  Contracte cu instituții publice (Titular / Soț / Rude / Societăți)
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore[assignment]


# ── Section delimiters ────────────────────────────────────────────────────────

SEC_MARKERS = [
    "1. Asociat sau ac",  # §1 — short prefix to match both ţionar / ționar
    "2. Calitatea de membru în organele de conducere, administrare",  # §2
    "3. Calitatea de membru în cadrul asocia",  # §3
    "4. Calitatea de membru în organele de conducere, administrare şi control, retribuite",  # §4
    "5. Contracte",  # §5
    "Prezenta declara",  # footer
]

# §5 sub-section headers (beneficiary type)
SEC5_SUBSECTIONS = [
    ("titular", "Titular"),
    ("sot_sotie", "Soţ/soţie"),
    ("sot_sotie", "Soț/soție"),
    ("rude", "Rude de gradul I"),
    ("societate_comerciala", "Societăţi comerciale"),
    ("societate_comerciala", "Societăți comerciale"),
]

# ── Regexes ───────────────────────────────────────────────────────────────────

ENTRY_SPLIT_RE = re.compile(r"(?=^\d+\.\d+\s)", re.MULTILINE)
SEC4_ENTRY_RE = re.compile(r"^4\.\d+\s+(.+)", re.MULTILINE)

CALITATE_SEC1_RE = re.compile(
    r"\b(Asociat|Ac[tţ]ionar|Fondator|Membru)\b", re.IGNORECASE
)
CALITATE_SEC2_RE = re.compile(
    r"\b(Administrator|Pre[şș]edinte|Vicepre[şș]edinte|Cenzor|Fondator|Altele)\b",
    re.IGNORECASE,
)
NR_TITLURI_RE = re.compile(
    r"\b(\d+)\s+(?:Păr[tţ]i\s+sociale|Ac[tţ]iuni|Parti\s+sociale)\b", re.IGNORECASE
)
TIP_TITLURI_RE = re.compile(
    r"(Păr[tţ]i\s+sociale|Ac[tţ]iuni|Parti\s+sociale)", re.IGNORECASE
)
VALOARE_RON_RE = re.compile(r"(\d[\d.,]*)\s*RON", re.IGNORECASE)
DATE_RE = re.compile(
    r"Data complet[aă]rii\s+Semn[aă]tura\s+(\d{2}-\d{2}-\d{4})", re.IGNORECASE
)
ANI_ID_RE = re.compile(r"^\d{6,9}")
TIP_DECL_RE = re.compile(
    r"(30 de zile de la num[iî]re|30 de zile de la [îi]ncetare|Anual[,\s])",
    re.IGNORECASE,
)
# Company name patterns for §5
BENEFICIAR_RE = re.compile(
    r"\b(?:SC|SRL|SA|RA|SNC|SCS|CABINET INDIVIDUAL|PFA|ASOCIATIA|FUNDATIA)\b",
    re.IGNORECASE,
)
# Lines to strip before emptiness check in §5 blocks:
#   - footnote markers "1)", "2)"
#   - table-header continuation lines starting with "/" ("/ Persoană fizică...")
#   - page-number markers "1 / 2"
#   - lowercase-starting lines (table header continuation: "asociate, ...", "desfăşoară...")
_FOOTNOTE_LINE_RE = re.compile(
    r"^\d+\).*$"  # footnote markers
    r"|^/.*$"  # "/" continuation lines
    r"|^\d+\s*/\s*\d+$"  # page markers "1 / 2"
    r"|^[a-z].*$",  # lowercase-starting lines (boilerplate continuation)
    re.MULTILINE,
)


# ── Utilities ─────────────────────────────────────────────────────────────────


def _extract_section(text: str, marker: str, next_markers: list[str]) -> str:
    start = text.find(marker)
    if start < 0:
        return ""
    end = len(text)
    for nm in next_markers:
        idx = text.find(nm, start + len(marker))
        if 0 < idx < end:
            end = idx
    return text[start:end]


def _is_empty_entry(text: str) -> bool:
    """True if the entry is only dashes / whitespace."""
    stripped = re.sub(r"[\s\-–]+", "", text)
    return len(stripped) == 0


def _parse_amount(s: str) -> float | None:
    s = s.replace(" ", "").strip()
    if not s:
        return None
    # Handle both comma-as-decimal and dot-as-decimal
    if "." in s and "," in s:
        s = (
            s.replace(".", "").replace(",", ".")
            if s.rindex(",") > s.rindex(".")
            else s.replace(",", "")
        )
    elif "," in s:
        parts = s.split(",")
        s = s.replace(",", ".") if len(parts[-1]) <= 2 else s.replace(",", "")
    elif "." in s:
        parts = s.split(".")
        if len(parts[-1]) == 3 and len(parts) >= 2:
            s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date_dmy(s: str) -> date | None:
    """DD-MM-YYYY or DD.MM.YYYY → date."""
    m = re.match(r"(\d{2})[-.](\d{2})[-.](\d{4})", s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


# ── §1 parser ─────────────────────────────────────────────────────────────────


def _parse_companii(sec1: str) -> list[dict]:
    """Parse §1 entries: company stakes / association memberships."""
    results: list[dict] = []
    blocks = ENTRY_SPLIT_RE.split(sec1)
    for block in blocks:
        block = block.strip()
        if not block or _is_empty_entry(block):
            continue
        # Only process blocks that actually start with an N.M entry index
        if not re.match(r"^\d+\.\d+\s", block):
            continue
        # Strip leading index "1.1 ", "1.2 " etc.
        block = re.sub(r"^\d+\.\d+\s+", "", block, count=1)

        cal_m = CALITATE_SEC1_RE.search(block)
        if not cal_m:
            continue

        # Company name = everything before calitate word, first line
        before = block[: cal_m.start()].strip()
        denumire = before.splitlines()[0].strip().rstrip("-").strip()
        if not denumire:
            continue

        calitate = cal_m.group(1).capitalize()

        # Nr titluri and tip
        nr_m = NR_TITLURI_RE.search(block)
        nr_titluri = int(nr_m.group(1)) if nr_m else None

        tip_m = TIP_TITLURI_RE.search(block)
        tip_titluri = tip_m.group(1).strip() if tip_m else None

        # Valoare RON — last match wins (usually the total)
        val_matches = list(VALOARE_RON_RE.finditer(block))
        valoare_ron: float | None = None
        for vm in reversed(val_matches):
            v = _parse_amount(vm.group(1))
            if v is not None:
                valoare_ron = v
                break

        results.append(
            {
                "denumire": denumire,
                "calitate": calitate,
                "nr_titluri": nr_titluri,
                "tip_titluri": tip_titluri,
                "valoare_ron": valoare_ron,
            }
        )
    return results


# ── §2 parser ─────────────────────────────────────────────────────────────────


def _parse_conducere(sec2: str) -> list[dict]:
    """Parse §2 entries: governance / board roles."""
    results: list[dict] = []
    blocks = ENTRY_SPLIT_RE.split(sec2)
    for block in blocks:
        block = block.strip()
        if not block or _is_empty_entry(block):
            continue
        # Only process blocks that start with an N.M entry index
        if not re.match(r"^\d+\.\d+\s", block):
            continue
        block = re.sub(r"^\d+\.\d+\s+", "", block, count=1)

        # Company name = first line
        first_line = block.splitlines()[0].strip().rstrip("-").strip()
        if not first_line:
            continue

        cal_m = CALITATE_SEC2_RE.search(block)
        calitate = cal_m.group(1).capitalize() if cal_m else None

        val_matches = list(VALOARE_RON_RE.finditer(block))
        valoare: float | None = None
        for vm in reversed(val_matches):
            v = _parse_amount(vm.group(1))
            if v is not None:
                valoare = v
                break

        results.append(
            {
                "denumire": first_line,
                "calitate_conducere": calitate,
                "valoare_beneficii_ron": valoare,
            }
        )
    return results


# ── §3 parser ─────────────────────────────────────────────────────────────────


def _parse_asociatii_profesionale(sec3: str) -> str | None:
    """Return the §3 content as raw text, or None if empty."""
    # Strip the section header
    text = re.sub(
        r"^3\. Calitatea de membru.*?\n",
        "",
        sec3,
        flags=re.IGNORECASE | re.DOTALL,
        count=1,
    )
    text = text.strip()
    if not text or _is_empty_entry(text):
        return None
    return text


# ── §4 parser ─────────────────────────────────────────────────────────────────


def _parse_partide(sec4: str) -> list[str]:
    """Return list of raw 'Partid - Funcție' strings from §4."""
    results: list[str] = []
    for m in SEC4_ENTRY_RE.finditer(sec4):
        val = m.group(1).strip()
        if not val or _is_empty_entry(val):
            continue
        results.append(val)
    return results


# ── §5 parser ─────────────────────────────────────────────────────────────────


def _parse_contracte(sec5: str) -> list[dict]:
    """Parse §5 public contracts.

    The table is scrambled by pdfplumber column merging. We detect each
    beneficiary sub-section (Titular / Soț / Rude / Societăți) and within each,
    extract any company/person names and RON values. One InteresContract per
    non-empty sub-section block.
    """
    results: list[dict] = []

    # Build list of (beneficiar_tip, start_idx) for each sub-section found
    subsec_positions: list[tuple[str, int]] = []
    for tip, header in SEC5_SUBSECTIONS:
        idx = sec5.find(header)
        if idx >= 0:
            # Deduplicate by position (Romanian chars variant hits twice)
            if not any(abs(idx - p) < 5 for _, p in subsec_positions):
                subsec_positions.append((tip, idx))

    subsec_positions.sort(key=lambda x: x[1])

    for i, (tip, start) in enumerate(subsec_positions):
        end = subsec_positions[i + 1][1] if i + 1 < len(subsec_positions) else len(sec5)
        block = sec5[start:end]

        # Skip the sub-section header line itself
        block_body = block.split("\n", 1)[1] if "\n" in block else ""

        # Strip footnote lines and table header continuations
        block_body_clean = _FOOTNOTE_LINE_RE.sub("", block_body).strip()
        # Truncate at the last dash-row: anything after it is footnote body text
        _DASHES = "- - - - - - -"
        last_dash = block_body_clean.rfind(_DASHES)
        if last_dash >= 0:
            block_body_clean = block_body_clean[: last_dash + len(_DASHES)]
        if _is_empty_entry(block_body_clean):
            continue

        # Extract RON values (join lines first; use cleaned block to skip footnotes)
        joined = " ".join(block_body_clean.split())
        val_matches = list(VALOARE_RON_RE.finditer(joined))
        valoare_ron: float | None = None
        # Sum all values in this sub-block (multiple contracts possible)
        total = 0.0
        for vm in val_matches:
            v = _parse_amount(vm.group(1))
            if v is not None and v > 0:
                total += v
        if total > 0:
            valoare_ron = total

        # Try to extract beneficiary name (first SRL/SA/CABINET/PFA match)
        beneficiar_denumire: str | None = None
        lines = [ln.strip() for ln in block_body_clean.splitlines() if ln.strip()]
        for line in lines:
            if BENEFICIAR_RE.search(line) or (
                line
                and line[0].isupper()
                and len(line) > 4
                and not line.startswith("-")
            ):
                # Take the first substantive line that looks like a name
                candidate = line.split("  ")[0].strip()
                if candidate and not _is_empty_entry(candidate) and len(candidate) > 3:
                    beneficiar_denumire = candidate
                    break

        # Extract date (DD.MM.YYYY)
        date_m = re.search(r"\b(\d{2}[./]\d{2}[./]\d{4})\b", block_body_clean)
        data_incheiere = _parse_date_dmy(date_m.group(1)) if date_m else None

        # Contract type hint
        tip_contract: str | None = None
        if re.search(r"LUCRARI|LUCRĂRI", block_body_clean, re.IGNORECASE):
            tip_contract = "lucrari"
        elif re.search(
            r"ASISTEN[TŢ][AĂ]\s+JURIDIC[AĂ]", block_body_clean, re.IGNORECASE
        ):
            tip_contract = "asistenta_juridica"
        elif re.search(r"CONSULTAN[TŢ][AĂ]", block_body_clean, re.IGNORECASE):
            tip_contract = "consultanta"
        elif re.search(r"FURNIZARE", block_body_clean, re.IGNORECASE):
            tip_contract = "furnizare"

        results.append(
            {
                "beneficiar_tip": tip,
                "beneficiar_denumire": beneficiar_denumire,
                "institutie_contractanta": None,  # too scrambled to parse reliably
                "tip_contract": tip_contract,
                "valoare_ron": valoare_ron,
                "data_incheiere": data_incheiere.isoformat()
                if data_incheiere
                else None,
            }
        )

    return results


# ── Public entry point ────────────────────────────────────────────────────────


def parse_pdf(pdf_path: Path) -> dict:
    """Parse an ANI interest declaration PDF.

    Returns a dict matching InteresDeclaratie fields (excluding pdf_url / data_depunere).
    """
    result: dict = {
        "ani_id": None,
        "tip_declaratie": None,
        "data_completarii": None,
        "text_extracted": False,
        "error": None,
        "companii": [],
        "nr_companii": 0,
        "conducere": [],
        "asociatii_profesionale_raw": None,
        "partide_raw": [],
        "are_functie_partid": False,
        "contracte": [],
        "are_contracte_publice": False,
        "contracte_total_ron": 0.0,
    }

    if pdfplumber is None:
        result["error"] = "pdfplumber not installed"
        return result

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception as e:
        result["error"] = f"PDF read failed: {e}"
        return result

    if len(full_text.strip()) < 100:
        result["error"] = "PDF scanat (text < 100 chars)"
        return result

    result["text_extracted"] = True

    # ── Header fields ─────────────────────────────────────────────────────────
    ani_m = ANI_ID_RE.match(full_text.strip())
    if ani_m:
        result["ani_id"] = ani_m.group()

    tip_m = TIP_DECL_RE.search(full_text)
    if tip_m:
        raw = tip_m.group(1).lower()
        if "num" in raw:
            result["tip_declaratie"] = "numire"
        elif "ncetare" in raw or "incetare" in raw:
            result["tip_declaratie"] = "incetare"
        else:
            result["tip_declaratie"] = "anual"

    date_m = DATE_RE.search(full_text)
    if date_m:
        result["data_completarii"] = _parse_date_dmy(date_m.group(1))

    # ── Sections ──────────────────────────────────────────────────────────────
    sec1 = _extract_section(full_text, SEC_MARKERS[0], SEC_MARKERS[1:])
    sec2 = _extract_section(full_text, SEC_MARKERS[1], SEC_MARKERS[2:])
    sec3 = _extract_section(full_text, SEC_MARKERS[2], SEC_MARKERS[3:])
    sec4 = _extract_section(full_text, SEC_MARKERS[3], SEC_MARKERS[4:])
    sec5 = _extract_section(full_text, SEC_MARKERS[4], SEC_MARKERS[5:])

    # §1
    companii = _parse_companii(sec1)
    result["companii"] = companii
    result["nr_companii"] = len(companii)

    # §2
    result["conducere"] = _parse_conducere(sec2)

    # §3
    result["asociatii_profesionale_raw"] = _parse_asociatii_profesionale(sec3)

    # §4
    partide = _parse_partide(sec4)
    result["partide_raw"] = partide
    result["are_functie_partid"] = len(partide) > 0

    # §5
    contracte = _parse_contracte(sec5)
    result["contracte"] = contracte
    result["are_contracte_publice"] = len(contracte) > 0
    result["contracte_total_ron"] = sum(
        c["valoare_ron"] for c in contracte if c.get("valoare_ron")
    )

    return result
