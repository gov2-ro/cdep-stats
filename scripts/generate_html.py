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
    corr_path = DATA / "correspondence" / "monitorul_idm_lookup.json"
    corr = json.loads(corr_path.read_text(encoding="utf-8")) if corr_path.exists() else {}
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
            monitorul_url = (corr.get(f"{d['cdep_idm']}_{d['legislatura']}") or {}).get("monitorul_url")
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
{f'<p><a href="{safe(monitorul_url)}" data-pagefind-ignore>Profil monitorul.ai</a></p>' if monitorul_url else ''}
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


def generate_motiuni() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "motiuni" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for m in data["data"]:
            tip = m.get("tip") or "simpla"
            rezultat = m.get("rezultat") or "in_procedura"
            year = (m.get("data_inregistrare") or "")[:4] or "necunoscut"
            vot_html = ""
            if m.get("vot_pentru") is not None:
                vot_html = (
                    f"<p>Vot ({m.get('data_vot') or '-'}): "
                    f"pentru={m['vot_pentru']}, "
                    f"contra={m.get('vot_contra', 0)}, "
                    f"abțineri={m.get('vot_abtineri', 0)}</p>"
                )
            semnatari_html = ""
            if m.get("semnatari"):
                semnatari_html = f"<p>{len(m['semnatari'])} semnatari listați nominal</p>"
            body = f"""
<p data-pagefind-filter="tip:motiune" data-pagefind-meta="tip:motiune">
<strong data-pagefind-filter="tip_motiune:{safe(tip)}">{safe(tip)}</strong>
&middot; Legislatura {m["legislatura"]}
&middot; <span data-pagefind-filter="an:{year}">{safe(m.get("data_inregistrare") or "")}</span>
&middot; <span data-pagefind-filter="rezultat_motiune:{safe(rezultat)}">{safe(rezultat)}</span>
</p>
<p>Inițiatori: {safe(m.get("initiatori_descriere") or "-")}</p>
{f"<p>Nr. înregistrare: {safe(m.get('nr_inregistrare'))}</p>" if m.get("nr_inregistrare") else ""}
{vot_html}
{semnatari_html}
"""
            page_path = PAGES / "motiuni" / f"{m['cam']}-{m['cdep_idm']}.html"
            write_page(
                page_path,
                m["titlu"],
                body,
                f"/data/v1/motiuni/legislatura-{leg}.json",
            )
            count += 1
    return count


def generate_proiecte() -> int:
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "proiecte" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for p in data["data"]:
            year = (p.get("data_inregistrare_cd") or p.get("data_prezentare") or "")[:4] or "?"
            stadiu = p.get("stadiu") or "necunoscut"
            stadiu_filter = (
                "promulgat"
                if p.get("lege_nr")
                else (
                    "respins"
                    if "respins" in stadiu.lower()
                    else ("retras" if "retras" in stadiu.lower() else "în lucru")
                )
            )
            initiator = p.get("initiator") or "necunoscut"
            urgent = "urgenta" if p.get("procedura_urgenta") else "ordinara"

            timeline_html = ""
            if p.get("timeline"):
                timeline_html = "<h2>Timeline</h2><ul>"
                for ev in p["timeline"][:30]:
                    timeline_html += (
                        f"<li>{safe(ev.get('data') or '')}: {safe(ev.get('eveniment') or '')}</li>"
                    )
                timeline_html += "</ul>"

            vot_html = ""
            if p.get("vot_pentru") is not None:
                vot_html = (
                    f"<p>Vot final: pentru={p['vot_pentru']}, "
                    f"contra={p.get('vot_contra', 0)}, "
                    f"abțineri={p.get('vot_abtineri', 0)}</p>"
                )

            body = f"""
<p data-pagefind-filter="tip:proiect" data-pagefind-meta="tip:proiect">
<strong data-pagefind-filter="an:{year}">{safe(p.get("nr_camera_deputati") or p.get("nr_inregistrare") or "")}</strong>
&middot; Legislatura {p["legislatura"]}
&middot; <span data-pagefind-filter="stadiu:{stadiu_filter}">{safe(stadiu)}</span>
&middot; <span data-pagefind-filter="initiator:{safe(initiator[:30])}">{safe(initiator)}</span>
&middot; <span data-pagefind-filter="procedura:{urgent}">{urgent}</span>
</p>
<p>Caracter: {safe(p.get("caracter") or "")} &middot; Cameră decizională: {safe(p.get("camera_decizionala") or "-")}</p>
{f"<p>Lege: <strong>{safe(p['lege_nr'])}</strong> (Decret {safe(p.get('decret_nr') or '-')})</p>" if p.get("lege_nr") else ""}
{vot_html}
{timeline_html}
"""
            page_path = PAGES / "proiecte" / f"{p['cam']}-{p['cdep_idp']}.html"
            write_page(
                page_path,
                p["titlu"],
                body,
                f"/data/v1/proiecte/legislatura-{leg}.json",
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


def generate_ordine_zi() -> int:
    """Generează pagini HTML pentru ordinea de zi a ședințelor (cross-link la proiecte)."""
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "ordine-zi" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for sesiune in data["data"]:
            items_html = ""
            if sesiune.get("items"):
                items_html = "<h2>Puncte pe ordinea de zi</h2><ol>"
                for it in sesiune["items"]:
                    nr = (
                        f" <strong>{safe(it.get('nr_inregistrare') or '')}</strong> -"
                        if it.get("nr_inregistrare")
                        else ""
                    )
                    items_html += f"<li>{nr} {safe(it.get('descriere', ''))}</li>"
                items_html += "</ol>"
            data_aprobare = sesiune.get("data_aprobare") or ""
            body = f"""
<p data-pagefind-filter="tip:ordine_zi" data-pagefind-meta="tip:ordine_zi">
<strong data-pagefind-filter="legislatura:{sesiune["legislatura"]}">Legislatura {sesiune["legislatura"]}</strong>
&middot; Ședință din <span data-pagefind-filter="data:{sesiune["session_date"]}">{safe(sesiune["session_date"])}</span>
{f"&middot; Aprobată: {safe(data_aprobare)}" if data_aprobare else ""}
&middot; {len(sesiune.get("items", []))} puncte
</p>
{items_html}
"""
            ymd = sesiune["session_date"].replace("-", "")
            page_path = PAGES / "ordine-zi" / f"{leg}-{ymd}.html"
            write_page(
                page_path,
                sesiune.get("titlu", f"Ordinea de zi {sesiune['session_date']}"),
                body,
                f"/data/v1/ordine-zi/legislatura-{leg}.json",
            )
            count += 1
    return count


def generate_declaratii() -> int:
    """Generează pagini pentru declarațiile de avere ale fiecărui deputat."""
    count = 0
    for leg in [2024, 2020, 2016]:
        f = DATA / "declaratii" / f"legislatura-{leg}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        for d in data["data"]:
            avere_html = ""
            if d.get("avere"):
                avere_html = "<h2>Declarații de avere</h2><ul>"
                for a in d["avere"]:
                    avere_html += (
                        f'<li><a href="{safe(a["url"])}">PDF</a> '
                        f"— {safe(a.get('data') or 'fără dată')}</li>"
                    )
                avere_html += "</ul>"
            interese_html = ""
            if d.get("interese"):
                interese_html = "<h2>Declarații de interese</h2><ul>"
                for i in d["interese"]:
                    interese_html += (
                        f'<li><a href="{safe(i["url"])}">PDF</a> '
                        f"— {safe(i.get('data') or 'fără dată')}</li>"
                    )
                interese_html += "</ul>"
            partid = d.get("partid_short") or "neafiliat"
            body = f"""
<p data-pagefind-filter="tip:declaratie" data-pagefind-meta="tip:declaratie">
<strong>{safe(d["deputat_nume"])}</strong>
&middot; <span data-pagefind-filter="partid:{safe(partid)}">{safe(partid)}</span>
&middot; <span data-pagefind-filter="legislatura:{d["legislatura"]}">Legislatura {d["legislatura"]}</span>
&middot; {len(d.get("avere", []))} decl. avere, {len(d.get("interese", []))} decl. interese
</p>
{avere_html}
{interese_html}
"""
            page_path = PAGES / "declaratii" / f"{leg}-{d['cdep_idm']}.html"
            write_page(
                page_path,
                f"Declarații {d['deputat_nume']} ({partid})",
                body,
                f"/data/v1/declaratii/legislatura-{leg}.json",
            )
            count += 1
    return count


def generate_stenograme() -> int:
    """Generează pagini pentru stenogramele ședințelor (din _index)."""
    count = 0
    for leg in [2024, 2020, 2016]:
        idx = DATA / "stenograme" / f"legislatura-{leg}" / "_index.json"
        if not idx.exists():
            continue
        data = json.loads(idx.read_text(encoding="utf-8"))
        for s in data["data"]:
            body = f"""
<p data-pagefind-filter="tip:stenograma" data-pagefind-meta="tip:stenograma">
<strong>Stenograma ședinței plen</strong>
&middot; <span data-pagefind-filter="data:{s["session_date"]}">{safe(s["session_date"])}</span>
&middot; <span data-pagefind-filter="legislatura:{s["legislatura"]}">Legislatura {s["legislatura"]}</span>
{f"&middot; ~{s['text_complet_len']:,} caractere text" if s.get("text_complet_len") else ""}
</p>
{f"<p>{safe(s['titlu'])}</p>" if s.get("titlu") else ""}
"""
            ymd = s["session_date"].replace("-", "")
            page_path = PAGES / "stenograme" / f"{leg}-{ymd}.html"
            write_page(
                page_path,
                s.get("titlu") or f"Stenograma {s['session_date']}",
                body,
                f"/data/v1/stenograme/legislatura-{leg}/{ymd}.json",
            )
            count += 1
    return count


def generate_doc_comisii() -> int:
    """Generează pagini pentru documente comisii (rapoarte, avize, sinteze)."""
    f = DATA / "doc-comisii" / "all.json"
    if not f.exists():
        return 0
    data = json.loads(f.read_text(encoding="utf-8"))
    count = 0
    for d in data["data"]:
        comisii_str = ", ".join(c.get("nume", "?") for c in d.get("comisii", []))
        data_doc = d.get("data") or "fără dată"
        proi_link = (
            f' <a href="/proiect.html?idp={d["idp"]}">PL {safe(d.get("nr_proiect") or "?")}</a>'
            if d.get("idp")
            else ""
        )
        body = f"""
<p data-pagefind-filter="tip:doc_comisie" data-pagefind-meta="tip:doc_comisie">
<strong data-pagefind-filter="tip_doc:{safe(d["tip"])}">{safe(d["tip"]).upper()}</strong>
&middot; <span data-pagefind-filter="data:{safe(data_doc)}">{safe(data_doc)}</span>
{f"&middot; Comisia: {safe(comisii_str)}" if comisii_str else ""}
{proi_link}
&middot; <a href="{safe(d["pdf_url"])}">PDF</a>
</p>
<p>{safe(d.get("titlu", ""))}</p>
"""
        page_path = PAGES / "doc-comisii" / f"{d['id']}.html"
        write_page(
            page_path,
            d.get("titlu", "Document comisie")[:120],
            body,
            "/data/v1/doc-comisii/all.json",
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
    n_pro = generate_proiecte()
    print(f"  proiecte: {n_pro}")
    n_mot = generate_motiuni()
    print(f"  motiuni: {n_mot}")
    n_oz = generate_ordine_zi()
    print(f"  ordine-zi: {n_oz}")
    n_dcl = generate_declaratii()
    print(f"  declarații: {n_dcl}")
    n_stn = generate_stenograme()
    print(f"  stenograme: {n_stn}")
    n_dc = generate_doc_comisii()
    print(f"  doc-comisii: {n_dc}")
    total = n_dep + n_vot + n_san + n_int + n_com + n_pro + n_mot + n_oz + n_dcl + n_stn + n_dc
    print(f"\nTotal: {total} pagini HTML generate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
