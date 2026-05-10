"""Scraper pentru interpelări și întrebări parlamentare.

Strategia:
1. Pentru fiecare an, fetch `interpelari2015.lista?tip=&dat=YYYY` → listă cu link-uri detail.
2. Pentru fiecare detail (idi=N), fetch `interpelari2015.detalii?idi=N` → parsare info.

Sursa: cdep.ro/pls/parlam/interpelari2015.*
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from datetime import date
from urllib.parse import urljoin

from parsel import Selector

from schemas.interpelare import Interpelare
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
LIST_URL = BASE + "/ords/pls/parlam/interpelari2015.lista?tip=&dat={year}&idl=1"
DETAIL_URL = BASE + "/ords/pls/parlam/interpelari2015.detalii?idi={idi}&idl=1"


def _strip_diacritics(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _voter_canonical_id(name: str) -> str:
    norm = " ".join(_strip_diacritics(name).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _interpelare_id(legislatura: int, idi: int) -> str:
    return hashlib.sha256(f"{legislatura}|{idi}".encode()).hexdigest()[:16]


def _parse_iso_date(s: str) -> date | None:
    """Parsează data în format DD-MM-YYYY sau DD.MM.YYYY sau DD/MM/YYYY → date.

    Suport pentru schema ORDS (folosește puncte `.`) și HTML legacy (folosea liniuțe).
    """
    if not s:
        return None
    s = s.strip()
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", s)
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except (ValueError, TypeError):
        return None


def list_idis_for_year(year: int) -> list[int]:
    """Returnează lista de idi pentru un an."""
    url = LIST_URL.format(year=year)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"list year {year}: {e}")
        return []
    sel = Selector(text=r.text)
    idis = []
    for href in sel.css("a::attr(href)").getall():
        m = re.search(r"interpelari2015\.detalii\?idi=(\d+)", href)
        if m:
            idi = int(m.group(1))
            if idi not in idis:
                idis.append(idi)
    return idis


def parse_detail(idi: int, legislatura: int) -> Interpelare | None:
    """Fetch & parse o interpelare individuală.

    Schema HTML nouă (după migrarea ORDS 2026-05-10):
      - Header: ``<meta og:title content="Întrebarea nr. 4106A/18.02.2026">``
      - Titlu: ``<meta og:description>`` sau ``<h1>`` din ``.boxTitle``
      - Câmpurile sunt în <table> cu rânduri ``<tr><td>Label:</td><td><b>Value</b></td></tr>``
      - Răspuns: după marker ``Informaţii privind răspunsul``
      - Formatul datei: ``DD.MM.YYYY`` cu puncte (anterior era cu liniuțe)
    """
    url = DETAIL_URL.format(idi=idi)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  idi={idi}: {e}")
        return None

    sel = Selector(text=r.text)

    # --- Header: extras din og:title meta tag ---
    og_title = sel.css('meta[property="og:title"]::attr(content)').get() or ""
    m_header = re.search(
        r"(Întrebarea|Interpelarea)\s+nr\.\s*([\dA-Za-z]+)\s*/\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})",
        og_title,
    )
    if not m_header:
        logger.warning(f"  idi={idi}: header not found (og:title='{og_title[:60]}')")
        return None
    nr_inregistrare = m_header.group(2)
    data_header = _parse_iso_date(m_header.group(3))

    # --- Titlu: din og:description sau h1 din .boxTitle ---
    titlu = (sel.css('meta[property="og:description"]::attr(content)').get() or "").strip()
    if not titlu:
        titlu = (sel.css("div.boxTitle h1::text").get() or "").strip()
    titlu = re.sub(r"\s+", " ", titlu)[:500]

    # --- Câmpuri din tabel: label → value ---
    # Construim un dict {label_lower: text_val} parsând fiecare <tr>.
    # Folosim ``::text`` (CSS) care prinde și textul direct al elementului — mai robust
    # decât xpath("text()") care e ambiguu între direct vs. descendent în parsel.
    # Stocăm AMBELE apariții pentru fiecare label (main + raspuns) ca să le diferențiem ulterior.
    rows: list[tuple[str, str]] = []
    for tr in sel.css("tr"):
        cells = tr.css("td")
        if len(cells) != 2:
            continue
        label = "".join(cells[0].css("::text").getall()).strip()
        label = re.sub(r":\s*$", "", label).strip().lower()
        if not label:
            continue
        value = " ".join(p.strip() for p in cells[1].css("::text").getall() if p.strip())
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            rows.append((label, value))

    # Dict pentru lookup primul (din blocul principal, înaintea răspunsului)
    fields: dict[str, str] = {}
    for label, value in rows:
        if label not in fields:
            fields[label] = value

    def get_field(*labels: str) -> str | None:
        for lab in labels:
            v = fields.get(lab.lower())
            if v:
                return v
        return None

    data_inreg = _parse_iso_date(get_field("Data înregistrarii", "Data înregistrării") or "")
    data_prez = _parse_iso_date(get_field("Data prezentării") or "")
    data_com = _parse_iso_date(get_field("Data comunicării") or "")
    termen = _parse_iso_date(get_field("Termen primire răspuns") or "")
    mod_adresare = get_field("Mod adresare")
    raspuns_solicitat = get_field("Răspuns solicitat")

    # --- Adresant: extras din tag-uri HTML (e structurat semantic) ---
    # Pattern: <td>Adresant:</td><td><b><a href="...mp?idm=N...">NUME</a></b> - deputat <a href="...gp?idg=N">GRUP</a></td>
    adresant_nume = ""
    adresant_grup = None
    for tr in sel.css("tr"):
        cells = tr.css("td")
        if len(cells) != 2:
            continue
        label = re.sub(r":\s*$", "", "".join(cells[0].css("::text").getall()).strip()).lower()
        if label == "adresant":
            nume = cells[1].css("b a::text").get() or cells[1].css("b::text").get() or ""
            adresant_nume = nume.strip()
            for a in cells[1].css("a"):
                if "structura2015.gp" in (a.attrib.get("href") or ""):
                    adresant_grup = (a.css("::text").get() or "").strip() or None
                    break
            break
    if not adresant_nume:
        adresant_nume = get_field("Adresant") or "?"

    # --- Destinatar: institutia (in <b>) + persoana ---
    destinatar = get_field("Destinatar") or "?"

    # --- PDF-uri: primul = textul interpelării, al doilea (dacă există) = răspunsul ---
    # Dedupe păstrând ordinea (PDF-urile apar de 2 ori: icon + text link).
    seen_pdfs: set[str] = set()
    pdfs: list[str] = []
    for href in sel.css('a[href$=".pdf"]::attr(href)').getall():
        full = urljoin(BASE, href)
        if full not in seen_pdfs:
            seen_pdfs.add(full)
            pdfs.append(full)
    text_pdf = pdfs[0] if pdfs else None

    # --- Răspuns: secțiunea "Informaţii privind răspunsul" ---
    # Detectăm dacă răspunsul există căutând al doilea bloc cu acest titlu
    raspuns_primit = bool(
        sel.xpath("//*[contains(text(), 'Informaţii privind răspunsul') or contains(text(), 'Informatii privind raspunsul')]")
    )
    raspuns_data = None
    raspuns_sursa = None
    raspuns_comunicat = None
    raspuns_pdf = None
    raspuns_nr = None

    if raspuns_primit:
        # Răspuns are tabelul lui propriu DUPĂ marker. Luăm ULTIMA apariție pentru fiecare
        # label (răspunsul fiind a doua secțiune, ultimele rânduri = răspuns).
        last_fields: dict[str, str] = {}
        for label, value in rows:
            last_fields[label] = value  # overwrite — ultima câștigă
        # Răspunsul are propriul "Nr.înregistrare" diferit de cel principal
        cand_raspuns_nr = last_fields.get("nr.înregistrare")
        if cand_raspuns_nr and cand_raspuns_nr != nr_inregistrare:
            raspuns_nr = cand_raspuns_nr
        raspuns_data = _parse_iso_date(last_fields.get("data înregistrării") or "")
        raspuns_sursa_raw = last_fields.get("răspuns primit de la") or None
        if raspuns_sursa_raw:
            # Tăiem la "comunicat de:" — păstrăm doar institutia
            raspuns_sursa = re.split(r"\s+comunicat de:?\s*", raspuns_sursa_raw, maxsplit=1)[0].strip()
        else:
            raspuns_sursa = None
        # Pentru "comunicat de" extragem din întregul text (apare după "comunicat de:")
        body_text = " ".join(sel.css("body *::text").getall())
        body_text = re.sub(r"\s+", " ", body_text)
        m_com = re.search(
            r"comunicat de:\s*(?:domnul|doamna)?\s*([A-Za-zĂÂÎȘȚăâîșțşţ\-\.\s]+?)\s+-\s+"
            r"(?:Secretar de Stat|Subsecretar de Stat|Ministru|Secretar|Director|Pre[şs]edinte|"
            r"Vicepre[şs]edinte|Consilier|Şef)",
            body_text,
        )
        if m_com:
            raspuns_comunicat = m_com.group(1).strip()
        if len(pdfs) >= 2:
            raspuns_pdf = pdfs[1]

    # Fallback dacă data_inreg lipsea
    if not data_inreg:
        data_inreg = data_header

    return Interpelare(
        id=_interpelare_id(legislatura, idi),
        cdep_idi=idi,
        legislatura=legislatura,
        nr_inregistrare=nr_inregistrare,
        data_inregistrare=data_inreg,
        data_prezentare=data_prez,
        data_comunicare=data_com,
        termen_raspuns=termen,
        titlu=titlu[:500],  # truncate la 500 chars
        mod_adresare=mod_adresare,
        adresant_nume=adresant_nume,
        adresant_canonical_id=_voter_canonical_id(adresant_nume) if adresant_nume != "?" else None,
        adresant_grup=adresant_grup,
        destinatar=destinatar,
        text_pdf_url=text_pdf,
        raspuns_solicitat=raspuns_solicitat,
        raspuns_primit=raspuns_primit,
        raspuns_nr_inregistrare=raspuns_nr,
        raspuns_data=raspuns_data,
        raspuns_sursa=raspuns_sursa,
        raspuns_comunicat_de=raspuns_comunicat,
        raspuns_pdf_url=raspuns_pdf,
        source_url=url,
    )


def scrape_year(year: int, legislatura: int) -> list[Interpelare]:
    idis = list_idis_for_year(year)
    logger.info(f"year={year}: {len(idis)} interpelări/întrebări")
    results = []
    for i, idi in enumerate(idis, 1):
        try:
            interp = parse_detail(idi, legislatura)
            if interp:
                results.append(interp)
                if i % 100 == 0:
                    logger.info(f"  [{i}/{len(idis)}] processed")
        except Exception as e:
            logger.warning(f"  idi={idi} failed: {e}")
    logger.info(f"year={year}: {len(results)} parsed successfully")
    return results
