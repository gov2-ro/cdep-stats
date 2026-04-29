"""Generează pagini HTML din JSON-urile API ca să fie indexate de Pagefind.

Output: `pages/{tip}/{id}.html` — câte un fișier per entitate.
Pagefind apoi rulează peste `pages/` și produce indexul de căutare.

Tipuri indexate:
- Deputați (toate legislaturile)
- Voturi (event summary, NU breakdown nominal)
- Sancțiuni
- Interpelări
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "v1"
PAGES = ROOT / "pages"


def normalize_grup(raw: str | None) -> str:
    """Normalizează adresant_grup la abreviere standard.

    Datele din cdep.ro sunt murdare: scraperul prinde uneori 'AUR Destinatar' sau
    'Neafiliaţi Destinatari' din cauza câmpului următor. Aici curățăm.
    """
    if not raw:
        return "Neafiliat"
    # Strip ":" și cuvinte spurioase ("Destinatar", "Destinatari")
    cleaned = re.sub(r"[:;,]+", " ", raw)
    cleaned = re.sub(r"\bDestinatar[ie]?\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    if not cleaned:
        return "Neafiliat"

    # Strip diacritice pentru matching robust
    norm = unicodedata.normalize("NFD", cleaned).encode("ascii", "ignore").decode("ascii").lower()

    if "fara adeziune" in norm or "fara grup" in norm:
        return "Neafiliat"
    if "social democrat" in norm or norm == "psd":
        return "PSD"
    if "national liberal" in norm or norm == "pnl":
        return "PNL"
    if "salvati romania" in norm or norm == "usr":
        return "USR"
    if "alianta pentru unirea" in norm or norm == "aur":
        return "AUR"
    if "democrata maghiara" in norm or norm == "udmr":
        return "UDMR"
    if "s.o.s" in norm or norm.startswith("sos"):
        return "S.O.S."
    if "oamenilor tineri" in norm or norm == "pot":
        return "POT"
    if "minorit" in norm:
        return "Minorități"
    if "neafiliat" in norm:
        return "Neafiliat"
    # Fallback: ia primul cuvânt curățat
    return cleaned.split()[0]


def safe(s: str | None) -> str:
    """Escape pentru HTML."""
    return html.escape(s) if s else ""


def write_page(path: Path, title: str, body: str, meta_url: str = "") -> None:
    """Scrie un fișier HTML minimalist, optimizat pentru Pagefind indexing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    page = f"""<!doctype html>
<html lang="ro">
<head>
<meta charset="utf-8">
<title>{safe(title)}</title>
<meta name="description" content="{safe(title)}">
</head>
<body>
<main data-pagefind-body>
<h1>{safe(title)}</h1>
{body}
{f'<p><a href="{safe(meta_url)}">Sursa JSON</a></p>' if meta_url else ""}
</main>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def generate_deputati() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "deputati" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for d in data["data"]:
            comisii_html = ""
            if d.get("comisii"):
                comisii_html = "<h2>Comisii</h2><ul>"
                for c in d["comisii"]:
                    rol = f" — {safe(c.get('rol') or '')}" if c.get("rol") else ""
                    comisii_html += f"<li>{safe(c.get('comisia'))}{rol}</li>"
                comisii_html += "</ul>"
            partid = d.get("current_party") or "fără partid"
            judet = d.get("judet") or "necunoscut"
            body = f"""
<p data-pagefind-filter="tip:deputat" data-pagefind-meta="tip:deputat">
<strong data-pagefind-filter="legislatura:{d["legislatura"]}">Legislatura {d["legislatura"]}</strong>
&middot; <span data-pagefind-filter="partid:{safe(partid)}" data-pagefind-meta="partid">{safe(partid)}</span>
&middot; <span data-pagefind-filter="judet:{safe(judet)}" data-pagefind-meta="judet">{safe(judet)}</span>
{f"&middot; circumscripția {d['circumscriptie']}" if d.get("circumscriptie") else ""}
</p>
<p>Grup parlamentar: {safe(d.get("current_group") or "-")}</p>
{f"<p>Data nașterii: {d['birth_date']}</p>" if d.get("birth_date") else ""}
{comisii_html}
<p><a href="{safe(d["profile_url"])}" data-pagefind-ignore>Profil cdep.ro</a></p>
"""
            page_path = PAGES / "deputati" / f"{d['legislatura']}-{d['cdep_idm']}.html"
            write_page(
                page_path, d["name"], body, f"/data/v1/deputati/legislatura-{d['legislatura']}.json"
            )
            count += 1
    return count


def generate_voturi() -> int:
    count = 0
    voturi_dir = DATA / "voturi"
    if not voturi_dir.exists():
        return 0
    for leg_dir in voturi_dir.iterdir():
        if not leg_dir.is_dir():
            continue
        index_path = leg_dir / "_index.json"
        if not index_path.exists():
            continue
        idx = json.loads(index_path.read_text(encoding="utf-8"))
        for v in idx["data"]:
            counts = v.get("counts", {})
            ts = v.get("timestamp", "")[:16].replace("T", " ")
            year = (v.get("timestamp") or "")[:4] or "necunoscut"
            adoptat = "adoptat" if counts.get("pentru", 0) > counts.get("contra", 0) else "respins"
            body = f"""
<p data-pagefind-filter="tip:vot" data-pagefind-meta="tip:vot">
<strong data-pagefind-filter="an:{year}" data-pagefind-meta="data">{safe(ts)}</strong>
&middot; Legislatura {v["legislatura"]}
&middot; <span data-pagefind-filter="rezultat:{adoptat}">{adoptat}</span>
</p>
<p>
<span data-pagefind-meta="rezultat">
Pentru: {counts.get("pentru", 0)} &middot;
Contra: {counts.get("contra", 0)} &middot;
Abțineri: {counts.get("abtineri", 0)} &middot;
Nu au votat: {counts.get("nu_au_votat", 0)}
</span>
</p>
"""
            page_path = PAGES / "voturi" / f"{v['legislatura']}-{v['cdep_idv']}.html"
            write_page(
                page_path,
                v["descriere"] or f"Vot {v['cdep_idv']}",
                body,
                f"/data/v1/voturi/{v['legislatura']}/{v['cdep_idv']}.json",
            )
            count += 1
    return count


def generate_sanctiuni() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "sanctiuni" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for s in data["data"]:
            tip_sanc = s.get("tip") or "OTHER"
            body = f"""
<p data-pagefind-filter="tip:sanctiune" data-pagefind-meta="tip:sanctiune">
<strong data-pagefind-meta="data">{safe(s.get("data") or "")}</strong>
&middot; Legislatura {s["legislatura"]}
&middot; <span data-pagefind-filter="tip_sanctiune:{safe(tip_sanc)}" data-pagefind-meta="tip_sanctiune">{safe(tip_sanc)}</span>
</p>
<p>Deputat: {safe(s.get("deputat_nume"))}</p>
{f"<p>Procent: {s['procent']}% pe {s['durata_luni']} luni</p>" if s.get("procent") else ""}
{f"<p>Decizia: {safe(s['nr_decizie'])}</p>" if s.get("nr_decizie") else ""}
<p>{safe(s.get("descriere"))}</p>
"""
            page_path = PAGES / "sanctiuni" / f"{s['id']}.html"
            write_page(
                page_path,
                f"Sancțiune: {s.get('deputat_nume', 'necunoscut')}",
                body,
                f"/data/v1/sanctiuni/legislatura-{leg}.json",
            )
            count += 1
    return count


def generate_interpelari() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "interpelari" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for i in data["data"]:
            raspuns_section = ""
            if i.get("raspuns_primit"):
                raspuns_section = f"""
<h2>Răspuns</h2>
<p>Primit la: {safe(i.get("raspuns_data") or "")}</p>
<p>De la: {safe(i.get("raspuns_sursa") or "")}</p>
{f"<p>Comunicat de: {safe(i['raspuns_comunicat_de'])}</p>" if i.get("raspuns_comunicat_de") else ""}
"""
            year = (i.get("data_inregistrare") or "")[:4] or "necunoscut"
            raspuns_filter = "primit" if i.get("raspuns_primit") else "nu"
            grup = normalize_grup(i.get("adresant_grup"))
            body = f"""
<p data-pagefind-filter="tip:interpelare" data-pagefind-meta="tip:interpelare">
<strong data-pagefind-filter="an:{year}" data-pagefind-meta="data">{safe(i.get("data_inregistrare") or "")}</strong>
&middot; nr. {safe(i.get("nr_inregistrare"))}
&middot; Legislatura {i["legislatura"]}
</p>
<p>Adresant: <strong data-pagefind-filter="grup:{safe(grup)}">{safe(i.get("adresant_nume"))}</strong>
{f"({safe(i.get('adresant_grup'))})" if i.get("adresant_grup") else ""}</p>
<p>Destinatar: <span data-pagefind-meta="destinatar">{safe(i.get("destinatar"))}</span></p>
{f"<p>Mod: {safe(i.get('mod_adresare'))}</p>" if i.get("mod_adresare") else ""}
<p>Răspuns: <span data-pagefind-filter="raspuns:{raspuns_filter}">{"primit" if i.get("raspuns_primit") else "nu"}</span></p>
{raspuns_section}
"""
            page_path = PAGES / "interpelari" / f"{i['legislatura']}-{i['cdep_idi']}.html"
            write_page(
                page_path,
                i.get("titlu") or f"Interpelarea {i.get('nr_inregistrare')}",
                body,
                f"/data/v1/interpelari/legislatura-{leg}.json",
            )
            count += 1
    return count


def generate_comisii() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "comisii" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for c in data["data"]:
            membri_html = ""
            if c.get("membri"):
                membri_html = "<h2>Membri</h2><ul>"
                for m in c["membri"]:
                    rol = f" — {safe(m.get('rol') or '')}" if m.get("rol") else ""
                    partid = f" ({safe(m.get('partid') or '')})" if m.get("partid") else ""
                    membri_html += f"<li>{safe(m.get('deputat_nume'))}{rol}{partid}</li>"
                membri_html += "</ul>"
            conducere_html = ""
            if c.get("presedinte") or c.get("vicepresedinti") or c.get("secretari"):
                conducere_html = "<h2>Conducere</h2>"
                if c.get("presedinte"):
                    conducere_html += f"<p>Președinte: <strong>{safe(c['presedinte'])}</strong></p>"
                if c.get("vicepresedinti"):
                    conducere_html += (
                        f"<p>Vicepreședinți: {safe(', '.join(c['vicepresedinti']))}</p>"
                    )
                if c.get("secretari"):
                    conducere_html += f"<p>Secretari: {safe(', '.join(c['secretari']))}</p>"
            body = f"""
<p data-pagefind-filter="tip:comisie" data-pagefind-meta="tip:comisie">
<strong data-pagefind-filter="legislatura:{c["legislatura"]}">Legislatura {c["legislatura"]}</strong>
&middot; <span data-pagefind-filter="tip_comisie:{safe(c["tip"])}">{safe(c["tip"])}</span>
&middot; {c["nr_membri"]} membri
</p>
{conducere_html}
{membri_html}
"""
            page_path = PAGES / "comisii" / f"{c['id']}.html"
            write_page(
                page_path,
                c["nume"],
                body,
                f"/data/v1/comisii/legislatura-{leg}.json",
            )
            count += 1
    return count


def main() -> int:
    PAGES.mkdir(parents=True, exist_ok=True)
    print(f"Generating HTML pages in {PAGES}/")
    n_dep = generate_deputati()
    print(f"  deputați: {n_dep}")
    n_vot = generate_voturi()
    print(f"  voturi: {n_vot}")
    n_san = generate_sanctiuni()
    print(f"  sancțiuni: {n_san}")
    n_int = generate_interpelari()
    print(f"  interpelări: {n_int}")
    n_com = generate_comisii()
    print(f"  comisii: {n_com}")
    total = n_dep + n_vot + n_san + n_int + n_com
    print(f"\nTotal: {total} pagini HTML generate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
