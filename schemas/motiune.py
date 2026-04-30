"""Moțiuni parlamentare — simple sau de cenzură.

Sursa: cdep.ro/pls/parlam/motiuni2015.lista + parlament.motiuni2015.detalii
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class TipMotiune(StrEnum):
    SIMPLA = "simpla"
    CENZURA = "cenzura"
    OTHER = "other"


class RezultatMotiune(StrEnum):
    ADOPTATA = "adoptata"
    RESPINSA = "respinsa"
    RETRASA = "retrasa"
    IN_PROCEDURA = "in_procedura"
    OTHER = "other"


class SemnatarMotiune(BaseModel):
    """Un deputat semnatar al moțiunii."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nume: str
    canonical_id: str | None = Field(None, description="Match cu Deputat.id")
    partid: str | None = None


class Motiune(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Hash stabil pe (cam, idm)")
    cdep_idm: int = Field(..., description="ID intern cdep.ro")
    cam: int = Field(default=2, description="1=Senat, 2=Camera, 0=ambele")
    legislatura: int

    nr_inregistrare: str | None = None
    data_inregistrare: date | None = None
    titlu: str
    tip: TipMotiune = TipMotiune.SIMPLA
    initiatori_descriere: str | None = Field(
        None, description="Ex: 'Inițiată de cel puțin 50 de deputați AUR'"
    )

    # Vot
    data_vot: date | None = None
    vot_pentru: int | None = None
    vot_contra: int | None = None
    vot_abtineri: int | None = None
    rezultat: RezultatMotiune = RezultatMotiune.IN_PROCEDURA

    # Semnatari (când sunt listați nominal)
    nr_semnatari: int | None = None
    semnatari: list[SemnatarMotiune] = Field(default_factory=list)

    # Documente
    pdf_url: HttpUrl | None = None

    source_url: HttpUrl
