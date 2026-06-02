"""Unit tests for scrapers/entities_ordine_zi.py."""

from __future__ import annotations

from datetime import date

import pytest

from scrapers.entities_ordine_zi import (
    extract_action,
    extract_commissions,
    extract_entities,
    extract_flags,
    extract_initiator,
    extract_institutions,
    extract_item_type,
    extract_law_category,
    extract_referenced_acts,
    extract_senate_date,
    extract_subject,
)


# ---------------------------------------------------------------------------
# extract_item_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Proiectul de Lege privind aprobarea...", "proiect_lege"),
        ("Proiectul de Hotărâre privind...", "proiect_hotarare"),
        # old-style diacritics (ţ/ş)
        ("Propunerea legislativă pentru modificarea...", "propunere_legislativa"),
        ("Reexaminarea Legii privind...", "reexaminare"),
        ("Dezbaterea moţiunii simple iniţiate de 86 de deputaţi (MS 7/2025).", "motiune_simpla"),
        ("Dezbaterea şi votul asupra moţiunii de cenzură iniţiate de 155...", "motiune_cenzura"),
        ("Informare privind distribuirea unor documente la casetele deputaţilor...", "informare_casete"),
        ("Informare din partea domnului Klaus...", "informare"),
        ("Declaraţia Parlamentului României cu ocazia...", "declaratie"),
        ("Dezbateri politice, cu participarea...", "dezbateri_politice"),
        ("Raportul privind execuţia bugetului...", "raport"),
        ("Solicitarea comună a Comisiei pentru industrii...", "solicitare"),
        ("Vacantarea unei funcţii de consilier...", "vacantare"),
        ("Prezentarea unor alocuţiuni din partea...", "alocutiuni"),
        ("Păstrarea unui moment de reculegere...", "moment_reculegere"),
        ("Ceva complet nerecunoscut", None),
    ],
)
def test_extract_item_type(text: str, expected: str | None) -> None:
    assert extract_item_type(text) == expected


# ---------------------------------------------------------------------------
# extract_action
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, item_type, expected",
    [
        (
            "Proiectul de Lege privind aprobarea Ordonanţei de urgenţă a Guvernului nr.38/2025...",
            "proiect_lege",
            "aprobare_oug",
        ),
        (
            "Proiectul de Lege privind aprobarea Ordonanţei Guvernului nr.26/2024...",
            "proiect_lege",
            "aprobare_og",
        ),
        (
            "Proiectul de Lege pentru modificarea şi completarea Legii nr.24/2017...",
            "proiect_lege",
            "modificare_si_completare",
        ),
        (
            "Proiectul de Lege pentru modificarea art.32 din Legea nr.273/2006...",
            "proiect_lege",
            "modificare",
        ),
        (
            "Proiectul de Lege pentru completarea Legii nr.165/2018...",
            "proiect_lege",
            "completare",
        ),
        (
            "Proiectul de Hotărâre privind modificarea anexei la Hotărârea nr.111/2024...",
            "proiect_hotarare",
            "modificare_anexa",
        ),
        (
            "Proiectul de Lege privind abilitarea Guvernului de a emite ordonanţe...",
            "proiect_lege",
            "abilitare",
        ),
        (
            "Proiectul de Hotărâre privind aprobarea componentei nominale a comisiilor...",
            "proiect_hotarare",
            "aprobare_componenta",
        ),
        (
            "Proiectul de Hotărâre privind constituirea Comisiei speciale...",
            "proiect_hotarare",
            "constituire",
        ),
        (
            "Proiectul de Hotărâre privind revocarea din funcţie...",
            "proiect_hotarare",
            "revocare",
        ),
    ],
)
def test_extract_action(text: str, item_type: str, expected: str) -> None:
    assert extract_action(text, item_type) == expected


# ---------------------------------------------------------------------------
# extract_law_category
# ---------------------------------------------------------------------------


def test_law_category_organica() -> None:
    html = '(PL-x 318/2025) - <b>lege organică </b>-<i>Adoptat de Senat</i>'
    assert extract_law_category(html) == "lege_organica"


def test_law_category_ordinara() -> None:
    html = '(PL-x 569/2024) - <b>lege ordinară </b>-<i>Adoptat de Senat</i>'
    assert extract_law_category(html) == "lege_ordinara"


def test_law_category_none_for_hotarare() -> None:
    html = "Proiectul de Hotărâre privind modificarea anexei..."
    assert extract_law_category(html) is None


def test_law_category_old_diacritics() -> None:
    # ţ instead of ț in "organică" — should still match
    html = "<b>lege organică</b>"
    assert extract_law_category(html) == "lege_organica"


# ---------------------------------------------------------------------------
# extract_flags
# ---------------------------------------------------------------------------


def test_flags_multiple() -> None:
    text = "Procedură de urgenţă\nCameră decizională\nPrioritate legislativă\nSe dezbate sub rezerva depunerii raportului"
    flags = extract_flags(text)
    assert "procedura_urgenta" in flags
    assert "camera_decizionala" in flags
    assert "prioritate_legislativa" in flags
    assert "rezerva_raport" in flags


def test_flags_vot_secret() -> None:
    text = "Vot secret cu bile (prezenţă fizică) - La finalizarea ordinii de zi."
    assert "vot_secret_bile" in extract_flags(text)


def test_flags_vot_deschis() -> None:
    text = "Vot deschis electronic la distanţă (prezenţă fizică şi online)"
    assert "vot_deschis_electronic" in extract_flags(text)


def test_flags_art115() -> None:
    text = "Adoptat de Senat în condiţiile articolului 115 alineatul (5)"
    assert "adoptat_art115" in extract_flags(text)


def test_flags_empty() -> None:
    text = "Informare privind distribuirea unor documente la casete."
    assert extract_flags(text) == []


# ---------------------------------------------------------------------------
# extract_senate_date
# ---------------------------------------------------------------------------


def test_senate_date_found() -> None:
    text = "lege organică -Adoptat de Senat -07.10.2024\nRaport comun..."
    assert extract_senate_date(text) == date(2024, 10, 7)


def test_senate_date_with_space() -> None:
    text = "Adoptat de Senat - 26.06.2023"
    assert extract_senate_date(text) == date(2023, 6, 26)


def test_senate_date_none() -> None:
    text = "Proiectul de Hotărâre privind modificarea anexei..."
    assert extract_senate_date(text) is None


# ---------------------------------------------------------------------------
# extract_referenced_acts
# ---------------------------------------------------------------------------


def test_referenced_acts_oug() -> None:
    text = "privind aprobarea Ordonanţei de urgenţă a Guvernului nr.38/2025 pentru modificarea"
    acts = extract_referenced_acts(text)
    assert len(acts) == 1
    assert acts[0].act_type == "OUG"
    assert acts[0].nr == "38"
    assert acts[0].year == 2025


def test_referenced_acts_lege() -> None:
    text = "pentru modificarea Legii nr.165/2013 privind măsurile..."
    acts = extract_referenced_acts(text)
    assert any(a.act_type == "Lege" and a.nr == "165" and a.year == 2013 for a in acts)


def test_referenced_acts_multiple() -> None:
    text = (
        "aprobarea Ordonanţei de urgenţă a Guvernului nr.38/2025 "
        "pentru modificarea Legii nr.165/2013"
    )
    acts = extract_referenced_acts(text)
    types = {a.act_type for a in acts}
    assert "OUG" in types
    assert "Lege" in types


def test_referenced_acts_hotarare_parlament() -> None:
    text = "Hotărârea Parlamentului României nr.5/2025 privind constituirea"
    acts = extract_referenced_acts(text)
    assert any(a.act_type == "HotarareParlament" and a.nr == "5" for a in acts)


def test_referenced_acts_ccr() -> None:
    text = "ca urmare a Deciziei Curţii Constituţionale nr.676 din 25 noiembrie 2025"
    acts = extract_referenced_acts(text)
    assert any(a.act_type == "CCR" and a.nr == "676" for a in acts)
    ccr = next(a for a in acts if a.act_type == "CCR")
    assert ccr.year is None


def test_referenced_acts_oug_without_guvernului() -> None:
    # "a Guvernului" is optional — cdep.ro sometimes omits it
    text = "modificarea şi completarea Ordonanţei de urgenţă nr.24/2008 privind asistenţa socială"
    acts = extract_referenced_acts(text)
    assert any(a.act_type == "OUG" and a.nr == "24" and a.year == 2008 for a in acts)


def test_referenced_acts_lege_lowercase() -> None:
    text = "pentru completarea legea nr.226/2023 privind X"
    acts = extract_referenced_acts(text)
    assert any(a.act_type == "Lege" and a.nr == "226" and a.year == 2023 for a in acts)


def test_referenced_acts_deduplication() -> None:
    text = "Legii nr.24/2017 ... completarea Legii nr.24/2017"
    acts = extract_referenced_acts(text)
    lege_acts = [a for a in acts if a.act_type == "Lege" and a.nr == "24"]
    assert len(lege_acts) == 1


# ---------------------------------------------------------------------------
# extract_commissions
# ---------------------------------------------------------------------------


def test_commissions_single() -> None:
    text = "Raport -Comisia pentru muncă (Adoptare) - distribuit-12.06.2025"
    comms = extract_commissions(text)
    assert len(comms) == 1
    assert "Comisia pentru muncă" in comms[0]


def test_commissions_multiple_si() -> None:
    text = "Raport comun - Comisia pentru politică economică şi Comisia pentru buget (Adoptare)"
    comms = extract_commissions(text)
    assert len(comms) == 2
    assert any("politică economică" in c for c in comms)
    assert any("buget" in c for c in comms)


def test_commissions_multiple_comma() -> None:
    text = "Raport comun - Comisia pentru industrii, Comisia pentru mediu şi Comisia juridică (Adoptare)"
    comms = extract_commissions(text)
    assert len(comms) == 3


def test_commissions_juridica_with_de() -> None:
    # "Comisia juridică, de disciplină şi imunităţi" is ONE commission
    text = "Raport - Comisia juridică, de disciplină şi imunităţi (Adoptare)"
    comms = extract_commissions(text)
    assert len(comms) == 1
    assert "disciplin" in comms[0]


def test_commissions_none() -> None:
    text = "Informare privind distribuirea unor documente la casete."
    assert extract_commissions(text) == []


# ---------------------------------------------------------------------------
# extract_initiator
# ---------------------------------------------------------------------------


def test_initiator_group() -> None:
    text = 'Dezbateri politice, la solicitarea Grupului parlamentar AUR, cu tema "Dezastrul..."'
    group, count, itype = extract_initiator(text)
    assert group == "AUR"
    assert count is None


def test_initiator_group_with_dash() -> None:
    text = "Păstrarea unui moment de reculegere, la solicitarea Grupului parlamentar S.O.S. - România."
    group, count, itype = extract_initiator(text)
    assert group == "S.O.S. - România"


def test_initiator_deputies_and_senators() -> None:
    text = "Dezbaterea moţiunii de cenzură iniţiate de 155 de deputaţi şi senatori."
    group, count, itype = extract_initiator(text)
    assert group is None
    assert count == 155
    assert itype == "deputati_si_senatori"


def test_initiator_deputies_only() -> None:
    text = "Dezbaterea moţiunii simple iniţiate de 86 de deputaţi (MS 7/2025)."
    group, count, itype = extract_initiator(text)
    assert count == 86
    assert itype == "deputati"


def test_initiator_none() -> None:
    text = "Proiectul de Lege privind aprobarea Ordonanţei de urgenţă..."
    group, count, itype = extract_initiator(text)
    assert group is None
    assert count is None
    assert itype is None


# ---------------------------------------------------------------------------
# extract_subject
# ---------------------------------------------------------------------------


def test_subject_proiect_lege() -> None:
    text = (
        "Proiectul de Lege privind aprobarea Ordonanţei de urgenţă a Guvernului nr.38/2025 "
        "pentru modificarea şi completarea Legii nr.165/2013 privind măsurile pentru "
        "finalizarea procesului de restituire (PL-x 318/2025)"
    )
    subj = extract_subject(text, "proiect_lege")
    assert subj is not None
    assert "(PL-x" not in subj
    assert "aprobarea" not in subj   # verb phrase stripped
    assert "restituire" in subj      # topical term kept


def test_subject_strips_law_category() -> None:
    text = (
        "Proiectul de Lege pentru modificarea şi completarea Legii nr.24/2017 "
        "privind emitenţii de instrumente financiare şi operaţiuni de piaţă "
        "(PL-x 569/2024) - lege ordinară -Adoptat de Senat"
    )
    subj = extract_subject(text, "proiect_lege")
    assert subj is not None
    assert "instrumente financiare" in subj   # topical phrase
    assert "modificarea" not in subj          # verb stripped
    assert "lege ordinară" not in subj
    assert "Adoptat" not in subj


def test_subject_bill_without_privind_clause() -> None:
    # When the descriere is cut short and has no "privind" clause after act nr → None
    text = "Proiectul de Lege pentru modificarea Legii nr.24/2017 (PL-x 569/2024)"
    subj = extract_subject(text, "proiect_lege")
    assert subj is None  # no topic clause available


def test_subject_propunere_legislativa() -> None:
    text = (
        "Propunerea legislativă pentru completarea Legii nr.165/2018 "
        "privind acordarea biletelor de valoare (Pl-x 342/2023)"
    )
    subj = extract_subject(text, "propunere_legislativa")
    assert subj is not None
    assert "acordarea biletelor de valoare" in subj
    assert "completarea" not in subj


def test_subject_oug_without_guvernului() -> None:
    text = (
        "Proiectul de Lege pentru modificarea şi completarea Ordonanţei de urgenţă "
        "nr.24/2008 privind asistenţa socială (PL-x 201/2025)"
    )
    subj = extract_subject(text, "proiect_lege")
    assert subj is not None
    assert "asistenţa socială" in subj or "asistența socială" in subj
    assert "modificarea" not in subj


def test_subject_informare_casete_none() -> None:
    text = "Informare privind distribuirea unor documente la casetele deputaţilor, potrivit art.94..."
    assert extract_subject(text, "informare_casete") is None


def test_subject_hotarare() -> None:
    text = "Proiectul de Hotărâre privind vacantarea unui loc de deputat (PHCD 94/2025)."
    subj = extract_subject(text, "proiect_hotarare")
    assert subj is not None
    assert "vacantarea unui loc de deputat" in subj
    assert "(PHCD" not in subj


# ---------------------------------------------------------------------------
# Integration: extract_entities
# ---------------------------------------------------------------------------


def test_integration_proiect_lege_full() -> None:
    html = (
        "Proiectul de Lege privind aprobarea Ordonanţei de urgenţă a Guvernului nr.57/2023 "
        "pentru stabilirea unor măsuri privind salarizarea personalului din sistemul naţional "
        "de învăţământ de stat (PL-x 464/2023) - <b>lege organică </b>"
        "-<i>Adoptat de Senat -26.06.2023<br>"
        "Raport -Comisia pentru muncă (Adoptare) - distribuit-12.06.2025<br></i>"
        "<b>Procedură de urgenţă<br><i>Cameră decizională\n</i></b>"
    )
    ent = extract_entities(html)
    assert ent.item_type == "proiect_lege"
    assert ent.action == "aprobare_oug"
    assert ent.law_category == "lege_organica"
    assert "procedura_urgenta" in ent.flags
    assert "camera_decizionala" in ent.flags
    assert ent.senate_adoption_date == date(2023, 6, 26)
    assert any(a.act_type == "OUG" and a.nr == "57" and a.year == 2023 for a in ent.referenced_acts)
    assert len(ent.commissions) == 1
    assert "muncă" in ent.commissions[0]
    # subject = topical noun phrase (verb+act stripped)
    assert ent.subject is not None
    assert "salarizarea" in ent.subject
    assert "aprobarea" not in ent.subject  # verb phrase stripped


def test_integration_motiune_cenzura() -> None:
    html = (
        "Dezbaterea moţiunii de cenzură iniţiate de 155 de deputaţi şi senatori.<br>"
        "<br><b>Vot secret cu bile (prezenţă fizică) - La finalizarea ordinii de zi.</b>"
    )
    ent = extract_entities(html)
    assert ent.item_type == "motiune_cenzura"
    assert ent.initiator_count == 155
    assert ent.initiator_type == "deputati_si_senatori"
    assert "vot_secret_bile" in ent.flags


def test_integration_hotarare_modificare_anexa() -> None:
    html = (
        "Proiectul de Hotărâre pentru modificarea anexei la Hotărârea Parlamentului României "
        "nr.5/2025 privind constituirea Comisiei speciale comune (PH CD 3/2025)."
    )
    ent = extract_entities(html)
    assert ent.item_type == "proiect_hotarare"
    assert ent.action == "modificare_anexa"
    assert any(a.act_type == "HotarareParlament" and a.nr == "5" for a in ent.referenced_acts)


def test_integration_dezbateri_politice() -> None:
    html = (
        'Dezbateri politice, cu participarea doamnei Diana-Anda Buzoianu, ministrul mediului, '
        'la solicitarea Grupului parlamentar AUR, cu tema "Dezastrul administrativ..."'
    )
    ent = extract_entities(html)
    assert ent.item_type == "dezbateri_politice"
    assert ent.initiator_group == "AUR"


# ---------------------------------------------------------------------------
# extract_institutions
# ---------------------------------------------------------------------------

def test_institutions_eu_comisie():
    text = "Proiectul de Hotărâre privind adoptarea opiniei referitoare la Comunicarea Comisiei Europene"
    assert "Comisia Europeană" in extract_institutions(text)

def test_institutions_eu_multiple():
    text = ("Comunicarea Comisiei Europene către Parlamentul European, Consiliul UE, "
            "Comitetul Economic şi Social European şi Comitetul Regiunilor")
    inst = extract_institutions(text)
    assert "Comisia Europeană" in inst
    assert "Parlamentul European" in inst
    assert "Comitetul Regiunilor" in inst
    assert "CESE" in inst
    assert "Consiliul UE" in inst

def test_institutions_bnr():
    text = "Proiectul de Lege privind statutul Bancii Nationale a Romaniei"
    assert "BNR" in extract_institutions(text)

def test_institutions_csm():
    text = "Propunere legislativă privind organizarea Consiliului Superior al Magistraturii"
    assert "CSM" in extract_institutions(text)

def test_institutions_none():
    text = "Proiectul de Lege pentru modificarea Codului fiscal"
    assert extract_institutions(text) == []

def test_institutions_in_entities():
    html = ("Proiectul de Hotărâre privind adoptarea opiniei referitoare la "
            "Comunicarea Comisiei Europene și a Parlamentului European privind strategia digitală")
    ent = extract_entities(html)
    assert "Comisia Europeană" in ent.institutions
    assert "Parlamentul European" in ent.institutions

# ---------------------------------------------------------------------------
# Extended action patterns
# ---------------------------------------------------------------------------

def test_action_prorogare():
    text = "Proiectul de Lege privind prorogarea termenului prevăzut la art.5"
    assert extract_action(text, "proiect_lege") == "prorogare"

def test_action_ratificare():
    text = "Proiectul de Lege privind ratificarea Acordului dintre România și Franța"
    assert extract_action(text, "proiect_lege") == "ratificare"

def test_action_adoptare_opinie():
    text = "Proiectul de Hotărâre privind adoptarea opiniei referitoare la Comunicarea Comisiei"
    assert extract_action(text, "proiect_hotarare") == "adoptare_opinie"

# ---------------------------------------------------------------------------
# Extended flag patterns
# ---------------------------------------------------------------------------

def test_flag_sesizare_neconstitutionalitate():
    text = "Sesizare de neconstituționalitate a Legii nr.50/2020"
    assert "sesizare_neconstitutionalitate" in extract_flags(text)

def test_flag_cerere_reexaminare():
    text = "Reexaminarea cererii de reexaminare a Legii nr.100/2024"
    assert "cerere_reexaminare" in extract_flags(text)
