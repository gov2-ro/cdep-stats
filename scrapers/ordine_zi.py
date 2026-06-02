"""Scraper pentru ordinea de zi a ședințelor plenului Camerei Deputaților.

Strategia:
1. Pentru o lună, fetch `/ords/pls/caseta/ecaseta2015.zile_ordinezi?lu=MM&an=YYYY`
   → returnează un șir cu zilele care au ședință (format CSV cu YYYYMMDD).
2. Pentru fiecare zi, fetch `/ords/pls/caseta/ecaseta2015.OrdineZi?dat=YYYYMMDD`
   și parsează tabelul cu punctele de pe agendă.

Sursa: cdep.ro/ords/pls/caseta/ecaseta2015.*
"""

from __future__ import annotations

import calendar
import hashlib
import logging
import re
import shutil
import sys
from datetime import date
from urllib.parse import urljoin

from parsel import Selector

from schemas.ordine_zi import DocOrdineZiItem, OrdineZi, OrdineZiItem
from scrapers._http import get

logger = logging.getLogger(__name__)

BASE = "https://www.cdep.ro"
LIST_URL = BASE + "/ords/pls/caseta/ecaseta2015.zile_ordinezi?lu={mm}&an={yyyy}"
DOCS_URL = BASE + "/ords/pls/caseta/ecaseta2015.more_docs_pl?ozitm={ozitm}&npl=1"
DETAIL_URL = BASE + "/ords/pls/caseta/ecaseta2015.OrdineZi?dat={yyyymmdd}"


def _session_id(cam: int, session_date: date) -> str:
    return hashlib.sha256(f"{cam}|{session_date.isoformat()}".encode()).hexdigest()[:16]


def _clean_descriere_html(raw: str) -> str:
    """Keep only b/i/br tags from raw inner HTML, normalised to lowercase."""
    # Normalise <B>, <I>, <BR> (and closing forms) to lowercase
    text = re.sub(
        r"<(/?)(b|i|br)\b([^>]*)>",
        lambda m: f"<{m.group(1)}{m.group(2).lower()}{m.group(3).strip()}>",
        raw,
        flags=re.IGNORECASE,
    )
    # Drop all other tags
    text = re.sub(r"<(?!/?(?:b|i|br)\b)[^>]+>", "", text)
    # Remove content-free wrappers
    text = re.sub(r"<b>\s*</b>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<i>\s*</i>", "", text, flags=re.IGNORECASE)
    # Strip leading/trailing whitespace and stray <br>
    text = text.strip()
    text = re.sub(r"^(<br\s*/?>|\s)+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"(<br\s*/?>|\s)+$", "", text, flags=re.IGNORECASE)
    # Collapse 3+ consecutive <br> to 2
    text = re.sub(r"(<br>){3,}", "<br><br>", text, flags=re.IGNORECASE)
    return text[:2000]


def _parse_iso_date(s: str | None) -> date | None:
    """DD.MM.YYYY sau DD-MM-YYYY sau DD/MM/YYYY → date."""
    if not s:
        return None
    m = re.match(r"(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{4})", s.strip())
    if not m:
        return None
    try:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except (ValueError, TypeError):
        return None


def _parse_title_dates(titlu: str) -> tuple[date | None, date | None]:
    """Extrage data (sau range de date) dintr-un titlu ca:

    'Ordinea de zi pentru sedinţa Camerei Deputaţilor din 26 - 27 mai 2026'
    'Ordinea de zi pentru sedinţa din 11 februarie 2026'
    'din 1 noiembrie 2026'

    Returnează (start_date, end_date_or_None).
    """
    months = {
        "ianuarie": 1,
        "februarie": 2,
        "martie": 3,
        "aprilie": 4,
        "mai": 5,
        "iunie": 6,
        "iulie": 7,
        "august": 8,
        "septembrie": 9,
        "octombrie": 10,
        "noiembrie": 11,
        "decembrie": 12,
    }
    # Range cu liniuță: "26 - 27 mai 2026" sau "26-27 mai 2026"
    m = re.search(
        r"(\d{1,2})\s*[\-\u2013]\s*(\d{1,2})\s+([a-zăâîșț]+)\s+(\d{4})",
        titlu,
        re.IGNORECASE,
    )
    if m:
        d1, d2, mo, y = int(m.group(1)), int(m.group(2)), m.group(3).lower(), int(m.group(4))
        mo_num = months.get(mo)
        if mo_num:
            try:
                return date(y, mo_num, d1), date(y, mo_num, d2)
            except ValueError:
                pass
    # O singură zi: "26 mai 2026"
    m = re.search(r"(\d{1,2})\s+([a-zăâîșț]+)\s+(\d{4})", titlu, re.IGNORECASE)
    if m:
        d, mo, y = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        mo_num = months.get(mo)
        if mo_num:
            try:
                return date(y, mo_num, d), None
            except ValueError:
                pass
    return None, None


def list_session_dates_for_month(year: int, month: int) -> list[date]:
    """Returnează lista zilelor cu ședință de plen într-o lună.

    cdep.ro returnează un șir cu virgule de tip "," + YYYYMMDD + ",..." prin AJAX.
    """
    url = LIST_URL.format(mm=f"{month:02d}", yyyy=year)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"list_session_dates {year}-{month:02d}: {e}")
        return []
    # Format observat: ",20260526,20260527,20260601,..."
    matches = re.findall(r"(\d{8})", r.text)
    out: list[date] = []
    seen: set[date] = set()
    for ymd in matches:
        try:
            d = date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
        except ValueError:
            continue
        if d not in seen and d.year == year and d.month == month:
            seen.add(d)
            out.append(d)
    return sorted(out)


def fetch_item_docs(ozitm: int) -> list[DocOrdineZiItem]:
    """Fetch documente asociate unui punct (more_docs_pl)."""
    url = DOCS_URL.format(ozitm=ozitm)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  docs ozitm={ozitm}: {e}")
        return []

    sel = Selector(text=r.text)
    docs: list[DocOrdineZiItem] = []

    # Outer table has 2 data cells: fisa_pl (td[0]) and caseta (td[2], after spacer)
    inner_tables = sel.css("table > tr > td > table")
    sursa_labels = ["fisa_pl", "caseta"]

    for inner_table, sursa in zip(inner_tables, sursa_labels):
        for tr in inner_table.css("tr"):
            cells = tr.css("td")
            # Skip header/separator rows (single cell spanning all columns)
            if not cells or cells[0].attrib.get("colspan"):
                continue
            if len(cells) < 2:
                continue

            date_raw = cells[0].css("::text").get("").strip().strip("\xa0")
            titlu = " ".join(t.strip() for t in cells[1].css("::text").getall() if t.strip())
            if not titlu:
                continue

            pdf_href = cells[2].css("a::attr(href)").get() if len(cells) > 2 else None
            docs.append(
                DocOrdineZiItem(
                    data=_parse_iso_date(date_raw) if date_raw else None,
                    titlu=titlu,
                    pdf_url=urljoin(BASE, pdf_href) if pdf_href else None,
                    sursa=sursa,
                )
            )

    return docs


def parse_session(session_date: date, legislatura: int, cam: int = 2) -> OrdineZi | None:
    """Fetch + parse ordinea de zi pentru o zi specifică."""
    ymd = session_date.strftime("%Y%m%d")
    url = DETAIL_URL.format(yyyymmdd=ymd)
    try:
        r = get(url)
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"  session {session_date}: {e}")
        return None

    sel = Selector(text=r.text)
    # Titlu din heading
    titlu = (sel.css("div.boxTitle h1::text").get() or "").strip()
    if not titlu:
        # Posibil nu e ședință în această zi (cdep.ro returnează pagina goală)
        logger.info(f"  {session_date}: fără titlu — probabil nu e ședință")
        return None

    # Range de date din titlu
    start, end = _parse_title_dates(titlu)
    if not start:
        start = session_date
    # session_date_end doar dacă e diferit de start
    end_date = end if end and end != start else None

    # Data aprobării (text "Aprobata: DD.MM.YYYY")
    body_text = " ".join(sel.css("body *::text").getall())
    body_text = re.sub(r"\s+", " ", body_text)
    data_aprobare = None
    m_ap = re.search(r"Aprobata:\s*(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})", body_text)
    if m_ap:
        data_aprobare = _parse_iso_date(m_ap.group(1))

    # PDF cu ordinea completă
    pdf_url = None
    for href in sel.css("a::attr(href)").getall():
        if "OZ" in href and ".pdf" in href.lower() and "caseta/upload" in href:
            pdf_url = urljoin(BASE, href)
            break

    # Punctele de pe ordinea de zi — tabelul cu 4 coloane
    items: list[OrdineZiItem] = []
    # Identificăm tabelul: are <th>Numar<br>inreg.</th>
    for table in sel.css("table"):
        ths = [t.strip() for t in table.css("th::text").getall()]
        if not any("nreg" in t for t in ths):
            continue
        # E tabelul nostru
        for tr in table.css("tbody tr"):
            # Skip rândurile care sunt iframe-uri ascunse
            tr_id = tr.attrib.get("id") or ""
            if tr_id.startswith("row"):
                continue
            cells = tr.css("td")
            if len(cells) < 4:
                continue

            # Col 0: poziție ("-" sau "1.", "2.", "PCT1", etc.)
            poz_text = "".join(cells[0].css("::text").getall()).strip()
            poz_text = re.sub(r"^PCT\.?", "", poz_text)
            poz_text = poz_text.rstrip(".").strip()
            pozitie = int(poz_text) if poz_text.isdigit() else None

            # Col 1: nr_inregistrare + link la /proiecte
            nr_inregistrare = None
            idp = None
            link = cells[1].css('a[href*="upl_pck2015.proiect"]::attr(href)').get()
            if link:
                nr_inregistrare = (
                    cells[1].css('a[href*="upl_pck2015.proiect"]::text').get() or ""
                ).strip()
                m_idp = re.search(r"idp=(\d+)", link)
                if m_idp:
                    idp = int(m_idp.group(1))
            else:
                nr_text = "".join(cells[1].css("::text").getall()).strip()
                if nr_text and nr_text != "-":
                    nr_inregistrare = nr_text

            # Col 2: descriere — preserve <b>/<i>/<br> markup from source
            descriere = _clean_descriere_html("".join(cells[2].xpath("node()").getall()))
            if not descriere:
                continue

            # Col 3: doc PDF + link more_docs
            doc_pdf = cells[3].css('a[href*=".pdf"]::attr(href)').get()
            doc_pdf_url = urljoin(BASE, doc_pdf) if doc_pdf else None

            # ozitm pentru documentele asociate
            ozitm = None
            for href in cells[3].css("a::attr(href)").getall():
                m_oz = re.search(r"ozitm=(\d+)", href)
                if m_oz:
                    ozitm = int(m_oz.group(1))
                    break

            item_docs = fetch_item_docs(ozitm) if ozitm else []
            items.append(
                OrdineZiItem(
                    pozitie=pozitie,
                    nr_inregistrare=nr_inregistrare,
                    idp=idp,
                    descriere=descriere,
                    doc_pdf_url=doc_pdf_url,
                    ozitm=ozitm,
                    docs=item_docs,
                )
            )
        break  # un singur tabel cu acest header

    return OrdineZi(
        id=_session_id(cam, start),
        session_date=start,
        session_date_end=end_date,
        legislatura=legislatura,
        cam=cam,
        titlu=titlu[:500],
        data_aprobare=data_aprobare,
        pdf_url=pdf_url,
        items=items,
        source_url=url,
    )


def scrape_year(
    year: int,
    legislatura: int,
    cam: int = 2,
    skip_dates: set[date] | None = None,
) -> list[OrdineZi]:
    """Scrape ordinile de zi pentru toate ședințele dintr-un an.

    Args:
        skip_dates: opțional, set de date deja procesate; se sare peste ele.
    """
    skip = skip_dates or set()
    all_dates: list[date] = []
    for month in range(1, 13):
        # Optimizare: nu interogăm luni viitoare
        today = date.today()
        if year == today.year and month > today.month:
            break
        days = list_session_dates_for_month(year, month)
        all_dates.extend(days)

    new_dates = [d for d in all_dates if d not in skip]
    skipped = len(all_dates) - len(new_dates)
    logger.info(
        f"year={year}: {len(all_dates)} sesiuni total, {skipped} skip, {len(new_dates)} de procesat"
    )

    results: list[OrdineZi] = []
    total = len(new_dates)
    tty = total > 0 and sys.stderr.isatty()
    for i, d in enumerate(new_dates, 1):
        if tty:
            cols = shutil.get_terminal_size((80, 24)).columns
            pct = i * 100 // total
            bar = "=" * (pct // 5) + "-" * (20 - pct // 5)
            line = f"  [{bar}] {i}/{total}  {d}"
            sys.stderr.write(f"\r\033[K{line[:cols - 1]}")
            sys.stderr.flush()
        try:
            ord_z = parse_session(d, legislatura=legislatura, cam=cam)
            if ord_z:
                results.append(ord_z)
        except Exception as e:
            logger.warning(f"  {d}: {e}")
    if tty:
        sys.stderr.write("\n")

    logger.info(f"year={year}: {len(results)} parsed successfully")
    return results


# Suprimă warning de la calendar dacă nu îl folosim
_ = calendar
