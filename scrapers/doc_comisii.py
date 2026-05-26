"""Scraper pentru documente comisii parlamentare (rapoarte, avize, sinteze, procese verbale).

Strategia:
1. `/ords/pls/proiecte/upl_com2015.lista` returnează pagina cu 99 documente
2. Paginare prin `?nrc=N` (offset multiplu de 100): 1..99, 100..199, 200..299, ...
3. Total observat: ~85.895 înregistrări → ~870 pagini

Sursa: cdep.ro/ords/pls/proiecte/upl_com2015.lista
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import date
from urllib.parse import urljoin

from parsel import Selector

from schemas.doc_comisie import DocComisie
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
LIST_URL = BASE + "/ords/pls/proiecte/upl_com2015.lista{query}"


def _doc_id(pdf_url: str) -> str:
    return hashlib.sha256(pdf_url.encode()).hexdigest()[:16]


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except (ValueError, TypeError):
        return None


def _detect_tip(titlu_text: str) -> str:
    t = titlu_text.upper()
    if "RAPORT" in t:
        return "raport"
    if "AVIZ" in t:
        return "aviz"
    if "SINTEZA" in t or "SINTEZĂ" in t:
        return "sinteza"
    if "PROCESUL VERBAL" in t or "PROCES VERBAL" in t or "PROCES-VERBAL" in t:
        return "proces_verbal"
    return "other"


def parse_page(html: str, source_url: str) -> list[DocComisie]:
    """Parsează o pagină cu 99 documente comisii."""
    sel = Selector(text=html)
    results: list[DocComisie] = []

    for tr in sel.css("tr"):
        cells = tr.xpath("./td")
        if len(cells) < 5:
            continue
        # Validare: prima celulă e număr
        nr_text = "".join(cells[0].css("::text").getall()).strip().rstrip(".")
        if not nr_text.isdigit():
            continue

        # Col 1: PDF (primul link)
        pdf_href = cells[1].css('a[href$=".pdf"]::attr(href)').get()
        if not pdf_href:
            continue
        pdf_url = urljoin(BASE, pdf_href)

        # Col 2: data (string optional)
        data_text = "".join(cells[2].css("::text").getall()).strip()
        data_doc = _parse_date(data_text) if data_text else None

        # Col 3: titlu + cross-link la proiect
        titlu_text = " ".join(p.strip() for p in cells[3].css("::text").getall() if p.strip())
        titlu_text = re.sub(r"\s+", " ", titlu_text)
        idp = None
        nr_proiect = None
        proj_link = cells[3].css('a[href*="upl_pck2015.proiect"]::attr(href)').get()
        if proj_link:
            m_idp = re.search(r"idp=(\d+)", proj_link)
            if m_idp:
                idp = int(m_idp.group(1))
            nr_proiect = (
                cells[3].css('a[href*="upl_pck2015.proiect"]::text').get() or ""
            ).strip() or None

        tip = _detect_tip(titlu_text)

        # Col 4: comisia/comisiile emitente (poate fi multiple link-uri)
        comisii = []
        for a in cells[4].css('a[href*="structura2015.co"]'):
            href = a.attrib.get("href") or ""
            m_idc = re.search(r"idc=(\d+)", href)
            m_leg = re.search(r"leg=(\d+)", href)
            nume = (a.css("::text").get() or "").strip()
            if m_idc and nume:
                comisii.append(
                    {
                        "idc": int(m_idc.group(1)),
                        "nume": nume,
                        "leg": int(m_leg.group(1)) if m_leg else None,
                    }
                )

        results.append(
            DocComisie(
                id=_doc_id(pdf_url),
                pdf_url=pdf_url,
                data=data_doc,
                tip=tip,
                titlu=titlu_text[:500],
                idp=idp,
                nr_proiect=nr_proiect,
                comisii=comisii,
                source_url=source_url,
            )
        )

    return results


def scrape_pages(
    max_pages: int = 1,
    seen_pdf_urls: set[str] | None = None,
) -> list[DocComisie]:
    """Scrape primele N pagini (99 docs per pagină).

    Args:
        max_pages: numărul de pagini de scrappiat (de la cele mai recente).
        seen_pdf_urls: set de PDF URL-uri deja procesate; oprire incrementală
                       când prima pagină nu mai aduce documente noi.
    """
    seen = seen_pdf_urls or set()
    results: list[DocComisie] = []

    for page_idx in range(max_pages):
        nrc = page_idx * 100  # pagina 0 = nrc=0 (sau lipsă), pagina 1 = nrc=100, etc.
        query = f"?nrc={nrc}" if nrc > 0 else ""
        url = LIST_URL.format(query=query)
        logger.info(f"docs comisii: page {page_idx + 1}/{max_pages} (nrc={nrc})")
        try:
            r = get(url)
            r.raise_for_status()
        except Exception as e:
            logger.warning(f"  page {page_idx + 1}: {e}")
            continue

        page_docs = parse_page(r.text, url)
        # Filter pe cele necunoscute
        new_docs = [d for d in page_docs if str(d.pdf_url) not in seen]
        # Stop incremental dacă pagina 0 (cea mai recentă) nu aduce nimic nou
        if page_idx == 0 and not new_docs and seen:
            logger.info("  pagina 1 fără documente noi — stop incremental")
            return results
        results.extend(new_docs)
        for d in new_docs:
            seen.add(str(d.pdf_url))
        if len(page_docs) < 99:
            # Ultima pagină — am ajuns la final
            break

    return results
