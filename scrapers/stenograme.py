"""Scraper pentru stenograme ședințe plen.

Strategia:
1. Calendar anual: `/ords/pls/steno/steno2015.calendar?cam=2&an=YYYY&TIP=0&idl=1`
   → returnează HTML cu link-uri la zilele cu ședință.
2. Detail: `/ords/pls/steno/steno2015.data?cam=2&dat=YYYYMMDD&idl=1`
   → returnează stenograma propriu-zisă (text + intervenții).

NOTĂ: parserul de detail e WIP — necesită HTML real al unei stenograme pentru
calibrare exactă. Pe primă iterație extragem doar text complet + lungime.

Sursa: cdep.ro/ords/pls/steno/steno2015.*
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import date

from parsel import Selector

from schemas.stenograma import Stenograma
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
CAL_URL = BASE + "/ords/pls/steno/steno2015.calendar?cam={cam}&an={year}&TIP=0&idl=1"
DETAIL_URL = BASE + "/ords/pls/steno/steno2015.data?cam={cam}&dat={ymd}&idl=1"


def _steno_id(cam: int, session_date: date) -> str:
    return hashlib.sha256(f"{cam}|{session_date.isoformat()}".encode()).hexdigest()[:16]


def list_session_dates_for_year(year: int, cam: int = 2) -> list[date]:
    """Listează datele cu ședință de plen pentru un an.

    Parsează HTML-ul calendarului anual și extrage link-urile `steno2015.data?dat=YYYYMMDD`.
    """
    url = CAL_URL.format(cam=cam, year=year)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"calendar {year} cam={cam}: {e}")
        return []
    sel = Selector(text=r.text)
    seen: set[date] = set()
    out: list[date] = []
    for href in sel.css('a[href*="steno2015.data"]::attr(href)').getall():
        m = re.search(r"dat=(\d{8})", href)
        if not m:
            continue
        ymd = m.group(1)
        try:
            d = date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
        except ValueError:
            continue
        if d in seen or d.year != year:
            continue
        seen.add(d)
        out.append(d)
    return sorted(out)


def parse_session(session_date: date, legislatura: int, cam: int = 2) -> Stenograma | None:
    """Fetch + parse stenograma pentru o zi specifică.

    Versiune inițială — extrage text complet și aproximează intervențiile.
    Schema HTML exactă necesită calibrare cu HTML real.
    """
    ymd = session_date.strftime("%Y%m%d")
    url = DETAIL_URL.format(cam=cam, ymd=ymd)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  steno {session_date}: {e}")
        return None

    sel = Selector(text=r.text)
    # Titlu din heading (similar cu alte pagini cdep.ro)
    titlu = (sel.css("div.boxTitle h1::text").get() or "").strip() or None

    # Textul complet — extragem și ne uităm la lungime
    body_text = " ".join(sel.css("#olddiv ::text").getall())
    body_text = re.sub(r"\s+", " ", body_text).strip()
    if not body_text:
        return None

    return Stenograma(
        id=_steno_id(cam, session_date),
        session_date=session_date,
        cam=cam,
        legislatura=legislatura,
        titlu=titlu[:500] if titlu else None,
        interventions=[],  # WIP — necesită HTML real pentru parsare exactă
        text_complet_len=len(body_text),
        source_url=url,
    )


def scrape_year(
    year: int,
    legislatura: int,
    cam: int = 2,
    skip_dates: set[date] | None = None,
) -> list[Stenograma]:
    """Scrape toate stenogramele unui an."""
    skip = skip_dates or set()
    all_dates = list_session_dates_for_year(year, cam=cam)
    new_dates = [d for d in all_dates if d not in skip]
    skipped = len(all_dates) - len(new_dates)
    logger.info(
        f"year={year} cam={cam}: {len(all_dates)} sesiuni total, "
        f"{skipped} skip, {len(new_dates)} de procesat"
    )

    results: list[Stenograma] = []
    for i, d in enumerate(new_dates, 1):
        try:
            st = parse_session(d, legislatura=legislatura, cam=cam)
            if st:
                results.append(st)
                if i % 10 == 0:
                    logger.info(f"  [{i}/{len(new_dates)}] processed")
        except Exception as e:
            logger.warning(f"  {d}: {e}")

    logger.info(f"year={year}: {len(results)} parsed successfully")
    return results
