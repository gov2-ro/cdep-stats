"""Test integration: parser proiecte legislative pe fixture HTML real.

Folosește `tests/fixtures/proiect_22201.html` (Bugetul de stat 2025) ca să
testeze că `parse_detail` extrage toate câmpurile-cheie corect — fără request HTTP.

Acest test prinde regresii dacă cdep.ro schimbă HTML-ul.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FIXTURE = Path(__file__).parent / "fixtures" / "proiect_22201.html"


class _FakeResponse:
    """Minimal stand-in pentru `requests.Response`."""

    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        pass


def test_parse_detail_buget_2025() -> None:
    """Bugetul de stat 2025 (idp=22201) trebuie să producă toate câmpurile."""
    from scrapers.proiecte import parse_detail

    html = FIXTURE.read_text(encoding="utf-8")

    with patch("scrapers.proiecte.get", return_value=_FakeResponse(html)):
        p = parse_detail(idp=22201, legislatura=2024, cam=2)

    assert p is not None

    # === Câmpuri de identificare ===
    assert p.cdep_idp == 22201
    assert p.cam == 2
    assert p.legislatura == 2024
    assert p.id  # hash stabil non-empty

    # === Numere de înregistrare ===
    assert p.nr_inregistrare == "PL-x nr. 1/2025"
    assert p.nr_camera_deputati == "1/01.02.2025"
    assert p.nr_senat == "L13/2025"
    assert p.nr_guvern == "E13/01.02.2025"
    assert p.nr_bpi == "3/01-02-2025"

    # === Conținut ===
    assert p.titlu == "Proiectul Legii bugetului de stat pe anul 2025"
    assert p.tip.value == "proiect_lege"
    assert p.caracter.value == "ordinar"
    assert p.procedura_urgenta is True
    assert p.initiator == "Guvern"
    assert p.camera_decizionala and "Camera Deputa" in p.camera_decizionala

    # === Stadiu și promulgare ===
    assert p.stadiu and "Lege 9/2025" in p.stadiu
    assert p.lege_nr == "9/2025"
    assert p.decret_nr == "59/2025"

    # === Date cheie din timeline ===
    assert str(p.data_prezentare) == "2025-02-01"
    assert str(p.data_inregistrare_cd) == "2025-02-01"
    assert str(p.data_promulgare) == "2025-02-10"
    # Ședința comună acoperă ambele Camere
    assert str(p.data_adoptare_cd) == "2025-02-05"
    assert str(p.data_adoptare_senat) == "2025-02-05"

    # === Vot final ===
    assert p.vot_pentru == 254
    assert p.vot_contra == 192
    assert p.vot_abtineri == 0

    # === Timeline ===
    assert len(p.timeline) >= 5  # cel puțin 5 evenimente
    # Primul eveniment: prezentare
    assert p.timeline[0].data is not None
    assert "prezentare" in p.timeline[0].eveniment.lower()

    # === PDF documents ===
    assert len(p.documente_pdf) >= 5
    for url in p.documente_pdf:
        url_str = str(url)
        assert url_str.startswith("https://")
        assert url_str.endswith(".pdf")


def test_parse_detail_handles_missing_fixture() -> None:
    """Fixture-ul trebuie să existe — sanity check pentru CI."""
    assert FIXTURE.exists(), f"Fixture lipsă: {FIXTURE}"
    assert FIXTURE.stat().st_size > 10_000, "Fixture pare incomplet"
