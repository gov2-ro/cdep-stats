"""Construiește feed-urile Atom + JSON Feed peste toate endpoint-urile.

Agregă ultimele 50 de evenimente din voturi, proiecte, interpelări, sancțiuni —
sortate descrescător după dată.

Output:
- `data/v1/feed.atom`  (RFC 4287, standard Atom)
- `data/v1/feed.json`  (JSON Feed v1.1, https://www.jsonfeed.org)

Util pentru jurnaliști: abonare RSS în Feedly / Inoreader / NetNewsWire.

Utilizare:
    python scripts/build_feeds.py
    python scripts/build_feeds.py --leg 2024 --limit 100
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BUILDER_VERSION = "0.1.0"
BASE_URL = "https://endimion2k.github.io/cdep-api-poc"


def _to_datetime(s: str | None) -> datetime | None:
    """Parsează ISO 8601 / YYYY-MM-DD în datetime UTC."""
    if not s:
        return None
    s = s.strip()
    try:
        if "T" in s:
            # ISO 8601 cu time
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(UTC)
        # Doar dată — folosesc miezul nopții
        d = datetime.strptime(s[:10], "%Y-%m-%d")
        return d.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return None


def collect_events(leg: int) -> list[dict]:
    """Colectează evenimente din toate sursele JSON existente."""
    events: list[dict] = []
    data_dir = ROOT / "data" / "v1"

    # 1. Voturi — ultimele din _index.json
    voturi_idx = data_dir / "voturi" / str(leg) / "_index.json"
    if voturi_idx.exists():
        idx = json.loads(voturi_idx.read_text(encoding="utf-8"))
        for v in idx.get("data", []):
            ts = _to_datetime(v.get("timestamp"))
            if not ts:
                continue
            counts = v.get("counts", {})
            adoptat = counts.get("pentru", 0) > counts.get("contra", 0)
            events.append(
                {
                    "timestamp": ts,
                    "tip": "vot",
                    "id": f"vot-{v['cdep_idv']}",
                    "title": f"Vot: {v.get('descriere', '(fără descriere)')[:120]}",
                    "summary": (
                        f"Pentru: {counts.get('pentru', 0)} · "
                        f"Contra: {counts.get('contra', 0)} · "
                        f"Abțineri: {counts.get('abtineri', 0)} · "
                        f"{'adoptat' if adoptat else 'respins'}"
                    ),
                    "url": f"{BASE_URL}/data/v1/voturi/{leg}/{v['cdep_idv']}.json",
                }
            )

    # 2. Proiecte legislative — ultima dată semnificativă (promulgare > adoptare CD > prezentare)
    proiecte_f = data_dir / "proiecte" / f"legislatura-{leg}.json"
    if proiecte_f.exists():
        proiecte = json.loads(proiecte_f.read_text(encoding="utf-8")).get("data", [])
        for p in proiecte:
            for date_field, suffix in [
                ("data_promulgare", "promulgat"),
                ("data_adoptare_cd", "adoptat de Camera Deputaților"),
                ("data_inregistrare_cd", "înregistrat la Camera Deputaților"),
                ("data_prezentare", "prezentat"),
            ]:
                ts = _to_datetime(p.get(date_field))
                if ts:
                    initiator = p.get("initiator") or "?"
                    stadiu = (p.get("stadiu") or "?")[:80]
                    events.append(
                        {
                            "timestamp": ts,
                            "tip": "proiect",
                            "id": f"proiect-{p['cdep_idp']}-{date_field}",
                            "title": f"Proiect {suffix}: {(p.get('titlu') or '')[:120]}",
                            "summary": (
                                f"{p.get('nr_inregistrare') or ''} · "
                                f"Inițiator: {initiator} · "
                                f"Stadiu: {stadiu}"
                            ),
                            "url": p.get("source_url")
                            or f"{BASE_URL}/data/v1/proiecte/legislatura-{leg}.json",
                        }
                    )
                    break  # un singur eveniment per proiect

    # 3. Interpelări recente
    interpelari_f = data_dir / "interpelari" / f"legislatura-{leg}.json"
    if interpelari_f.exists():
        interpelari = json.loads(interpelari_f.read_text(encoding="utf-8")).get("data", [])
        for i in interpelari:
            ts = _to_datetime(i.get("data_inregistrare"))
            if not ts:
                continue
            adresant = i.get("adresant_nume") or "?"
            destinatar = (i.get("destinatar") or "?")[:80]
            events.append(
                {
                    "timestamp": ts,
                    "tip": "interpelare",
                    "id": f"interpelare-{i['cdep_idi']}",
                    "title": f"Interpelare: {(i.get('titlu') or '')[:120]}",
                    "summary": (
                        f"Adresant: {adresant} · "
                        f"Destinatar: {destinatar} · "
                        f"Răspuns: {'primit' if i.get('raspuns_primit') else 'nu'}"
                    ),
                    "url": i.get("source_url")
                    or f"{BASE_URL}/data/v1/interpelari/legislatura-{leg}.json",
                }
            )

    # 4. Sancțiuni
    sanctiuni_f = data_dir / "sanctiuni" / f"legislatura-{leg}.json"
    if sanctiuni_f.exists():
        sanctiuni = json.loads(sanctiuni_f.read_text(encoding="utf-8")).get("data", [])
        for s in sanctiuni:
            ts = _to_datetime(s.get("data"))
            if not ts:
                continue
            deputat = s.get("deputat_nume") or "?"
            tip_s = s.get("tip") or "?"
            events.append(
                {
                    "timestamp": ts,
                    "tip": "sanctiune",
                    "id": f"sanctiune-{s['id']}",
                    "title": f"Sancțiune: {deputat} ({tip_s})",
                    "summary": (s.get("descriere") or "")[:300],
                    "url": f"{BASE_URL}/data/v1/sanctiuni/legislatura-{leg}.json",
                }
            )

    # Sortare descrescătoare după timestamp
    events.sort(key=lambda e: e["timestamp"], reverse=True)
    return events


def to_atom(events: list[dict], leg: int) -> str:
    """Generează feed Atom (RFC 4287)."""
    now_iso = datetime.now(UTC).isoformat()
    feed_id = f"{BASE_URL}/data/v1/feed.atom"
    items_xml = []
    for e in events:
        items_xml.append(
            f"""  <entry>
    <id>{escape(BASE_URL)}/feed#{escape(e["id"])}</id>
    <title>{escape(e["title"])}</title>
    <updated>{e["timestamp"].isoformat()}</updated>
    <published>{e["timestamp"].isoformat()}</published>
    <link rel="alternate" href="{escape(e["url"])}"/>
    <category term="{escape(e["tip"])}"/>
    <summary>{escape(e["summary"])}</summary>
  </entry>"""
        )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <id>{feed_id}</id>
  <title>Camera Deputaților — flux date deschise (legislatura {leg})</title>
  <subtitle>Voturi, proiecte legislative, interpelări, sancțiuni — actualizat zilnic.</subtitle>
  <updated>{now_iso}</updated>
  <link rel="self" href="{feed_id}" type="application/atom+xml"/>
  <link rel="alternate" href="{BASE_URL}/" type="text/html"/>
  <author>
    <name>cdep-api-poc</name>
    <uri>{BASE_URL}</uri>
  </author>
  <generator uri="{BASE_URL}" version="{BUILDER_VERSION}">cdep-api-poc feed builder</generator>
  <rights>Open Government License v3.0</rights>
{chr(10).join(items_xml)}
</feed>
"""


def to_json_feed(events: list[dict], leg: int) -> dict:
    """Generează JSON Feed v1.1 (https://www.jsonfeed.org/version/1.1/)."""
    return {
        "version": "https://jsonfeed.org/version/1.1",
        "title": f"Camera Deputaților — flux date deschise (legislatura {leg})",
        "home_page_url": BASE_URL,
        "feed_url": f"{BASE_URL}/data/v1/feed.json",
        "description": "Voturi, proiecte legislative, interpelări, sancțiuni — actualizat zilnic.",
        "language": "ro",
        "authors": [{"name": "cdep-api-poc", "url": BASE_URL}],
        "items": [
            {
                "id": f"{BASE_URL}/feed#{e['id']}",
                "url": e["url"],
                "title": e["title"],
                "summary": e["summary"],
                "date_published": e["timestamp"].isoformat(),
                "tags": [e["tip"]],
            }
            for e in events
        ],
    }


def balance_per_type(events: list[dict], max_per_type: int) -> list[dict]:
    """Returnează top `max_per_type` evenimente per tip, apoi sortat global descrescător."""
    from collections import defaultdict

    by_tip: dict[str, list[dict]] = defaultdict(list)
    for e in events:
        by_tip[e["tip"]].append(e)
    balanced: list[dict] = []
    for items in by_tip.values():
        # `items` e deja sortat descrescător (events e sortat global)
        balanced.extend(items[:max_per_type])
    balanced.sort(key=lambda e: e["timestamp"], reverse=True)
    return balanced


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--leg", type=int, default=2024, help="Legislatură (default: 2024)")
    parser.add_argument(
        "--limit", type=int, default=60, help="Număr maxim total items (default: 60)"
    )
    parser.add_argument(
        "--per-type",
        type=int,
        default=15,
        help="Max items per tip (default: 15) — asigură reprezentare echilibrată",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    print(f"Colectez evenimente din legislatura {args.leg}...")
    events = collect_events(args.leg)
    print(f"  {len(events)} evenimente totale găsite")

    # Balansare per tip ca toate cele 4 tipuri să apară în feed
    events = balance_per_type(events, args.per_type)
    events = events[: args.limit]
    print(f"  păstrăm {len(events)} (max {args.per_type} per tip, total {args.limit})")

    out_dir = ROOT / "data" / "v1"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Atom
    atom_xml = to_atom(events, args.leg)
    atom_path = out_dir / "feed.atom"
    atom_path.write_text(atom_xml, encoding="utf-8")
    print(f"  → {atom_path} ({atom_path.stat().st_size:,} bytes)")

    # JSON Feed
    jf = to_json_feed(events, args.leg)
    jf_path = out_dir / "feed.json"
    jf_path.write_text(json.dumps(jf, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  → {jf_path} ({jf_path.stat().st_size:,} bytes)")

    # Stats per tip
    from collections import Counter

    tipuri = Counter(e["tip"] for e in events)
    print("\nDistribuție pe tip:")
    for t, n in tipuri.most_common():
        print(f"  {t}: {n}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
