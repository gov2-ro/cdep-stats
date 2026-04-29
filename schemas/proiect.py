"""Proiect legislativ — propuneri și proiecte de lege.

Sursa: cdep.ro/pls/proiecte/upl_pck2015.{lista,proiect}
URL list:    /upl_pck2015.lista?anp={year}&cam=2
URL detail:  /upl_pck2015.proiect?cam=2&idp={N}

Vezi sitemap.md §3.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class CaracterProiect(StrEnum):
    ORDINAR = "ordinar"
    ORGANIC = "organic"
    OTHER = "other"


class TipInitiativa(StrEnum):
    PROIECT_LEGE = "proiect_lege"
    PROPUNERE_LEGISLATIVA = "propunere_legislativa"
    OUG = "ordonanta_urgenta"
    OG = "ordonanta_guvern"
    OTHER = "other"


class TimelineEvent(BaseModel):
    """Un eveniment din timeline-ul procedurii (data + descriere)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    data: date | None = None
    eveniment: str = Field(..., description="Ce s-a întâmplat la acea dată")


class Proiect(BaseModel):
    """Un proiect legislativ înregistrat la Camera Deputaților."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Identificare
    id: str = Field(..., description="Hash stabil pe (cam, idp)")
    cdep_idp: int = Field(..., description="ID intern cdep.ro din URL")
    cam: int = Field(default=2, description="1=Senat, 2=Camera Deputaților, 0=ambele")
    legislatura: int

    # Numere de înregistrare
    nr_inregistrare: str | None = Field(
        None, description="Forma compactă (PL-x nr/data)", examples=["PL-x 1/2025"]
    )
    nr_camera_deputati: str | None = None
    nr_senat: str | None = None
    nr_guvern: str | None = None
    nr_bpi: str | None = Field(None, description="Birourile Permanente Reunite")

    # Conținut
    titlu: str
    tip: TipInitiativa = TipInitiativa.PROIECT_LEGE
    caracter: CaracterProiect = CaracterProiect.ORDINAR
    procedura_urgenta: bool = False
    initiator: str | None = None
    camera_decizionala: str | None = None

    # Stadiu
    stadiu: str | None = Field(None, description="Text liber, ex. 'Lege 9/2025', 'în dezbatere'")
    lege_nr: str | None = Field(None, description="Extras din stadiu dacă promulgat")
    decret_nr: str | None = Field(None, description="Decret prezidențial de promulgare")

    # Date cheie
    data_prezentare: date | None = None
    data_inregistrare_cd: date | None = None
    data_adoptare_cd: date | None = None
    data_adoptare_senat: date | None = None
    data_promulgare: date | None = None

    # Vot final (când există)
    vot_pentru: int | None = None
    vot_contra: int | None = None
    vot_abtineri: int | None = None

    # Amendamente — metadate (lista completă e doar în PDF-ul raportului comisiei)
    amendamente_termen_depunere: date | None = Field(
        None, description="Deadline pentru depunere amendamente"
    )
    amendamente_admise: int | None = Field(
        None, description="Număr amendamente admise în raportul comisiei"
    )
    amendamente_respinse: int | None = Field(
        None, description="Număr amendamente respinse în raportul comisiei"
    )
    raport_comisie_pdf: HttpUrl | None = Field(
        None, description="URL-ul PDF cu raportul comisiei (conține lista completă de amendamente)"
    )

    # Timeline complet
    timeline: list[TimelineEvent] = Field(default_factory=list)

    # Documente atașate (PDF-uri din pagina detaliu)
    documente_pdf: list[HttpUrl] = Field(default_factory=list)

    source_url: HttpUrl
