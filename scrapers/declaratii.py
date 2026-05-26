"""Scraper pentru declarații de avere și interese ale deputaților.

Strategia:
1. Un SINGUR fetch la `/ords/pls/dic/declaratii2015.deputati?tip=ai&leg=YYYY`
   returnează tabelul cu toți deputații + PDF link-uri (avere + interese).
2. Parsăm rândul pentru fiecare deputat (id + nume + grup + multiple PDF-uri cu data).

URL pattern: cdep.ro/ords/pls/dic/declaratii2015.deputati?tip={a|i|ai}&leg=YYYY
PDF format: /declaratii/deputati/{leg}/{avere|interese}/{nnn}{suffix}.pdf
"""

from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from datetime import date
from urllib.parse import urljoin

from parsel import Selector

from schemas.declaratie import DeclaratieDeputat, DeclaratieFisier
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
LIST_URL = BASE + "/ords/pls/dic/declaratii2015.deputati?tip=ai&leg={leg}"


def _strip_diacritics(s: str) -> str:
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode("ascii")


def _voter_canonical_id(name: str) -> str:
    """Same convention as scrapers/deputati.py — fără birth_date.

    Atenție: NU produce același id ca scrapers/deputati._canonical_id (care include birth_date).
    E ID-ul "fallback" pentru cross-link când birth_date nu e disponibil.
    """
    norm = " ".join(_strip_diacritics(name).lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()[:16]


def _entity_id(leg: int, idm: int) -> str:
    return hashlib.sha256(f"{leg}|{idm}".encode()).hexdigest()[:16]


def _parse_date(s: str | None) -> date | None:
    """DD.MM.YYYY → date."""
    if not s:
        return None
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except (ValueError, TypeError):
        return None


def _extract_pdf_files(cell: Selector) -> list[DeclaratieFisier]:
    """Extrage toate fișierele PDF dintr-o celulă de declarații.

    Structura observată: sub-tabel cu rânduri ``<tr><td>icon_pdf</td><td>data</td></tr>``.
    Fiecare rând = un PDF (declarație inițială sau modificare).
    """
    files: list[DeclaratieFisier] = []
    seen: set[str] = set()
    for sub_tr in cell.css("tr"):
        # Caut primul link PDF din rând
        href = sub_tr.css('a[href$=".pdf"]::attr(href)').get()
        if not href:
            continue
        full = urljoin(BASE, href)
        if full in seen:
            continue
        seen.add(full)
        # Data — apare ca text într-un alt tag <a> din același tr
        date_text = ""
        for a in sub_tr.css("a::text").getall():
            if re.match(r"\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}", a.strip()):
                date_text = a.strip()
                break
        files.append(DeclaratieFisier(url=full, data=_parse_date(date_text)))
    return files


def scrape(leg: int) -> list[DeclaratieDeputat]:
    """Scrape lista de declarații pentru o legislatură.

    UN SINGUR request HTTP — pagina returnează tabelul complet cu toți deputații.
    Rapid (sub 1 secundă) + idempotent.
    """
    url = LIST_URL.format(leg=leg)
    logger.info(f"declaratii scrape: leg={leg}")
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.error(f"  fetch failed: {e}")
        return []

    sel = Selector(text=r.text)
    results: list[DeclaratieDeputat] = []

    # Iterăm prin tabelul principal — fiecare deputat e un <tr> cu 5 celule DIRECTE:
    # [#] [nume+link mp] [partid+link gp] [declaratii avere] [declaratii interese]
    # ATENȚIE: celulele 4-5 conțin SUB-tabele cu PDF-uri, deci folosim xpath direct children
    # ca să nu prindem și sub-td-urile.
    for tr in sel.css("tr"):
        cells = tr.xpath("./td")
        if len(cells) < 5:
            continue
        # Validare: prima celulă trebuie să fie un număr (ex. "1.", "2.", "335.")
        nr_text = "".join(cells[0].css("::text").getall()).strip().rstrip(".")
        if not nr_text.isdigit():
            continue

        # Col 1: nume + link la profil deputat
        mp_link = cells[1].css('a[href*="structura2015.mp"]::attr(href)').get()
        if not mp_link:
            continue
        m_idm = re.search(r"idm=(\d+)", mp_link)
        if not m_idm:
            continue
        idm = int(m_idm.group(1))
        nume = (cells[1].css('a[href*="structura2015.mp"]::text').get() or "").strip()
        if not nume:
            continue

        # Col 2: partid (link la gp)
        partid_short = (
            cells[2].css('a[href*="structura2015.gp"]::text').get() or ""
        ).strip() or None

        # Col 3: declarații de avere — sub-tabel cu PDF-uri
        avere = _extract_pdf_files(cells[3])

        # Col 4: declarații de interese — sub-tabel cu PDF-uri
        interese = _extract_pdf_files(cells[4])

        results.append(
            DeclaratieDeputat(
                id=_entity_id(leg, idm),
                cdep_idm=idm,
                deputat_nume=nume,
                deputat_canonical_id=_voter_canonical_id(nume),
                legislatura=leg,
                partid_short=partid_short,
                avere=avere,
                interese=interese,
                source_url=url,
            )
        )

    logger.info(f"declaratii leg={leg}: {len(results)} deputați")
    return results
