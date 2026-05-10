"""Scraper pentru moțiuni (simple + de cenzură).

Strategia:
1. Fetch lista: `motiuni2015.lista?cam=2` → toate idm-urile.
2. Pentru fiecare idm, fetch detalii: `parlament.motiuni2015.detalii?leg=YYYY&cam=2&idm=N`.

Sursa: cdep.ro/pls/parlam/motiuni2015.{lista,detalii}
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from urllib.parse import urljoin

from parsel import Selector

from schemas.motiune import Motiune, RezultatMotiune, SemnatarMotiune, TipMotiune
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
# leg= acceptat pentru a interoga si legislaturi anterioare (1990-prezent)
LIST_URL = BASE + "/ords/pls/parlam/motiuni2015.lista?leg={leg}&cam={cam}"
DETAIL_URL = BASE + "/ords/pls/parlam/parlament.motiuni2015.detalii?leg={leg}&cam={cam}&idm={idm}"

MAX_WORKERS = int(os.environ.get("CDEP_SCRAPE_WORKERS", "2"))


def _motiune_id(cam: int, idm: int) -> str:
    return hashlib.sha256(f"{cam}|{idm}".encode()).hexdigest()[:16]


def _voter_canonical_id(name: str) -> str:
    """Reproduce canonical_id din scrapers/deputati.py."""
    norm = unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii").lower()
    norm = " ".join(norm.split())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _parse_iso_date(s: str | None) -> date | None:
    """DD-MM-YYYY sau DD.MM.YYYY → date."""
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


def list_idms(leg: int, cam: int = 2) -> list[int]:
    """Returnează idm-urile pentru moțiuni la o legislatură + cameră.

    cdep.ro acceptă param ``leg`` și returnează idm-urile pentru legislatura
    indicată (sau curentă dacă ``leg`` e omis). Suport: 1990-prezent.
    """
    url = LIST_URL.format(leg=leg, cam=cam)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"list leg={leg} cam={cam}: {e}")
        return []

    sel = Selector(text=r.text)
    idms: list[int] = []
    for href in sel.css("a::attr(href)").getall():
        m = re.search(r"motiuni2015\.detalii\?[^=]*=\d+(?:&[^=]*=\d+)*&idm=(\d+)", href)
        if m:
            idm = int(m.group(1))
            if idm not in idms:
                idms.append(idm)
    return idms


def _detect_tip(text: str) -> TipMotiune:
    t = text.lower()
    if "cenzur" in t:
        return TipMotiune.CENZURA
    if "simpl" in t:
        return TipMotiune.SIMPLA
    return TipMotiune.OTHER


def _detect_rezultat(text: str | None) -> RezultatMotiune:
    if not text:
        return RezultatMotiune.IN_PROCEDURA
    t = text.lower()
    if "respins" in t:
        return RezultatMotiune.RESPINSA
    if "adoptat" in t:
        return RezultatMotiune.ADOPTATA
    if "retras" in t:
        return RezultatMotiune.RETRASA
    return RezultatMotiune.OTHER


def parse_detail(idm: int, legislatura: int, cam: int = 2) -> Motiune | None:
    """Fetch & parse o moțiune individuală."""
    url = DETAIL_URL.format(leg=legislatura, cam=cam, idm=idm)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  idm={idm}: {e}")
        return None

    sel = Selector(text=r.text)
    text = " ".join(sel.css("body *::text").getall())
    text = re.sub(r"\s+", " ", text).strip()

    # Helper pentru extracție label:value (pattern: label urmat de valoare până la următorul label)
    def field(label: str, max_len: int = 200) -> str | None:
        # Acceptă cu/fără diacritice prin replace
        pattern = (
            re.escape(label)
            + r"\s*:?\s*(.{1,"
            + str(max_len)
            + r"}?)(?=\s+(?:Tip|Inițiator|Iniţiator|Nr\.|Data|Voturi|Vot|Abțineri|Abţineri|Rezultat|Semnătur|Semnatar|Texte|Stenogr|$))"
        )
        m = re.search(pattern, text)
        return m.group(1).strip() if m else None

    # Titlu: e în heading, nu sub un label "Titlu"
    # Caut prin h1/h2/h3 pentru cel mai lung text — acesta e titlul moțiunii
    titlu = "(fără titlu)"
    candidates = []
    for tag in ("h1", "h2", "h3"):
        for h in sel.css(f"{tag}::text, {tag} *::text").getall():
            t = h.strip()
            if t and len(t) > 30 and t.lower() not in ("camera deputatilor", "camera deputaților"):
                candidates.append(t)
    # Sau din meta og:title / og:description
    og_desc = sel.xpath('//meta[@property="og:description"]/@content').get()
    if og_desc and len(og_desc.strip()) > 30:
        candidates.insert(0, og_desc.strip())
    # Aleg cel mai lung candidat (titlu lung = e cel real, nu un sub-titlu de tip "Moțiune simplă")
    if candidates:
        titlu = max(candidates, key=len)

    tip_text = field("Tip", 50) or "simpla"
    initiatori = field("Inițiatori", 200) or field("Iniţiatori", 200)
    nr_inreg_raw = field("Nr./Data înregistrării", 100) or field("Nr./Data inregistrarii", 100)

    nr_inreg = None
    data_inreg = None
    if nr_inreg_raw:
        m_nr = re.match(r"(\d+)\s*/\s*(\d{1,2}-\d{1,2}-\d{4})", nr_inreg_raw)
        if m_nr:
            nr_inreg = m_nr.group(1)
            data_inreg = _parse_iso_date(m_nr.group(2))
        else:
            nr_inreg = nr_inreg_raw

    data_vot_raw = field("Data votului", 50) or field("Data vot", 50)
    data_vot = _parse_iso_date(data_vot_raw) if data_vot_raw else None

    # Voturi: pentru / contra / abțineri
    def parse_int(text: str | None) -> int | None:
        if not text:
            return None
        m_int = re.match(r"(\d+)", text.strip())
        return int(m_int.group(1)) if m_int else None

    vot_pentru = parse_int(
        field("Voturi pentru moțiunii", 20)
        or field("Voturi pentru moţiunii", 20)
        or field("Voturi pentru", 20)
    )
    vot_contra = parse_int(
        field("Voturi împotriva moțiunii", 20)
        or field("Voturi impotriva motiunii", 20)
        or field("Voturi împotrivă", 20)
    )
    vot_abtineri = parse_int(field("Abțineri", 20) or field("Abţineri", 20))

    rezultat_text = field("Rezultat", 60) or ""
    rezultat = _detect_rezultat(rezultat_text)

    nr_semnatari_raw = field("Semnături", 30) or field("Semnatari", 30)
    nr_semnatari = parse_int(nr_semnatari_raw) if nr_semnatari_raw else None

    # Semnatari nominal — caut link-uri către structura2015.mp în pagină
    semnatari: list[SemnatarMotiune] = []
    seen_names: set[str] = set()
    for a in sel.css("a"):
        href = a.xpath("@href").get() or ""
        if "structura2015.mp" in href and "idm=" in href:
            nume = " ".join(a.css("*::text").getall()).strip()
            if nume and nume not in seen_names and len(nume) > 3:
                seen_names.add(nume)
                semnatari.append(
                    SemnatarMotiune(
                        nume=nume,
                        canonical_id=_voter_canonical_id(nume),
                        partid=None,  # partidul nu e ușor extras aici
                    )
                )

    # PDF
    pdf_url = None
    for href in sel.css('a[href$=".pdf"]::attr(href)').getall():
        pdf_url = urljoin(BASE, href)
        break

    return Motiune(
        id=_motiune_id(cam, idm),
        cdep_idm=idm,
        cam=cam,
        legislatura=legislatura,
        nr_inregistrare=nr_inreg,
        data_inregistrare=data_inreg,
        titlu=titlu[:500],
        tip=_detect_tip(tip_text),
        initiatori_descriere=initiatori,
        data_vot=data_vot,
        vot_pentru=vot_pentru,
        vot_contra=vot_contra,
        vot_abtineri=vot_abtineri,
        rezultat=rezultat,
        nr_semnatari=nr_semnatari,
        semnatari=semnatari,
        pdf_url=pdf_url,
        source_url=url,
    )


def scrape_all(legislatura: int, cam: int = 2) -> list[Motiune]:
    """Scrape toate moțiunile pentru o legislatură + cameră."""
    idms = list_idms(leg=legislatura, cam=cam)
    logger.info(f"leg={legislatura} cam={cam}: {len(idms)} moțiuni de procesat")

    results: list[Motiune] = []
    if not idms:
        return results

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idm = {executor.submit(parse_detail, idm, legislatura, cam): idm for idm in idms}
        for done, future in enumerate(as_completed(future_to_idm), start=1):
            idm = future_to_idm[future]
            try:
                m = future.result()
                if m:
                    results.append(m)
                if done % 20 == 0:
                    logger.info(f"  [{done}/{len(idms)}] processed")
            except Exception as e:
                logger.warning(f"  idm={idm} failed: {e}")

    logger.info(f"cam={cam}: {len(results)} parsed successfully")
    return results
