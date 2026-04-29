"""Scraper pentru proiecte legislative.

Strategia:
1. Pentru fiecare an, fetch `upl_pck2015.lista?anp=YYYY&cam=2` → listă cu idp-uri.
2. Pentru fiecare idp, fetch `upl_pck2015.proiect?cam=2&idp=N` → parsare detalii.

Sursa: cdep.ro/pls/proiecte/upl_pck2015.{lista,proiect}
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

from schemas.proiect import CaracterProiect, Proiect, TimelineEvent, TipInitiativa
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
LIST_URL = BASE + "/pls/proiecte/upl_pck2015.lista?anp={year}&cam={cam}"
DETAIL_URL = BASE + "/pls/proiecte/upl_pck2015.proiect?cam={cam}&idp={idp}"

MAX_WORKERS = int(os.environ.get("CDEP_SCRAPE_WORKERS", "2"))


def _proiect_id(cam: int, idp: int) -> str:
    return hashlib.sha256(f"{cam}|{idp}".encode()).hexdigest()[:16]


def _parse_iso_date(s: str | None) -> date | None:
    """Parsează DD.MM.YYYY sau DD-MM-YYYY → date."""
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


def list_idps_for_year(year: int, cam: int = 2) -> list[int]:
    """Returnează idp-urile pentru un an (de la lista anp=YEAR)."""
    url = LIST_URL.format(year=year, cam=cam)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"list year {year}: {e}")
        return []

    sel = Selector(text=r.text)
    idps: list[int] = []
    for href in sel.css("a::attr(href)").getall():
        m = re.search(r"upl_pck2015\.proiect\?cam=\d+&idp=(\d+)", href)
        if m:
            idp = int(m.group(1))
            if idp not in idps:
                idps.append(idp)
    return idps


def _detect_tip(titlu: str) -> TipInitiativa:
    t = titlu.lower()
    if t.startswith("proiect"):
        return TipInitiativa.PROIECT_LEGE
    if t.startswith("propunere"):
        return TipInitiativa.PROPUNERE_LEGISLATIVA
    if "ordonanță de urgență" in t or "ordonanta de urgenta" in t or "oug" in t:
        return TipInitiativa.OUG
    if "ordonanța" in t or "ordonanta" in t:
        return TipInitiativa.OG
    return TipInitiativa.OTHER


def _detect_caracter(text: str) -> CaracterProiect:
    t = text.lower()
    if "organic" in t:
        return CaracterProiect.ORGANIC
    if "ordinar" in t:
        return CaracterProiect.ORDINAR
    return CaracterProiect.OTHER


def _strip_label(s: str) -> str:
    """Curăță un label: strip whitespace, dashes, colons, dots."""
    return s.strip().lstrip("- ").rstrip(": .").strip()


def _norm_key(s: str) -> str:
    """Normalizează cheia pentru lookup robust (lowercase + fără diacritice + fără punctuație finală)."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9 ]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def _lookup(fields: dict[str, str], *candidates: str) -> str | None:
    """Caută o cheie în fields prin normalizare."""
    norm_fields = {_norm_key(k): v for k, v in fields.items()}
    for cand in candidates:
        v = norm_fields.get(_norm_key(cand))
        if v:
            return v
    return None


def _extract_label_table(sel: Selector) -> dict[str, str]:
    """Extrage toate label/value din table-ul principal.

    Cdep.ro folosește `<tr><td bgcolor="fff0d8">label</td><td>valoare</td></tr>`
    (cu sau fără # în culoare).
    """
    fields: dict[str, str] = {}
    # XPath: găsește td-urile cu bgcolor care conține fff0d8 (case-insensitive)
    for tr in sel.css("tr"):
        tds = tr.xpath("./td")
        if len(tds) < 2:
            continue
        # Verific dacă primul td e label (bgcolor fff0d8)
        bg = tds[0].xpath("@bgcolor").get() or ""
        if "fff0d8" not in bg.lower():
            continue
        label_raw = " ".join(tds[0].css("*::text").getall())
        label = _strip_label(label_raw)
        if not label:
            continue
        # Valoarea: tot textul din td-ul valoare (poate avea <a>, <b>, etc.)
        value = " ".join(tds[1].css("*::text").getall())
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            fields[label] = value
    return fields


def _extract_timeline(sel: Selector) -> list[TimelineEvent]:
    """Extrage timeline-ul din secțiunea „Derularea procedurii legislative".

    Format: rânduri cu o celulă centrată conținând data (DD.MM.YYYY) și o celulă
    colspan=2 cu descrierea evenimentului.
    """
    events: list[TimelineEvent] = []
    for tr in sel.css("tr"):
        cells = tr.xpath("./td")
        if len(cells) < 2:
            continue
        # Caut prima celulă cu o dată DD.MM.YYYY
        for i, td in enumerate(cells):
            text = " ".join(td.css("*::text").getall()).strip()
            d = _parse_iso_date(text)
            if d:
                # Eveniment: textul din toate celulele rămase concatenat
                rest = []
                for j in range(i + 1, len(cells)):
                    rest_text = " ".join(cells[j].css("*::text").getall())
                    rest_text = re.sub(r"\s+", " ", rest_text).strip()
                    if rest_text and rest_text not in ("PA", "VC"):  # filter coduri scurte
                        rest.append(rest_text)
                eveniment = " ".join(rest).strip()
                if eveniment:
                    events.append(TimelineEvent(data=d, eveniment=eveniment[:300]))
                break
    return events


def parse_detail(idp: int, legislatura: int, cam: int = 2) -> Proiect | None:
    """Fetch & parse o pagină detaliu proiect."""
    url = DETAIL_URL.format(cam=cam, idp=idp)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  idp={idp}: {e}")
        return None

    sel = Selector(text=r.text)

    # 1. Titlu și nr_inregistrare din meta tags
    titlu = sel.xpath('//meta[@property="og:description"]/@content').get() or ""
    nr_inreg = sel.xpath('//meta[@property="og:title"]/@content').get() or ""
    titlu = titlu.strip() or "(fără titlu)"

    # 2. Câmpurile label/value din tabelul principal
    fields = _extract_label_table(sel)

    nr_cd = _lookup(fields, "Camera Deputaţilor", "Camera Deputaților")
    nr_senat = _lookup(fields, "Senat")
    nr_guv = _lookup(fields, "Guvern")
    nr_bpi = _lookup(fields, "B.P.I.", "BPI")
    initiator = _lookup(fields, "Initiator", "Iniţiator", "Inițiator")
    camera_dec = _lookup(fields, "Camera decizionala", "Camera decizională")
    stadiu = _lookup(fields, "Stadiu")
    caracter_text = _lookup(fields, "Caracter") or "ordinar"
    proc_urg_text = (_lookup(fields, "Procedura de urgenta", "Procedura de urgenţă") or "").lower()
    tip_text = _lookup(fields, "Tip initiativa", "Tip iniţiativă") or ""

    # 3. Lege X/YYYY din stadiu
    lege_nr = None
    if stadiu:
        m = re.search(r"Lege\s+(\d+/\d{4})", stadiu)
        if m:
            lege_nr = m.group(1)

    # 4. Decret nr. (caut în tot HTML-ul, e undeva după promulgare)
    decret_nr = None
    full_text = " ".join(sel.css("body *::text").getall())
    m = re.search(r"Decret\s+nr\.?\s*(\d+/\d{4})", full_text)
    if m:
        decret_nr = m.group(1)

    # 5. Vot rezultat
    vot_pentru = vot_contra = vot_abtineri = None
    m = re.search(r"pentru\s*=\s*(\d+).*?contra\s*=\s*(\d+).*?abtineri\s*=\s*(\d+)", full_text)
    if m:
        vot_pentru = int(m.group(1))
        vot_contra = int(m.group(2))
        vot_abtineri = int(m.group(3))

    # 6. Timeline
    timeline = _extract_timeline(sel)

    # 7. PDF documents
    pdfs = []
    for href in sel.css('a[href$=".pdf"]::attr(href)').getall():
        full = urljoin(BASE, href)
        if full not in pdfs:
            pdfs.append(full)

    # 8. Date cheie din timeline
    data_prez = None
    data_inreg_cd = None
    data_adopt_cd = None
    data_adopt_sen = None
    data_promulgare = None

    # Amendamente metadata
    amend_termen: date | None = None
    amend_admise: int | None = None
    amend_respinse: int | None = None

    for ev in timeline:
        # Strip diacritice pentru matching robust
        e = (
            unicodedata.normalize("NFD", ev.eveniment)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )
        if ("prezentare" in e or "primit" in e) and not data_prez:
            data_prez = ev.data
        elif "inregistrat" in e and not data_inreg_cd:
            data_inreg_cd = ev.data
        elif "adoptat" in e and "sedin" in e and "comun" in e:
            # Adoptat în ședință comună — pun pe ambele
            if not data_adopt_cd:
                data_adopt_cd = ev.data
            if not data_adopt_sen:
                data_adopt_sen = ev.data
        elif "adoptat" in e and "camera deputat" in e and not data_adopt_cd:
            data_adopt_cd = ev.data
        elif "adoptat" in e and "senat" in e and not data_adopt_sen:
            data_adopt_sen = ev.data
        elif "promulgat" in e and not data_promulgare:
            data_promulgare = ev.data

        # Termen depunere amendamente: "termen depunere amendamente: 03.02.2025, ora 16:00"
        if "termen depunere amendament" in e and amend_termen is None:
            m_term = re.search(r"(\d{1,2}\.\d{1,2}\.\d{4})", ev.eveniment)
            if m_term:
                amend_termen = _parse_iso_date(m_term.group(1))

        # Amendamente admise/respinse din "primire raport favorabil (25 amend. admise)"
        if "amend" in e:
            m_admise = re.search(
                r"\((\d+)\s*amend(?:amente)?\.?\s*admise\)", ev.eveniment, re.IGNORECASE
            )
            if m_admise and amend_admise is None:
                amend_admise = int(m_admise.group(1))
            m_respinse = re.search(
                r"\((\d+)\s*amend(?:amente)?\.?\s*respinse\)", ev.eveniment, re.IGNORECASE
            )
            if m_respinse and amend_respinse is None:
                amend_respinse = int(m_respinse.group(1))

    # Raport comisie PDF: caut printre PDF-uri unul cu pattern „rp\d+.pdf" în /comisii/
    raport_pdf: str | None = None
    for u in pdfs:
        if "/comisii/" in u and u.endswith(".pdf") and re.search(r"rp\d+\.pdf", u, re.IGNORECASE):
            raport_pdf = u
            break

    return Proiect(
        id=_proiect_id(cam, idp),
        cdep_idp=idp,
        cam=cam,
        legislatura=legislatura,
        nr_inregistrare=nr_inreg.strip() or nr_cd or nr_senat,
        nr_camera_deputati=nr_cd,
        nr_senat=nr_senat,
        nr_guvern=nr_guv,
        nr_bpi=nr_bpi,
        titlu=titlu[:500],
        tip=_detect_tip(tip_text or titlu),
        caracter=_detect_caracter(caracter_text),
        procedura_urgenta=("da" in proc_urg_text or "yes" in proc_urg_text),
        initiator=initiator,
        camera_decizionala=camera_dec,
        stadiu=stadiu,
        lege_nr=lege_nr,
        decret_nr=decret_nr,
        data_prezentare=data_prez,
        data_inregistrare_cd=data_inreg_cd,
        data_adoptare_cd=data_adopt_cd,
        data_adoptare_senat=data_adopt_sen,
        data_promulgare=data_promulgare,
        vot_pentru=vot_pentru,
        vot_contra=vot_contra,
        vot_abtineri=vot_abtineri,
        amendamente_termen_depunere=amend_termen,
        amendamente_admise=amend_admise,
        amendamente_respinse=amend_respinse,
        raport_comisie_pdf=raport_pdf,
        timeline=timeline,
        documente_pdf=pdfs[:30],  # cap la 30 PDF-uri ca să nu explodeze
        source_url=url,
    )


def scrape_year(year: int, legislatura: int, cam: int = 2) -> list[Proiect]:
    """Scrape toate proiectele dintr-un an, în paralel."""
    idps = list_idps_for_year(year, cam)
    logger.info(f"year={year} cam={cam}: {len(idps)} proiecte de procesat")

    results: list[Proiect] = []
    if not idps:
        return results

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idp = {executor.submit(parse_detail, idp, legislatura, cam): idp for idp in idps}
        for done, future in enumerate(as_completed(future_to_idp), start=1):
            idp = future_to_idp[future]
            try:
                p = future.result()
                if p:
                    results.append(p)
                if done % 100 == 0:
                    logger.info(f"  [{done}/{len(idps)}] processed")
            except Exception as e:
                logger.warning(f"  idp={idp} failed: {e}")

    logger.info(f"year={year} cam={cam}: {len(results)} parsed successfully")
    return results
