from __future__ import annotations

import re
from typing import TypedDict


class PartyHistoryEntry(TypedDict):
    short: str
    label: str
    from_date: str | None
    until_date: str | None
    current: bool


PARTY_MAPPING = {
    "social democrat": "PSD",
    "national liberal": "PNL",
    "salvati romania": "USR",
    "unirea romanilor": "AUR",
    " aur": "AUR",  # Direct match in group names
    "aur ": "AUR",
    "democrata maghiara": "UDMR",
    "sos": "SOS",
    "s.o.s": "SOS",
    "oamenilor tineri": "POT",
    " pot": "POT",  # Direct match
    "pot ": "POT",
    "deputati neafiliat": "Neafiliat",  # "Deputaţi neafiliaţi"
    "neafiliat": "Neafiliat",
    "minoritat": "Minorități",
}


def normalize_ro(text: str) -> str:
    """Remove diacritics for matching."""
    replacements = {
        "ă": "a", "â": "a", "î": "i", "ț": "t", "ţ": "t", "ş": "s",
        "Ă": "A", "Â": "A", "Î": "I", "Ț": "T", "Ţ": "T", "Ş": "S",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.lower()


def get_party_short(label: str) -> str:
    """Map group/party label to short code."""
    normalized = normalize_ro(label)
    for key, short in PARTY_MAPPING.items():
        if key in normalized:
            return short
    # Fallback
    return "Altul"


def parse_group_history(text: str | None) -> list[PartyHistoryEntry]:
    """Parse parliamentary group history string into structured entries.

    Input: "Grupul parlamentar SOS România - membru până în feb. 2025 Deputaţi neafiliaţi - membru din feb. 2025..."

    Output: List of PartyHistoryEntry dicts with short, label, from_date, until_date, current.
    """
    if not text or not text.strip():
        return []

    entries: list[PartyHistoryEntry] = []

    # Split on segment boundaries: "Grupul parlamentar" or "Deputaţi"
    # Use lookahead to keep the keyword
    segments = re.split(r'(?=Grupul parlamentar|Deputaţi\s)', text)

    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue

        # Extract from_date: "din {date}" where date is like "feb. 2025" or "2025"
        from_match = re.search(r'din\s+([\w\.\s]+?\d{4})', seg)
        from_date = from_match.group(1).strip() if from_match else None

        # Extract until_date: "până în {date}"
        until_match = re.search(r'până\s+în\s+([\w\.\s]+?\d{4})', seg)
        until_date = until_match.group(1).strip() if until_match else None

        # Extract label: everything up to the first date-related dash or function word
        # Remove trailing date info, keep just the party/group name
        if seg.startswith("Grupul parlamentar"):
            # Extract everything after "Grupul parlamentar" until we hit a date or "afiliat"
            label_match = re.match(r'Grupul parlamentar\s+(.+?)(?:\s*-\s*(?:membru|afiliat)|$)', seg)
            if label_match:
                label = f"Grupul parlamentar {label_match.group(1).strip()}"
            else:
                label = seg.split('-')[0].strip()
        elif seg.startswith("Deputaţi"):
            label = "Deputaţi neafiliaţi"
        else:
            label = seg.split('-')[0].strip()

        # Get short code
        short = get_party_short(label)

        # Flag current: is this the last segment and has no until_date?
        is_last = (seg == segments[-1])
        is_current = is_last and until_date is None

        entries.append({
            "short": short,
            "label": label,
            "from_date": from_date,
            "until_date": until_date,
            "current": is_current,
        })

    # Mark the last entry as current if it has no until_date
    if entries and entries[-1]["until_date"] is None:
        entries[-1]["current"] = True

    return entries
