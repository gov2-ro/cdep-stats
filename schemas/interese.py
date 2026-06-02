"""Schema pentru declarații de interese ale deputaților."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class InteresCompanie(BaseModel):
    """§1 — Asociat sau acționar la societate comercială / asociație / fundație."""

    denumire: str
    calitate: str = Field(description="Asociat | Acționar | Fondator | Membru")
    nr_titluri: int | None = None
    tip_titluri: str | None = Field(default=None, description="Părți sociale | Acțiuni")
    valoare_ron: float | None = None


class InteresConductere(BaseModel):
    """§2 — Calitatea de conducere/administrare în organe de decizie."""

    denumire: str
    calitate_conducere: str | None = Field(
        default=None,
        description="Administrator | Președinte | Vicepreședinte | Cenzor | Fondator | Altele",
    )
    valoare_beneficii_ron: float | None = None


class InteresContract(BaseModel):
    """§5 — Contract obținut de la o instituție publică."""

    beneficiar_tip: str = Field(
        description="titular | sot_sotie | rude | societate_comerciala"
    )
    beneficiar_denumire: str | None = None
    institutie_contractanta: str | None = None
    tip_contract: str | None = None
    valoare_ron: float | None = None
    valoare_aproximativa: bool = Field(
        default=False,
        description="True când valoarea a fost reconstituită dintr-un număr fragmentat "
        "pe mai multe coloane de tabel (limitare pdfplumber). Valoarea poate fi inexactă.",
    )
    data_incheiere: date | None = None


class InteresDeclaratie(BaseModel):
    """O declarație de interese parsată dintr-un PDF ANI."""

    pdf_url: HttpUrl
    data_depunere: date | None = Field(
        default=None, description="Data din indexul cdep.ro"
    )
    ani_id: str | None = Field(default=None, description="Numărul de înregistrare ANI")
    tip_declaratie: str | None = Field(
        default=None, description="numire | anual | incetare"
    )
    data_completarii: date | None = Field(
        default=None, description="Data semnării PDF-ului"
    )
    text_extracted: bool = False
    error: str | None = None

    # §1 — Companii/asociații în care deputatul este asociat/acționar
    companii: list[InteresCompanie] = Field(default_factory=list)
    nr_companii: int = 0

    # §2 — Funcții în organe de conducere
    conducere: list[InteresConductere] = Field(default_factory=list)

    # §3 — Asociații profesionale / sindicale (text liber)
    asociatii_profesionale_raw: str | None = None

    # §4 — Funcții în partide politice
    partide_raw: list[str] = Field(
        default_factory=list,
        description='Texte brute, ex. "PNL Filiala Cluj - Vicepreședinte"',
    )
    are_functie_partid: bool = False

    # §5 — Contracte cu instituții publice
    contracte: list[InteresContract] = Field(default_factory=list)
    are_contracte_publice: bool = False
    contracte_total_ron: float = 0.0


class InteresDeputat(BaseModel):
    """Un deputat cu toate declarațiile lui de interese, cronologic."""

    id: str = Field(description="sha256('{leg}|{cdep_idm}|interese')[:16]")
    cdep_idm: int
    deputat_nume: str
    deputat_canonical_id: str | None = None
    legislatura: int
    partid_short: str | None = None

    declaratii: list[InteresDeclaratie] = Field(default_factory=list)

    # Snapshot ultima declarație
    ultima_data: date | None = None
    ultima_nr_companii: int = 0
    ultima_are_functie_partid: bool = False
    ultima_are_contracte_publice: bool = False
    ultima_contracte_total_ron: float = 0.0


class InteresSummary(BaseModel):
    """Sumar pentru fișierul index — fără declarațiile complete."""

    id: str
    cdep_idm: int
    deputat_nume: str
    legislatura: int
    partid_short: str | None = None
    n_declaratii: int = 0
    ultima_data: date | None = None
    ultima_nr_companii: int = 0
    ultima_are_functie_partid: bool = False
    ultima_are_contracte_publice: bool = False
    ultima_contracte_total_ron: float = 0.0
    detail_url: str
