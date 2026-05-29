# Avere PDF Full Extraction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract all fields from ANI wealth declaration PDFs — currently 4 sections are unread and all per-row detail lists are empty — to power a complete deputy profile card.

**Architecture:** Extract the parser into a dedicated `parsers/avere_pdf.py` module (shared by both build scripts), add 4 new parsing helpers for detail lists, add 3 new scalar-only sections, fix a latent double-counting bug in conturi vs. plasamente, and wire everything into `parse_pdf()`. Schema (`schemas/avere.py`) gains 3 new models, 11 new fields on `AvereDeclaratie`, and new snapshot fields on `AvereDeputat`/`AvereSummary`.

**Tech Stack:** Python 3.11+, pdfplumber, pydantic v2, regex, pytest

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `schemas/avere.py` | Modify | Add `VehiculDetail`, `ContDetail`, `PlasamentDetail`; update `AvereImobil`; add 11 fields to `AvereDeclaratie`; add 2 to `AvereDeputat`; add 3 to `AvereSummary` |
| `parsers/__init__.py` | Create | Empty package marker |
| `parsers/avere_pdf.py` | Create | All PDF parsing logic (regexes, helpers, new detail parsers, `parse_pdf()`) |
| `scripts/build_declaratii_avere.py` | Modify | Import `parse_pdf` from `parsers.avere_pdf`; update `process_deputat` snapshot fields |
| `scripts/analiza_avere_pdf.py` | Modify | Replace its own `parse_pdf` with import from `parsers.avere_pdf` |
| `tests/test_avere_pdf_parser.py` | Create | Unit tests for every new parsing function using synthetic text |

---

## Task 1 — Schema additions

**Files:**
- Modify: `schemas/avere.py`

- [ ] **Step 1: Replace the full contents of `schemas/avere.py`**

```python
"""Schema pentru averile parsate din PDF-urile ANI."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class AvereImobil(BaseModel):
    """Un teren sau o clădire declarată."""

    tip: str = Field(description="'teren' | 'cladire'")
    categorie: str = Field(
        description="agricol | forestier | intravilan | luciu_apa | extravilan"
        " | apartament | locuinta | vacanta | comercial | alte_cladiri | necunoscuta"
    )
    suprafata_mp: float | None = None
    judet: str | None = None
    an_dobandirii: int | None = None
    cota_parte: str | None = None
    modul_dobandirii: str | None = None


class VehiculDetail(BaseModel):
    """Un autovehicul / mijloc de transport declarat."""

    natura: str
    marca: str | None = None
    an_fabricatie: int | None = None
    mod_dobandire: str | None = None


class ContDetail(BaseModel):
    """Un cont bancar / depozit / fond declarat (IV.1)."""

    institutie: str | None = None
    tip: str | None = None  # "cont_curent" | "depozit" | "fond_investitii"
    valuta: str = "RON"
    an_deschis: int | None = None
    sold_ron: float = 0.0


class PlasamentDetail(BaseModel):
    """O investiție directă / acțiuni SRL / împrumut acordat (IV.2)."""

    emitent: str | None = None
    tip: str | None = None  # "actiuni" | "parti_sociale" | "titluri_stat" | "imprumut"
    nr_titluri: str | None = None  # e.g. "100 %" or "1/3"
    valoare_ron: float = 0.0


class AvereDeclaratie(BaseModel):
    """O declarație individuală depusă la o anumită dată."""

    data_depunere: date | None = Field(description="Data depunerii la ANI")
    pdf_url: HttpUrl
    text_extracted: bool = Field(description="True dacă pdfplumber a citit text")
    error: str | None = None

    # I. Imobile — agregate
    terenuri_count: int = 0
    cladiri_count: int = 0
    suprafata_total_mp: float = 0.0
    suprafata_agricol_mp: float = 0.0
    suprafata_forestier_mp: float = 0.0
    suprafata_intravilan_mp: float = 0.0
    suprafata_luciu_mp: float = 0.0
    suprafata_alte_mp: float = 0.0
    suprafata_cladiri_mp: float = 0.0

    # II.1 Auto
    auto_count: int = Field(default=0, description="Nr. vehicule declarate")

    # II.2 Metale prețioase / bijuterii / artă
    bijuterii_total_ron: float = 0.0

    # III. Bunuri înstrăinate (ultimele 12 luni)
    bunuri_instrainate_count: int = 0
    bunuri_instrainate_total_ron: float = 0.0

    # IV.1 Conturi
    conturi_total_ron: float = Field(default=0.0, description="Active financiare în RON")

    # IV.2 Plasamente / investiții / acțiuni
    plasamente_total_ron: float = 0.0

    # V. Datorii
    datorii_total_ron: float = 0.0

    # VI. Cadouri
    cadouri_total_ron: float = 0.0

    # VII. Venituri
    venituri_anuale_ron: float = Field(
        default=0.0, description="Suma veniturilor anuale (titular + familie)"
    )

    # Detail lists
    imobile_detaliate: list[AvereImobil] = Field(default_factory=list)
    vehicule: list[VehiculDetail] = Field(default_factory=list)
    conturi_detaliate: list[ContDetail] = Field(default_factory=list)
    plasamente_detaliate: list[PlasamentDetail] = Field(default_factory=list)


class AvereDeputat(BaseModel):
    """Un deputat cu toate declarațiile lui cronologic."""

    id: str = Field(description="sha256('{leg}|{cdep_idm}|avere')[:16]")
    cdep_idm: int
    deputat_nume: str
    deputat_canonical_id: str | None = None
    legislatura: int
    partid_short: str | None = None

    declaratii: list[AvereDeclaratie] = Field(
        default_factory=list, description="Sortate cronologic"
    )

    # Snapshot final (ultima declarație)
    ultima_data: date | None = None
    ultima_conturi_ron: float = 0.0
    ultima_venituri_ron: float = 0.0
    ultima_imobile_count: int = 0
    ultima_bijuterii_ron: float = 0.0
    ultima_plasamente_ron: float = 0.0

    # Delta prima → ultima
    delta_conturi_ron: float = 0.0
    delta_imobile: int = 0


class AvereSummary(BaseModel):
    """Sumar pentru index — fără declarațiile complete."""

    id: str
    cdep_idm: int
    deputat_nume: str
    legislatura: int
    partid_short: str | None = None
    n_declaratii: int = 0
    ultima_data: date | None = None
    ultima_conturi_ron: float = 0.0
    ultima_venituri_ron: float = 0.0
    ultima_imobile_count: int = 0
    ultima_bijuterii_ron: float = 0.0
    ultima_plasamente_ron: float = 0.0
    bunuri_instrainate_total_ron: float = 0.0
    delta_conturi_ron: float = 0.0
    delta_imobile: int = 0
    detail_url: str
```

- [ ] **Step 2: Verify schema imports still work**

```bash
PYTHONPATH=. python3 -c "from schemas.avere import AvereDeclaratie, AvereDeputat, AvereSummary, VehiculDetail, ContDetail, PlasamentDetail, AvereImobil; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add schemas/avere.py
git commit -m "feat(avere-schema): add VehiculDetail/ContDetail/PlasamentDetail; 11 new fields"
```

---

## Task 2 — Extract parser to `parsers/avere_pdf.py`

**Files:**
- Create: `parsers/__init__.py`
- Create: `parsers/avere_pdf.py`

- [ ] **Step 1: Create `parsers/__init__.py`**

```python
```

(empty file)

- [ ] **Step 2: Create `parsers/avere_pdf.py` with all existing parsing logic**

Copy the regexes, helpers, and `parse_pdf()` from `scripts/build_declaratii_avere.py`. Also fix the latent bug where the full IV section (including IV.2 plasamente entries) was scanned by both RE_AMOUNT and RE_AMOUNT_REV, inflating `conturi_total_ron`.

```python
"""PDF parser pentru declarații de avere ANI.

Funcția principală: parse_pdf(pdf_path) -> dict
Returnează un dict cu toate câmpurile AvereDeclaratie (fără data_depunere/pdf_url).
"""

from __future__ import annotations

import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore[assignment]

RE_AMOUNT = re.compile(
    r"(\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
    r"\s*(RON|EUR|EURO|USD|GBP|CHF|lei|euro|dolari)\b",
    re.IGNORECASE,
)
RE_MP = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*²?", re.IGNORECASE)
# Some PDFs lay out tables as "CURRENCY YEAR BALANCE" (currency before amount).
RE_AMOUNT_REV = re.compile(
    r"\b(RON|EUR|EURO|USD|GBP|CHF|lei|euro|dolari)\b\s+\d{4}\s+(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)

RATES_TO_RON: dict[str, float] = {
    "RON": 1.0, "LEI": 1.0,
    "EUR": 5.05, "EURO": 5.05,
    "USD": 4.50, "DOLARI": 4.50,
    "GBP": 5.80, "CHF": 5.40,
}

MARKERS = [
    "I. Bunuri imobile",
    "II. Bunuri mobile",
    "III. Bunuri mobile",
    "IV. Active financiare",
    "V. Datorii",
    "VI. Cadouri",
    "VII. Venituri",
]

AUTO_RE = re.compile(
    r"^(autoturism|autovehicul|motociclet|tractor|remorc|iaht|şalup|salup|alt mijloc)\w*",
    re.IGNORECASE | re.MULTILINE,
)


def _parse_amount(num_str: str) -> float | None:
    s = num_str.replace(" ", "")
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


def normalize_to_ron(amount: float, currency: str) -> float:
    return amount * RATES_TO_RON.get(currency.upper(), 1.0)


def extract_section(text: str, marker: str, next_markers: list[str]) -> str:
    start = text.find(marker)
    if start < 0:
        return ""
    end = len(text)
    for nm in next_markers:
        idx = text.find(nm, start + len(marker))
        if 0 < idx < end:
            end = idx
    return text[start:end]


def _scan_amounts(text: str, threshold: float = 100.0) -> float:
    """Sum all amount+currency matches (both directions) in text."""
    total = 0.0
    for m in RE_AMOUNT.finditer(text):
        num = _parse_amount(m.group(1))
        if num and num > threshold:
            total += normalize_to_ron(num, m.group(2))
    for m in RE_AMOUNT_REV.finditer(text):
        num = _parse_amount(m.group(2))
        if num and num > threshold:
            total += normalize_to_ron(num, m.group(1))
    return total


def _detect_imobil_categorie(block: str, tip: str) -> str:
    """Detect category from a property block string."""
    b = block.lower()
    if "luciu de ap" in b:
        return "luciu_apa"
    if "extravilan" in b:
        return "extravilan"
    if "forestier" in b:
        return "forestier"
    if "agricol" in b:
        return "agricol"
    if "intravilan" in b:
        return "intravilan"
    if tip == "cladire":
        if "comerciale" in b or "producti" in b:
            return "comercial"
        if "vacan" in b:
            return "vacanta"
        if "locuit" in b or ("cas" in b and "locuit" in b):
            return "locuinta"
        if "apartament" in b:
            return "apartament"
        if "bunuri imobile" in b:
            return "alte_cladiri"
    return "necunoscuta"


def _detect_mod_dobandire(block: str) -> str | None:
    b = block.lower()
    if "mostenire" in b or "moștenire" in b:
        return "mostenire"
    if "donati" in b or "donație" in b:
        return "donatie"
    if "vânzare" in b or "vanzare" in b:
        return "cumparare"
    if "altele" in b:
        return "altele"
    return None


def _parse_imobile_details(
    sec_terenuri: str, sec_cladiri: str
) -> tuple[list[dict], dict[str, float]]:
    """Parse per-row imobile details. Returns (rows_as_dicts, suprafata_by_category)."""
    from schemas.avere import AvereImobil

    CAT_TO_FIELD = {
        "agricol": "suprafata_agricol_mp",
        "forestier": "suprafata_forestier_mp",
        "intravilan": "suprafata_intravilan_mp",
        "luciu_apa": "suprafata_luciu_mp",
        "extravilan": "suprafata_alte_mp",
    }
    aggregates: dict[str, float] = {
        "suprafata_agricol_mp": 0.0,
        "suprafata_forestier_mp": 0.0,
        "suprafata_intravilan_mp": 0.0,
        "suprafata_luciu_mp": 0.0,
        "suprafata_alte_mp": 0.0,
        "suprafata_cladiri_mp": 0.0,
    }
    rows: list[dict] = []

    for tip, section in [("teren", sec_terenuri), ("cladire", sec_cladiri)]:
        if not section:
            continue
        # Split into blocks: each property entry starts with "Tara:"
        blocks = re.split(r"(?im)^Tara\s*:", section)
        for block in blocks[1:]:  # skip header
            m_mp = RE_MP.search(block)
            if not m_mp:
                continue
            suprafata = _parse_amount(m_mp.group(1))
            if not suprafata or suprafata <= 5:
                continue

            # Judet
            m_j = re.search(r"Judet\s*:\s*([^\n]+)", block, re.IGNORECASE)
            judet = m_j.group(1).strip().split()[0] if m_j else None

            # Year — look on the line containing m²
            line_s = block.rfind("\n", 0, m_mp.start()) + 1
            line_e = block.find("\n", m_mp.end())
            mp_line = block[line_s: len(block) if line_e < 0 else line_e]
            years = re.findall(r"\b(19\d{2}|20[0-3]\d)\b", mp_line)
            an = int(years[0]) if years else None

            # Cota-parte
            m_cota = re.search(r"\b(\d+/\d+)\b", mp_line)
            cota = m_cota.group(1) if m_cota else None

            categorie = _detect_imobil_categorie(block, tip)
            mod = _detect_mod_dobandire(block)

            rows.append(
                AvereImobil(
                    tip=tip,
                    categorie=categorie,
                    suprafata_mp=suprafata,
                    judet=judet,
                    an_dobandirii=an,
                    cota_parte=cota,
                    modul_dobandirii=mod,
                ).model_dump()
            )

            # Aggregate
            if tip == "cladire":
                aggregates["suprafata_cladiri_mp"] += suprafata
            else:
                field = CAT_TO_FIELD.get(categorie, "suprafata_alte_mp")
                aggregates[field] += suprafata

    return rows, aggregates


def _parse_vehicule(sec_mobile: str) -> list[dict]:
    """Parse per-row vehicle details from section II.1."""
    from schemas.avere import VehiculDetail

    rows: list[dict] = []
    lines = sec_mobile.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = AUTO_RE.match(line)
        if not m:
            i += 1
            continue
        natura = m.group(1).strip()
        # Try to find year on current line or next 3 lines
        search_text = "\n".join(lines[i: i + 4])
        years = re.findall(r"\b(19\d{2}|20[0-3]\d)\b", search_text)
        an = int(years[0]) if years else None
        # Marca: text on current line after natura, before first digit sequence
        rest = line[m.end():].strip()
        marca_m = re.match(r"([A-Za-zÀ-ž\s\-\.]+?)(?:\s+\d)", rest)
        marca = marca_m.group(1).strip() or None if marca_m else (rest.split()[0] if rest.split() else None)
        # Mod dobandire
        mod_text = search_text.lower()
        if "vânzare" in mod_text or "vanzare" in mod_text:
            mod = "cumparare"
        elif "mostenire" in mod_text or "moștenire" in mod_text:
            mod = "mostenire"
        elif "donati" in mod_text:
            mod = "donatie"
        else:
            mod = None
        rows.append(
            VehiculDetail(
                natura=natura, marca=marca, an_fabricatie=an, mod_dobandire=mod
            ).model_dump()
        )
        i += 1
    return rows


def _parse_conturi_detaliate(sec_conturi1: str) -> list[dict]:
    """Parse per-row account details from section IV.1 only (not IV.2)."""
    from schemas.avere import ContDetail

    rows: list[dict] = []
    # RE_AMOUNT_REV: groups are (currency, amount)
    for m in RE_AMOUNT_REV.finditer(sec_conturi1):
        num = _parse_amount(m.group(2))
        if not num or num <= 0:
            continue
        currency = m.group(1).upper()
        sold_ron = normalize_to_ron(num, currency)

        # Year from the match context (pattern: CURRENCY YYYY AMOUNT)
        year_m = re.search(
            r"\b(RON|EUR|EURO|USD|GBP|CHF|lei|euro|dolari)\b\s+(\d{4})\s+",
            sec_conturi1[max(0, m.start() - 5): m.end()],
            re.IGNORECASE,
        )
        an_deschis = int(year_m.group(2)) if year_m else None

        # Institution: last line ending with comma before this match
        context_before = sec_conturi1[max(0, m.start() - 300): m.start()]
        inst = None
        for line in reversed(context_before.splitlines()):
            line = line.strip()
            if line.endswith(",") and len(line) > 3 and not any(
                kw in line.lower() for kw in ["cont", "depozit", "fond", "echival", "inclusiv"]
            ):
                inst = line.rstrip(",").strip()
                break

        # Account type
        tip_context = sec_conturi1[max(0, m.start() - 200): m.start()].lower()
        if "fond" in tip_context or "pensii" in tip_context:
            tip = "fond_investitii"
        elif "depozit" in tip_context:
            tip = "depozit"
        else:
            tip = "cont_curent"

        rows.append(
            ContDetail(
                institutie=inst, tip=tip, valuta=currency,
                an_deschis=an_deschis, sold_ron=sold_ron,
            ).model_dump()
        )

    # Also catch forward-order amounts (amount RON) — rare in IV.1 but possible
    seen_positions: set[int] = {m.start() for m in RE_AMOUNT_REV.finditer(sec_conturi1)}
    for m in RE_AMOUNT.finditer(sec_conturi1):
        if m.start() in seen_positions:
            continue
        num = _parse_amount(m.group(1))
        if not num or num <= 100:
            continue
        currency = m.group(2).upper()
        rows.append(
            ContDetail(
                institutie=None, tip=None, valuta=currency,
                an_deschis=None,
                sold_ron=normalize_to_ron(num, currency),
            ).model_dump()
        )

    return rows


def _parse_plasamente(sec_plasamente: str) -> list[dict]:
    """Parse per-row investment/stake/loan details from section IV.2."""
    from schemas.avere import PlasamentDetail

    rows: list[dict] = []
    if not sec_plasamente or "- - -" in sec_plasamente:
        return rows

    for m in RE_AMOUNT.finditer(sec_plasamente):
        num = _parse_amount(m.group(1))
        if not num or num <= 100:
            continue
        currency = m.group(2).upper()
        valoare_ron = normalize_to_ron(num, currency)

        # The value line: emitent + nr_titluri + amount + currency all on one line
        line_s = sec_plasamente.rfind("\n", 0, m.start()) + 1
        line_e = sec_plasamente.find("\n", m.end())
        val_line = sec_plasamente[line_s: len(sec_plasamente) if line_e < 0 else line_e]

        # Remove the amount+currency suffix, rest is emitent + nr_titluri
        prefix = val_line[: val_line.rfind(m.group(0))].strip()
        # Nr titluri: "100 %" or "1/3" or similar at end of prefix
        nr_m = re.search(r"(\d+\s*%|\d+\s*/\s*\d+|\d+\s+parti?|\d+\s+titluri?|\d+\s+actiuni?)\s*$", prefix, re.IGNORECASE)
        nr_titluri = nr_m.group(1).strip() if nr_m else None
        emitent = prefix[: nr_m.start()].strip() if nr_m else prefix.strip()
        emitent = emitent or None

        # Tip from nearby context (lines before/after)
        context = sec_plasamente[max(0, m.start() - 200): m.end() + 50].lower()
        if "imprumut" in context or "împrumut" in context:
            tip = "imprumut"
        elif "acti" in context and "parti" not in context:
            tip = "actiuni"
        elif "parti social" in context or "parți social" in context:
            tip = "parti_sociale"
        elif "titluri" in context or "obligati" in context or "certificate" in context:
            tip = "titluri_stat"
        else:
            tip = None

        rows.append(
            PlasamentDetail(
                emitent=emitent, tip=tip, nr_titluri=nr_titluri, valoare_ron=valoare_ron,
            ).model_dump()
        )

    return rows


def parse_pdf(pdf_path: Path) -> dict:
    """Parse an ANI wealth declaration PDF. Returns a dict matching AvereDeclaratie fields."""
    result: dict = {
        "terenuri_count": 0,
        "cladiri_count": 0,
        "suprafata_total_mp": 0.0,
        "suprafata_agricol_mp": 0.0,
        "suprafata_forestier_mp": 0.0,
        "suprafata_intravilan_mp": 0.0,
        "suprafata_luciu_mp": 0.0,
        "suprafata_alte_mp": 0.0,
        "suprafata_cladiri_mp": 0.0,
        "conturi_total_ron": 0.0,
        "plasamente_total_ron": 0.0,
        "venituri_anuale_ron": 0.0,
        "datorii_total_ron": 0.0,
        "bijuterii_total_ron": 0.0,
        "bunuri_instrainate_count": 0,
        "bunuri_instrainate_total_ron": 0.0,
        "cadouri_total_ron": 0.0,
        "auto_count": 0,
        "imobile_detaliate": [],
        "vehicule": [],
        "conturi_detaliate": [],
        "plasamente_detaliate": [],
        "text_extracted": False,
        "error": None,
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

    # ── I. Bunuri imobile ─────────────────────────────────────────────────────
    sec_imobile = extract_section(full_text, "I. Bunuri imobile", MARKERS)
    sec_terenuri = extract_section(sec_imobile, "1. Terenuri", ["2. Clădiri", "II. Bunuri mobile"])
    sec_cladiri = extract_section(sec_imobile, "2. Clădiri", ["II. Bunuri mobile"])

    teren_matches = list(RE_MP.finditer(sec_terenuri))
    cladire_matches = list(RE_MP.finditer(sec_cladiri))
    result["terenuri_count"] = len(teren_matches)
    result["cladiri_count"] = len(cladire_matches)
    for m in teren_matches + cladire_matches:
        mp = _parse_amount(m.group(1))
        if mp and mp > 5:
            result["suprafata_total_mp"] += mp

    imobile_rows, suprafata_cats = _parse_imobile_details(sec_terenuri, sec_cladiri)
    result["imobile_detaliate"] = imobile_rows
    result.update(suprafata_cats)

    # ── II. Bunuri mobile ─────────────────────────────────────────────────────
    sec_mobile = extract_section(full_text, "II. Bunuri mobile", MARKERS)

    result["auto_count"] = len(AUTO_RE.findall(sec_mobile))
    result["vehicule"] = _parse_vehicule(sec_mobile)

    # II.2 Bijuterii / metale prețioase / artă
    sec_bij = extract_section(sec_mobile, "2. Bunuri sub", ["III. Bunuri", "IV. Active"])
    result["bijuterii_total_ron"] = _scan_amounts(sec_bij)

    # ── III. Bunuri înstrăinate ───────────────────────────────────────────────
    sec_instr = extract_section(full_text, "III. Bunuri mobile", MARKERS)
    if sec_instr and "- - -" not in sec_instr:
        dates = re.findall(r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", sec_instr)
        result["bunuri_instrainate_count"] = len(dates)
        result["bunuri_instrainate_total_ron"] = _scan_amounts(sec_instr)

    # ── IV. Active financiare — split IV.1 conturi from IV.2 plasamente ───────
    sec_iv = extract_section(full_text, "IV. Active financiare", MARKERS)
    sec_conturi1 = extract_section(sec_iv, "1. Conturi", ["2. Plasamente", "3. Alte active"])
    sec_plasamente = extract_section(sec_iv, "2. Plasamente", ["3. Alte active", "V. Datorii"])

    conturi_rows = _parse_conturi_detaliate(sec_conturi1)
    result["conturi_detaliate"] = conturi_rows
    result["conturi_total_ron"] = sum(c["sold_ron"] for c in conturi_rows)

    plasamente_rows = _parse_plasamente(sec_plasamente)
    result["plasamente_detaliate"] = plasamente_rows
    result["plasamente_total_ron"] = sum(p["valoare_ron"] for p in plasamente_rows)

    # ── V. Datorii ────────────────────────────────────────────────────────────
    sec_datorii = extract_section(full_text, "V. Datorii", MARKERS)
    result["datorii_total_ron"] = _scan_amounts(sec_datorii)

    # ── VI. Cadouri ───────────────────────────────────────────────────────────
    sec_cadouri = extract_section(full_text, "VI. Cadouri", MARKERS)
    result["cadouri_total_ron"] = _scan_amounts(sec_cadouri)

    # ── VII. Venituri ─────────────────────────────────────────────────────────
    sec_venituri = extract_section(full_text, "VII. Venituri", MARKERS)
    if not sec_venituri:
        sec_venituri = extract_section(full_text, "Venituri ale declarantului", MARKERS)
    for m in RE_AMOUNT.finditer(sec_venituri):
        num = _parse_amount(m.group(1))
        if num and num > 100:
            result["venituri_anuale_ron"] += normalize_to_ron(num, m.group(2))

    return result
```

- [ ] **Step 3: Verify module imports cleanly**

```bash
PYTHONPATH=. python3 -c "from parsers.avere_pdf import parse_pdf; print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add parsers/__init__.py parsers/avere_pdf.py
git commit -m "feat(avere-parser): extract parser to parsers/avere_pdf.py with full section coverage"
```

---

## Task 3 — Unit tests for new parsing functions

**Files:**
- Create: `tests/test_avere_pdf_parser.py`
- Test: `tests/test_avere_pdf_parser.py`

- [ ] **Step 1: Write failing tests**

```python
"""Unit tests for parsers/avere_pdf.py — synthetic text, no PDF files required."""

from __future__ import annotations

import pytest

from parsers.avere_pdf import (
    _parse_imobile_details,
    _parse_vehicule,
    _parse_conturi_detaliate,
    _parse_plasamente,
    _scan_amounts,
    extract_section,
    MARKERS,
)

# ── Synthetic section text ────────────────────────────────────────────────────

SEC_TERENURI = """1. Terenuri
NOTĂ: Se vor declara inclusiv cele aflate în alte ţări.
Tara:
ROMANIA
Judet: Gorj
Localitate:
Forestier 2017 284354 m2 1/2 Contract de vânzare cumpărare Iordache Ion
Borascu -
Tara:
ROMANIA
Judet: Gorj
Localitate: Agricol 2015 2856 m2 1/2 Contract de vânzare Iordache Ion
Borascu -
Tara:
ROMANIA
Judet: Mehedinti
Alte categorii de terenuri extravilane 2018 135000 m2 1/2 Contract de vânzare Iordache Ion
"""

SEC_CLADIRI = """2. Clădiri
NOTĂ:
Tara:
ROMANIA
Judet: Gorj
Casă de locuit 2018 229 m2 1/2 Contract de vânzare cumpărare iordache
Turceni -
Tara:
ROMANIA
Judet: Gorj
comerciale/de producţie 2020 273 m2 1/2 Contract de vânzare iorache
Turceni -
"""

SEC_AUTO = """II. Bunuri mobile
1. Autovehicule/autoturisme, tractoare, maşini agricole, şalupe, iahturi...
Modul de
Natura Marca Nr. de bucăţi Anul de fabricaţie
dobândire
Contract de
Autoturism jeep wrangler 1 2004
vânzare cumpărare
Contract de
Tractor U650 1 1988
vânzare cumpărare
Contract de
şalupă Skyjet 1 2016
vânzare cumpărare
Alt mijloc de Contract de
500Ai 1 1994
transport vânzare cumpărare
"""

SEC_CONTURI1 = """1. Conturi şi depozite bancare...
Cont curent sau
CEC Bank,
echivalente RON 2015 377500
Depozit bancar sau
CEC TG JIU, echivalente RON 2022 787012
Fonduri de investiţii
NN ASIGURARI, RON 2014 49355
"""

SEC_PLASAMENTE_EMPTY = """2. Plasamente, investiţii directe...
- - - -
"""

SEC_PLASAMENTE_BECALI = """2. Plasamente, investiţii directe...
Împrumuturi acordate în
ARCOM SA 100 % 45825140 RON
nume personal
Împrumuturi acordate în
Fotbal Club FCSB SA 100 % 800000 EUR
nume personal
"""

SEC_BIJUTERII = """2. Bunuri sub formă de metale preţioase, bijuterii...
Bijuterii 2015 - 2020 140000 RON
Ceasuri 2013 - 2020 42000 EUR
"""

SEC_INSTRAINATE = """III. Bunuri mobile, a căror valoare depăşeşte 3.000 de euro...
Alte categorii de terenuri 20.07.2022 Donatie 0 RON extravilane
Apartament 21.04.2023 Contract Vanzare Cumparare 63000 RON
"""

SEC_CADOURI_EMPTY = """VI. Cadouri...
1.1. Titular
- - - -
1.2. Soţ/soţie
- - - -
"""


# ── _parse_imobile_details ────────────────────────────────────────────────────

def test_imobile_count():
    rows, _ = _parse_imobile_details(SEC_TERENURI, SEC_CLADIRI)
    assert len(rows) == 5  # 3 terenuri + 2 cladiri


def test_imobile_tip():
    rows, _ = _parse_imobile_details(SEC_TERENURI, SEC_CLADIRI)
    terenuri = [r for r in rows if r["tip"] == "teren"]
    cladiri = [r for r in rows if r["tip"] == "cladire"]
    assert len(terenuri) == 3
    assert len(cladiri) == 2


def test_imobile_categorie_teren():
    rows, _ = _parse_imobile_details(SEC_TERENURI, "")
    cats = {r["categorie"] for r in rows}
    assert "forestier" in cats
    assert "agricol" in cats
    assert "extravilan" in cats


def test_imobile_categorie_cladire():
    rows, _ = _parse_imobile_details("", SEC_CLADIRI)
    cats = {r["categorie"] for r in rows}
    assert "locuinta" in cats
    assert "comercial" in cats


def test_imobile_suprafata():
    rows, _ = _parse_imobile_details(SEC_TERENURI, "")
    suprafete = {r["suprafata_mp"] for r in rows}
    assert 284354.0 in suprafete
    assert 2856.0 in suprafete
    assert 135000.0 in suprafete


def test_imobile_judet():
    rows, _ = _parse_imobile_details(SEC_TERENURI, "")
    judete = {r["judet"] for r in rows}
    assert "Gorj" in judete
    assert "Mehedinti" in judete


def test_imobile_aggregates_sum():
    rows, agg = _parse_imobile_details(SEC_TERENURI, SEC_CLADIRI)
    total_from_agg = sum(agg.values())
    total_from_rows = sum(r["suprafata_mp"] for r in rows if r["suprafata_mp"])
    assert abs(total_from_agg - total_from_rows) < 1.0


def test_imobile_suprafata_forestier():
    _, agg = _parse_imobile_details(SEC_TERENURI, "")
    assert agg["suprafata_forestier_mp"] == pytest.approx(284354.0)


def test_imobile_suprafata_cladiri():
    _, agg = _parse_imobile_details("", SEC_CLADIRI)
    assert agg["suprafata_cladiri_mp"] == pytest.approx(229.0 + 273.0)


def test_imobile_empty_sections():
    rows, agg = _parse_imobile_details("", "")
    assert rows == []
    assert all(v == 0.0 for v in agg.values())


# ── _parse_vehicule ───────────────────────────────────────────────────────────

def test_vehicule_count():
    rows = _parse_vehicule(SEC_AUTO)
    assert len(rows) == 4


def test_vehicule_natura():
    rows = _parse_vehicule(SEC_AUTO)
    naturi = {r["natura"].lower() for r in rows}
    assert "autoturism" in naturi
    assert "tractor" in naturi


def test_vehicule_an_fabricatie():
    rows = _parse_vehicule(SEC_AUTO)
    ani = {r["an_fabricatie"] for r in rows}
    assert 2004 in ani
    assert 1988 in ani
    assert 2016 in ani


def test_vehicule_empty():
    assert _parse_vehicule("II. Bunuri mobile\n") == []


# ── _parse_conturi_detaliate ──────────────────────────────────────────────────

def test_conturi_count():
    rows = _parse_conturi_detaliate(SEC_CONTURI1)
    assert len(rows) == 3


def test_conturi_sold_ron():
    rows = _parse_conturi_detaliate(SEC_CONTURI1)
    solds = {r["sold_ron"] for r in rows}
    assert 377500.0 in solds
    assert 787012.0 in solds


def test_conturi_tip_detection():
    rows = _parse_conturi_detaliate(SEC_CONTURI1)
    tips = {r["tip"] for r in rows}
    assert "depozit" in tips
    assert "fond_investitii" in tips


def test_conturi_empty():
    assert _parse_conturi_detaliate("") == []


# ── _parse_plasamente ─────────────────────────────────────────────────────────

def test_plasamente_empty():
    rows = _parse_plasamente(SEC_PLASAMENTE_EMPTY)
    assert rows == []


def test_plasamente_count():
    rows = _parse_plasamente(SEC_PLASAMENTE_BECALI)
    assert len(rows) == 2


def test_plasamente_emitent():
    rows = _parse_plasamente(SEC_PLASAMENTE_BECALI)
    emitenti = [r["emitent"] for r in rows]
    assert any(e and "ARCOM" in e for e in emitenti)
    assert any(e and "FCSB" in e for e in emitenti)


def test_plasamente_valoare_ron():
    rows = _parse_plasamente(SEC_PLASAMENTE_BECALI)
    ron_values = {r["valoare_ron"] for r in rows}
    assert 45825140.0 in ron_values
    # 800000 EUR × 5.05
    assert pytest.approx(800000 * 5.05) in ron_values


# ── _scan_amounts (bijuterii / cadouri) ───────────────────────────────────────

def test_scan_bijuterii():
    total = _scan_amounts(SEC_BIJUTERII)
    # 140000 RON + 42000 EUR × 5.05
    assert total == pytest.approx(140000.0 + 42000 * 5.05, rel=0.01)


def test_scan_cadouri_empty():
    assert _scan_amounts(SEC_CADOURI_EMPTY) == pytest.approx(0.0)


def test_scan_instrainate_excludes_zero():
    # 0 RON excluded by > 100 threshold; 63000 RON included
    total = _scan_amounts(SEC_INSTRAINATE)
    assert total == pytest.approx(63000.0)


# ── bunuri_instrainate_count ──────────────────────────────────────────────────

def test_instrainate_count():
    import re
    dates = re.findall(r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", SEC_INSTRAINATE)
    assert len(dates) == 2
```

- [ ] **Step 2: Run tests — expect failures**

```bash
PYTHONPATH=. pytest tests/test_avere_pdf_parser.py -v 2>&1 | head -50
```

Expected: multiple FAILs (functions not yet accessible from parsers.avere_pdf)

- [ ] **Step 3: Run tests after Task 2 is complete — expect all pass**

```bash
PYTHONPATH=. pytest tests/test_avere_pdf_parser.py -v
```

Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add tests/test_avere_pdf_parser.py
git commit -m "test(avere-parser): unit tests for all new parsing functions"
```

---

## Task 4 — Wire `parsers/avere_pdf.py` into `build_declaratii_avere.py`

**Files:**
- Modify: `scripts/build_declaratii_avere.py`

- [ ] **Step 1: Replace the parser body in `build_declaratii_avere.py`**

Remove everything from `RE_AMOUNT = ...` down through the end of `parse_pdf()` (lines ~51–223). Replace with imports and updated `process_deputat`.

The top of the file (imports + constants for the build pipeline) stays. Replace the parser block with:

```python
from parsers.avere_pdf import parse_pdf  # noqa: E402
```

Then update `process_deputat` to include the new snapshot fields. Find the `return AvereDeputat(...)` call and update:

```python
    return AvereDeputat(
        id=_avere_id(leg, d["cdep_idm"]),
        cdep_idm=d["cdep_idm"],
        deputat_nume=d["deputat_nume"],
        deputat_canonical_id=d.get("deputat_canonical_id")
        or _voter_canonical_id(d["deputat_nume"]),
        legislatura=leg,
        partid_short=d.get("partid_short"),
        declaratii=declaratii,
        ultima_data=ultima.data_depunere if ultima else None,
        ultima_conturi_ron=ultima.conturi_total_ron if ultima else 0.0,
        ultima_venituri_ron=ultima.venituri_anuale_ron if ultima else 0.0,
        ultima_imobile_count=(ultima.terenuri_count + ultima.cladiri_count) if ultima else 0,
        ultima_bijuterii_ron=ultima.bijuterii_total_ron if ultima else 0.0,
        ultima_plasamente_ron=ultima.plasamente_total_ron if ultima else 0.0,
        delta_conturi_ron=(ultima.conturi_total_ron - prima.conturi_total_ron)
        if ultima and prima
        else 0.0,
        delta_imobile=(
            (ultima.terenuri_count + ultima.cladiri_count)
            - (prima.terenuri_count + prima.cladiri_count)
        )
        if ultima and prima
        else 0,
    )
```

Also update the `AvereSummary` creation in `run_leg()`:

```python
        summaries.append(
            AvereSummary(
                id=av.id,
                cdep_idm=av.cdep_idm,
                deputat_nume=av.deputat_nume,
                legislatura=av.legislatura,
                partid_short=av.partid_short,
                n_declaratii=len(av.declaratii),
                ultima_data=av.ultima_data,
                ultima_conturi_ron=av.ultima_conturi_ron,
                ultima_venituri_ron=av.ultima_venituri_ron,
                ultima_imobile_count=av.ultima_imobile_count,
                ultima_bijuterii_ron=av.ultima_bijuterii_ron,
                ultima_plasamente_ron=av.ultima_plasamente_ron,
                bunuri_instrainate_total_ron=av.declaratii[-1].bunuri_instrainate_total_ron
                if av.declaratii
                else 0.0,
                delta_conturi_ron=av.delta_conturi_ron,
                delta_imobile=av.delta_imobile,
                detail_url=f"declaratii-avere/legislatura-{leg}/{av.cdep_idm}.json",
            ).model_dump(mode="json", exclude_none=False)
        )
```

- [ ] **Step 2: Verify build script imports cleanly**

```bash
PYTHONPATH=. python3 -c "from scripts.build_declaratii_avere import process_deputat; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Run full test suite**

```bash
PYTHONPATH=. pytest -v
```

Expected: all tests PASS (including pre-existing tests)

- [ ] **Step 4: Smoke test on cached PDF (Iordache Ion)**

```python
PYTHONPATH=. python3 -c "
from parsers.avere_pdf import parse_pdf
from pathlib import Path
r = parse_pdf(Path('data/analize/_pdfs/00dd571ad7d8.pdf'))
print('terenuri:', r['terenuri_count'])
print('imobile rows:', len(r['imobile_detaliate']))
print('vehicule:', len(r['vehicule']))
print('conturi rows:', len(r['conturi_detaliate']))
print('conturi_total_ron:', r['conturi_total_ron'])
print('plasamente_total_ron:', r['plasamente_total_ron'])
print('bijuterii:', r['bijuterii_total_ron'])
print('instrainate count:', r['bunuri_instrainate_count'])
print('instrainate total:', r['bunuri_instrainate_total_ron'])
print('cadouri:', r['cadouri_total_ron'])
print('suprafata_forestier:', r['suprafata_forestier_mp'])
print('suprafata_cladiri:', r['suprafata_cladiri_mp'])
"
```

Expected (Iordache Ion 153.pdf):
```
terenuri: 73
imobile rows: 83
vehicule: 10
conturi rows: ~11
conturi_total_ron: ~3091541
plasamente_total_ron: 0.0
bijuterii: ~352100  (140000 + 42000×5.05)
instrainate count: 2
instrainate total: 63000.0
cadouri: 0.0
suprafata_forestier: >0
suprafata_cladiri: >0
```

- [ ] **Step 5: Commit**

```bash
git add scripts/build_declaratii_avere.py
git commit -m "feat(avere-build): wire parsers/avere_pdf into build script; add bijuterii/plasamente snapshots"
```

---

## Task 5 — Update `analiza_avere_pdf.py`

**Files:**
- Modify: `scripts/analiza_avere_pdf.py`

- [ ] **Step 1: Replace the local `parse_pdf` function with an import**

Find the `parse_pdf` function definition in `analiza_avere_pdf.py` (starts around line 140). Delete it and its helpers (`_parse_amount`, `normalize_to_ron`, `extract_section`, and the regex/constant block it defines). Replace with:

```python
from parsers.avere_pdf import parse_pdf, RATES_TO_RON  # noqa: E402
```

- [ ] **Step 2: Update the CSV columns and print summary to include new fields**

Find the CSV header line (contains `"terenuri_count,cladiri_count"`) and extend it:

```python
"partid,cdep_idm,nume,data_declaratie,terenuri_count,cladiri_count,"
"suprafata_total_mp,conturi_total_ron,plasamente_total_ron,venituri_anuale_ron,"
"bijuterii_total_ron,bunuri_instrainate_total_ron,cadouri_total_ron,"
"datorii_total_ron,auto_count,text_extracted,error\n"
```

And the corresponding CSV row format. Add:
```python
f"{r.get('plasamente_total_ron', 0):.0f},{r.get('bijuterii_total_ron', 0):.0f},"
f"{r.get('bunuri_instrainate_total_ron', 0):.0f},{r.get('cadouri_total_ron', 0):.0f},"
```

- [ ] **Step 3: Verify script runs without errors**

```bash
PYTHONPATH=. python3 scripts/analiza_avere_pdf.py --limit 2 2>&1 | tail -20
```

Expected: completes without ImportError or AttributeError; shows summary table for 2 deputies.

- [ ] **Step 4: Run full test suite**

```bash
PYTHONPATH=. pytest -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/analiza_avere_pdf.py
git commit -m "feat(analiza-avere): import parse_pdf from shared parsers module; add new fields to CSV"
```

---

## Task 6 — Backlog + activity log + final commit

**Files:**
- Modify: `docs/backlog.md`
- Modify: `docs/activity-log.md`

- [ ] **Step 1: Remove the resolved "are all fields accounted for?" entry from backlog**

In `docs/backlog.md`, delete the entry under `## Misc`:
```
- [ ] Generally, are all possible fields accounted for? see https://...
```

- [ ] **Step 2: Add activity log entry**

Add at the top of `## Data Quality` in `docs/activity-log.md`:

```markdown
### 2026-05-29 — Full PDF extraction pipeline: all ANI form sections + per-row detail lists

**What was done**
- Extracted parser logic to `parsers/avere_pdf.py` (shared module; eliminates duplication with `analiza_avere_pdf.py`).
- Added 4 new detail-list parsers: `_parse_imobile_details`, `_parse_vehicule`, `_parse_conturi_detaliate`, `_parse_plasamente`.
- Added 3 new scalar sections: II.2 bijuterii, III bunuri înstrăinate, VI cadouri.
- Fixed latent bug: IV section was scanned as a whole, inflating `conturi_total_ron` with IV.2 plasamente values. Now IV.1 and IV.2 are extracted separately.
- `schemas/avere.py`: 3 new models (VehiculDetail, ContDetail, PlasamentDetail); `AvereDeclaratie` +11 fields; `AvereDeputat` +2 snapshot fields; `AvereSummary` +3 fields.
- Added `imobile_detaliate` population (was schema-defined but always empty).
- Category aggregates for imobile: `suprafata_agricol_mp`, `suprafata_forestier_mp`, `suprafata_intravilan_mp`, `suprafata_luciu_mp`, `suprafata_alte_mp`, `suprafata_cladiri_mp`.
- 26 unit tests covering all new functions with synthetic text.

**Action needed:** Re-run `build_declaratii_avere.py --leg 2024 --all` to regenerate JSON from cached PDFs.
```

- [ ] **Step 3: Commit**

```bash
git add docs/backlog.md docs/activity-log.md
git commit -m "docs: backlog cleanup + activity log for full avere extraction pipeline"
```

---

## Self-Review

**Spec coverage check:**
- ✅ `VehiculDetail`, `ContDetail`, `PlasamentDetail` models — Task 1
- ✅ `AvereImobil` updated with `tip`, `judet` — Task 1
- ✅ 11 new `AvereDeclaratie` fields — Task 1
- ✅ `AvereDeputat` `ultima_bijuterii_ron`, `ultima_plasamente_ron` — Task 1 + Task 4
- ✅ `AvereSummary` 3 new fields — Task 1 + Task 4
- ✅ `parsers/avere_pdf.py` created — Task 2
- ✅ `_parse_imobile_details` — Task 2; tested Task 3
- ✅ `_parse_vehicule` — Task 2; tested Task 3
- ✅ `_parse_conturi_detaliate` — Task 2; tested Task 3
- ✅ `_parse_plasamente` — Task 2; tested Task 3
- ✅ bijuterii scalar — Task 2 (`_scan_amounts` on II.2); tested Task 3
- ✅ bunuri înstrăinate count + total — Task 2; tested Task 3
- ✅ cadouri scalar — Task 2; tested Task 3
- ✅ IV.1/IV.2 split (bug fix) — Task 2
- ✅ `imobile_detaliate` populated — Task 2
- ✅ `build_declaratii_avere.py` wired — Task 4
- ✅ `analiza_avere_pdf.py` synced — Task 5

**Placeholder scan:** None found.

**Type consistency:** All field names in Task 1 schema match dict keys emitted by `parse_pdf()` in Task 2. `AvereDeclaratie(**parsed)` will map correctly via pydantic.
