"""Teste unitare pentru funcțiile-helper din scrapere și scripturi.

Aceste teste NU fac request-uri HTTP — testează pur logica de parsing.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _import_module(path: str, name: str):
    """Helper pentru a importa un modul după path absolut."""
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ============================================================
# Date parsing helpers (din scrapers/proiecte.py și interpelari.py)
# ============================================================


class TestParseIsoDate:
    def setup_method(self) -> None:
        from scrapers.proiecte import _parse_iso_date

        self.parse = _parse_iso_date

    def test_dotted_format(self) -> None:
        assert self.parse("01.02.2025") == date(2025, 2, 1)

    def test_dashed_format(self) -> None:
        assert self.parse("3-01-2025") == date(2025, 1, 3)

    def test_with_whitespace(self) -> None:
        assert self.parse("  10.05.2024  ") == date(2024, 5, 10)

    def test_invalid_returns_none(self) -> None:
        assert self.parse("nu e dată") is None
        assert self.parse("") is None
        assert self.parse(None) is None

    def test_invalid_day_returns_none(self) -> None:
        # 32 februarie nu există
        assert self.parse("32.02.2025") is None


# ============================================================
# Canonical ID generation (cross-scraper consistency)
# ============================================================


class TestCanonicalId:
    def test_voturi_voter_canonical_id_matches_interpelari(self) -> None:
        """Cross-scraper: același nume → același canonical_id."""
        from scrapers.interpelari import _voter_canonical_id as int_id
        from scrapers.voturi import _voter_canonical_id as vot_id

        nume = "Marcel Ciolacu"
        assert int_id(nume) == vot_id(nume)

    def test_diacritics_normalized(self) -> None:
        """Diacriticele nu produc ID-uri diferite."""
        from scrapers.voturi import _voter_canonical_id

        assert _voter_canonical_id("Adomnicăi Mirela") == _voter_canonical_id("Adomnicai Mirela")

    def test_whitespace_normalized(self) -> None:
        from scrapers.voturi import _voter_canonical_id

        assert _voter_canonical_id("Marcel  Ciolacu") == _voter_canonical_id("Marcel Ciolacu")

    def test_case_insensitive(self) -> None:
        from scrapers.voturi import _voter_canonical_id

        assert _voter_canonical_id("MARCEL CIOLACU") == _voter_canonical_id("marcel ciolacu")


# ============================================================
# Normalize grup (din scripts/generate_html.py)
# ============================================================


class TestNormalizeGrup:
    def setup_method(self) -> None:
        gen = _import_module("scripts/generate_html.py", "generate_html")
        self.norm = gen.normalize_grup

    def test_strips_destinatar_artifacts(self) -> None:
        assert self.norm("AUR Destinatar:") == "AUR"
        assert self.norm("AUR Destinatari") == "AUR"

    def test_dedupes_neafiliat_variants(self) -> None:
        # Diacritice diferite trebuie să mapeze la aceeași valoare
        assert self.norm("Neafiliat") == "Neafiliat"
        assert self.norm("Neafiliaţi") == "Neafiliat"
        assert self.norm("Neafiliaţi Destinatari") == "Neafiliat"

    def test_party_full_name_to_abbrev(self) -> None:
        assert self.norm("Partidul Social Democrat") == "PSD"
        assert self.norm("Partidul Naţional Liberal") == "PNL"
        assert self.norm("Uniunea Salvaţi România") == "USR"
        assert self.norm("Alianţa pentru Unirea Românilor") == "AUR"

    def test_sos_variants(self) -> None:
        assert self.norm("SOS RO") == "S.O.S."
        assert self.norm("Partidul S.O.S. România") == "S.O.S."

    def test_minorities(self) -> None:
        assert self.norm("Minoritati nationale") == "Minorități"

    def test_fara_adeziune_treated_as_neaf(self) -> None:
        # Deputatul care a părăsit partidul = Neafiliat
        assert self.norm("PSD - până în iun. 2025 Fără adeziune") == "Neafiliat"

    def test_empty_or_none(self) -> None:
        assert self.norm(None) == "Neafiliat"
        assert self.norm("") == "Neafiliat"


# ============================================================
# Normalize comisii (din scripts/build_comisii.py)
# ============================================================


class TestNormalizeName:
    def setup_method(self) -> None:
        bc = _import_module("scripts/build_comisii.py", "build_comisii")
        self.norm = bc.normalize_name

    def test_strips_alte_comisii_suffix(self) -> None:
        assert self.norm("Comisia X Alte comisii") == "Comisia X"

    def test_strips_temporal_variants(self) -> None:
        base = "Comisia pentru afaceri europene"
        assert self.norm(f"{base} (din feb. 2025)") == base
        assert self.norm(f"{base} (până în sep. 2025)") == base
        assert self.norm(f"{base} (mar. 2025)") == base
        assert self.norm(f"{base} (feb. - sep. 2025)") == base

    def test_preserves_unrelated_parens(self) -> None:
        # Paranteze fără date trebuie păstrate
        nume = "Comisia X (subgrupa A)"
        assert self.norm(nume) == nume

    def test_collapses_whitespace(self) -> None:
        assert self.norm("Comisia    X    Y") == "Comisia X Y"


# ============================================================
# Detect tip / caracter (din scrapers/proiecte.py)
# ============================================================


class TestDetectTip:
    def test_proiect_lege(self) -> None:
        from schemas.proiect import TipInitiativa
        from scrapers.proiecte import _detect_tip

        assert _detect_tip("Proiectul Legii bugetului") == TipInitiativa.PROIECT_LEGE

    def test_propunere_legislativa(self) -> None:
        from schemas.proiect import TipInitiativa
        from scrapers.proiecte import _detect_tip

        assert (
            _detect_tip("Propunere legislativă pentru ...") == TipInitiativa.PROPUNERE_LEGISLATIVA
        )

    def test_oug(self) -> None:
        from schemas.proiect import TipInitiativa
        from scrapers.proiecte import _detect_tip

        assert _detect_tip("OUG 144/2024") == TipInitiativa.OUG


class TestDetectCaracter:
    def test_ordinar(self) -> None:
        from schemas.proiect import CaracterProiect
        from scrapers.proiecte import _detect_caracter

        assert _detect_caracter("ordinar") == CaracterProiect.ORDINAR

    def test_organic(self) -> None:
        from schemas.proiect import CaracterProiect
        from scrapers.proiecte import _detect_caracter

        assert _detect_caracter("organic") == CaracterProiect.ORGANIC


# ============================================================
# Lookup câmpuri (case+diacritics-insensitive, din proiecte.py)
# ============================================================


class TestLookup:
    def test_exact_match(self) -> None:
        from scrapers.proiecte import _lookup

        fields = {"Camera Deputaţilor": "1/01.02.2025"}
        assert _lookup(fields, "Camera Deputaţilor") == "1/01.02.2025"

    def test_diacritics_insensitive(self) -> None:
        from scrapers.proiecte import _lookup

        fields = {"Camera Deputaţilor": "1/01.02.2025"}
        # Cere fără diacritice → găsește
        assert _lookup(fields, "Camera Deputatilor") == "1/01.02.2025"
        # Cere cu altă variantă de diacritic → găsește
        assert _lookup(fields, "Camera Deputaților") == "1/01.02.2025"

    def test_case_insensitive(self) -> None:
        from scrapers.proiecte import _lookup

        fields = {"INITIATOR": "Guvern"}
        assert _lookup(fields, "Initiator") == "Guvern"

    def test_multiple_candidates(self) -> None:
        from scrapers.proiecte import _lookup

        fields = {"Iniţiator": "Guvern"}
        # Niciuna dintre primele variante nu match → caută în continuare
        assert _lookup(fields, "X", "Y", "Initiator") == "Guvern"

    def test_missing_returns_none(self) -> None:
        from scrapers.proiecte import _lookup

        assert _lookup({}, "X") is None


# ============================================================
# Slug (din scripts/build_comisii.py)
# ============================================================


class TestSlug:
    def setup_method(self) -> None:
        bc = _import_module("scripts/build_comisii.py", "build_comisii")
        self.slug = bc.slug

    def test_strips_diacritics(self) -> None:
        assert self.slug("Comisia pentru afaceri europene") == "comisia-pentru-afaceri-europene"

    def test_strips_special_chars(self) -> None:
        assert self.slug("Comisia juridică, de disciplină şi imunităţi").startswith(
            "comisia-juridica-de-disciplina"
        )

    def test_max_length(self) -> None:
        long_name = "Comisia " + "foarte " * 20 + "lungă"
        assert len(self.slug(long_name)) <= 60
