"""Unit tests for parsers/interese_pdf.py — synthetic text, no PDF files required."""

from __future__ import annotations

import pytest

from parsers.interese_pdf import (
    _parse_companii,
    _parse_conducere,
    _parse_asociatii_profesionale,
    _parse_partide,
    _parse_contracte,
)

# ── Synthetic section text ────────────────────────────────────────────────────

SEC1_BASIC = """1. Asociat sau acţionar la societăţi comerciale...
1.1 MAXIMUS GENERAL SERVICES srl -
Sectorul 5 Bucuresti STR. RITORIDE, NR. Asociat 50 Părţi sociale 200 RON
14, IMOBIL LOTUL 2/2, AP. 8
1.2 MAXIMUS FOTOVOLTAIC ENERGY -
Buzau Buzau CART. BROSTENI, BL. P11, Asociat 100 Părţi sociale 500 RON
AP. 4
"""

SEC1_ACTIONAR = """1. Asociat sau acţionar la societăţi comerciale...
1.1 Team Asir Med agent de
asigurare SRL - Medgidia Constanta Acţionar 30 Părţi sociale 300 RON
Dobrotici 11 bloc C1 camera 1
1.2 IONEK SRL - Constanta Constanta
Prelungirea 8 martie,nr 10, lot 2, cam Acţionar 20 Părţi sociale 200 RON
"""

SEC1_EMPTY = """1. Asociat sau acţionar la societăţi comerciale...
- - - -
"""

SEC2_BASIC = """2. Calitatea de membru în organele de conducere...
1.1 MAXIMUS GENERAL SERVICES -
Sectorul 5 Bucuresti str RITORIDE, Administrator 0 RON
NR. 14, IMOBILUL LOTUL 2/2, AP.8
1.2 Federația Părinților și Aparținătorilor Legali -
Sector 1 Bucuresti Preşedinte 0 RON
"""

SEC2_EMPTY = """2. Calitatea de membru în organele de conducere...
- - -
"""

SEC3_WITH_CONTENT = """3. Calitatea de membru în cadrul asociaţiilor profesionale şi/sau sindicale
Ordinul Arhitecților din România - membru
"""

SEC3_EMPTY = """3. Calitatea de membru în cadrul asociaţiilor profesionale şi/sau sindicale
-
"""

SEC4_BASIC = """4. Calitatea de membru în organele de conducere...retribuite...
4.1 Partidul Național Liberal Filiala Cluj - Vicepreședinte
4.2 UNPR Filiala Sector 3 - Secretar
"""

SEC4_EMPTY = """4. Calitatea de membru în organele de conducere...retribuite...
4.1 - - -
"""

SEC4_SINGLE = """4. Calitatea de membru în organele de conducere...retribuite...
4.1 AUR FILIALA GIURGIU - PRIMVICEPRESEDINTE
"""

SEC5_WITH_CONTRACTS = """5. Contracte...
5.1 Beneficiarul
Soţ/soţie
SC EURO INVEST SRL COMPANIA NATIONALA LICITATIE CONTRACT DE 11.11.2021 3757804.94 RON
36 LUNI
DE INVESTITII PUBLICA LUCRARI
Gogosari - Giurgiu
Rude de gradul I
- - - - - - -
Societăţi comerciale
- - - - - - -
"""

SEC5_EMPTY = """5. Contracte...
5.1 Beneficiarul
Titular
- - - - - - -
Soţ/soţie
- - - - - - -
Rude de gradul I
- - - - - - -
Societăţi comerciale
- - - - - - -
"""

FULL_TEXT_EMPTY = """4576281
DECLARAŢIE DE INTERESE
30 de zile de la numire
Subsemnatul Test I. Deputat, având funcţia de Deputat la Camera Deputatilor, CNP
* ************
1. Asociat sau acţionar la societăţi comerciale, companii/societăţi naţionale, instituţii de credit,
grupuri de interes economic, precum şi membru în asociaţii, fundaţii sau alte organizaţii
neguvernamentale:
- - - -
2. Calitatea de membru în organele de conducere, administrare şi control ale societăţilor
comerciale, ale companiilor/societăţilor naţionale, ale instituţiilor de credit, ale grupurilor de
interes economic, ale asociaţiilor sau fundaţiilor ori ale altor organizaţii neguvernamentale:
- - -
3. Calitatea de membru în cadrul asociaţiilor profesionale şi/sau sindicale
-
4. Calitatea de membru în organele de conducere, administrare şi control, retribuite sau
neretribuite, deţinute în cadrul partidelor politice, funcţia deţinută şi denumirea partidului
politic
4.1 - - -
5. Contracte, inclusiv cele de asistenţă juridică...
5.1 Beneficiarul
Titular
- - - - - - -
Soţ/soţie
- - - - - - -
Rude de gradul I ale titularului
- - - - - - -
Societăţi comerciale
- - - - - - -
Prezenta declaraţie constituie act public şi răspund potrivit legii penale
Data completării Semnătura
17-01-2025
"""


# ── §1 tests ──────────────────────────────────────────────────────────────────


def test_parse_companii_basic_count():
    rows = _parse_companii(SEC1_BASIC)
    assert len(rows) == 2


def test_parse_companii_denumire():
    rows = _parse_companii(SEC1_BASIC)
    names = [r["denumire"] for r in rows]
    assert any("MAXIMUS GENERAL SERVICES" in n for n in names)
    assert any("MAXIMUS FOTOVOLTAIC ENERGY" in n for n in names)


def test_parse_companii_calitate():
    rows = _parse_companii(SEC1_BASIC)
    assert all(r["calitate"] == "Asociat" for r in rows)


def test_parse_companii_nr_titluri():
    rows = _parse_companii(SEC1_BASIC)
    nr_vals = {r["nr_titluri"] for r in rows}
    assert 50 in nr_vals
    assert 100 in nr_vals


def test_parse_companii_valoare_ron():
    rows = _parse_companii(SEC1_BASIC)
    valori = {r["valoare_ron"] for r in rows}
    assert 200.0 in valori
    assert 500.0 in valori


def test_parse_companii_actionar():
    rows = _parse_companii(SEC1_ACTIONAR)
    assert len(rows) == 2
    assert all(
        r["calitate"] == "Acţionar"
        or r["calitate"] == "Actionar"
        or "tionar" in r["calitate"].lower()
        for r in rows
    )


def test_parse_companii_empty():
    rows = _parse_companii(SEC1_EMPTY)
    assert rows == []


# ── §2 tests ──────────────────────────────────────────────────────────────────


def test_parse_conducere_count():
    rows = _parse_conducere(SEC2_BASIC)
    assert len(rows) == 2


def test_parse_conducere_denumire():
    rows = _parse_conducere(SEC2_BASIC)
    names = [r["denumire"] for r in rows]
    assert any("MAXIMUS" in n for n in names)
    assert any("Federația" in n or "Federatia" in n for n in names)


def test_parse_conducere_calitate():
    rows = _parse_conducere(SEC2_BASIC)
    calitati = {(r["calitate_conducere"] or "").lower() for r in rows}
    assert "administrator" in calitati
    assert any("edinte" in c for c in calitati)  # matches Pre[şș]edinte


def test_parse_conducere_valoare():
    rows = _parse_conducere(SEC2_BASIC)
    assert all(r["valoare_beneficii_ron"] == 0.0 for r in rows)


def test_parse_conducere_empty():
    rows = _parse_conducere(SEC2_EMPTY)
    assert rows == []


# ── §3 tests ──────────────────────────────────────────────────────────────────


def test_parse_asociatii_with_content():
    result = _parse_asociatii_profesionale(SEC3_WITH_CONTENT)
    assert result is not None
    assert "Ordinul Arhitecților" in result or "Ordinul Arhitec" in result


def test_parse_asociatii_empty():
    result = _parse_asociatii_profesionale(SEC3_EMPTY)
    assert result is None


# ── §4 tests ──────────────────────────────────────────────────────────────────


def test_parse_partide_basic_count():
    entries = _parse_partide(SEC4_BASIC)
    assert len(entries) == 2


def test_parse_partide_content():
    entries = _parse_partide(SEC4_BASIC)
    assert any("Vicepreședinte" in e or "Vicepresedinte" in e for e in entries)
    assert any("Secretar" in e for e in entries)


def test_parse_partide_empty():
    entries = _parse_partide(SEC4_EMPTY)
    assert entries == []


def test_parse_partide_single():
    entries = _parse_partide(SEC4_SINGLE)
    assert len(entries) == 1
    assert "AUR" in entries[0]


def test_parse_partide_are_functie_flag():
    assert len(_parse_partide(SEC4_BASIC)) > 0
    assert len(_parse_partide(SEC4_EMPTY)) == 0


# ── §5 tests ──────────────────────────────────────────────────────────────────


def test_parse_contracte_empty():
    rows = _parse_contracte(SEC5_EMPTY)
    assert rows == []


def test_parse_contracte_detects_sot_sotie():
    rows = _parse_contracte(SEC5_WITH_CONTRACTS)
    assert any(r["beneficiar_tip"] == "sot_sotie" for r in rows)


def test_parse_contracte_valoare_ron():
    rows = _parse_contracte(SEC5_WITH_CONTRACTS)
    sot_rows = [r for r in rows if r["beneficiar_tip"] == "sot_sotie"]
    assert len(sot_rows) > 0
    assert sot_rows[0]["valoare_ron"] == pytest.approx(3757804.94, rel=0.01)


def test_parse_contracte_tip_contract():
    rows = _parse_contracte(SEC5_WITH_CONTRACTS)
    tips = {r["tip_contract"] for r in rows if r.get("tip_contract")}
    assert "lucrari" in tips


def test_parse_contracte_total_ron():
    rows = _parse_contracte(SEC5_WITH_CONTRACTS)
    total = sum(r["valoare_ron"] for r in rows if r.get("valoare_ron"))
    assert total == pytest.approx(3757804.94, rel=0.01)


# ── Full parse_pdf (synthetic text, mocking pdfplumber) ──────────────────────


class _FakePDF:
    def __init__(self, text: str):
        self._text = text

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @property
    def pages(self):
        class _Page:
            def __init__(self, t):
                self._t = t

            def extract_text(self):
                return self._t

        return [_Page(self._text)]


def test_parse_pdf_full_empty(monkeypatch, tmp_path):
    """A declaration with all sections empty should parse cleanly with zero counts."""
    import parsers.interese_pdf as mod
    from parsers.interese_pdf import parse_pdf

    fake_pdf_path = tmp_path / "test.pdf"
    fake_pdf_path.write_bytes(b"fake")

    def fake_open(path):
        return _FakePDF(FULL_TEXT_EMPTY)

    monkeypatch.setattr(mod.pdfplumber, "open", fake_open)

    result = parse_pdf(fake_pdf_path)

    assert result["text_extracted"] is True
    assert result["error"] is None
    assert result["ani_id"] == "4576281"
    assert result["tip_declaratie"] == "numire"
    assert result["nr_companii"] == 0
    assert result["companii"] == []
    assert result["conducere"] == []
    assert result["partide_raw"] == []
    assert result["are_functie_partid"] is False
    assert result["contracte"] == []
    assert result["are_contracte_publice"] is False
    assert result["contracte_total_ron"] == 0.0
