"""Schema pentru documente emise de comisii parlamentare."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class TipDocComisie:
    RAPORT = "raport"
    AVIZ = "aviz"
    SINTEZA = "sinteza"
    PROCES_VERBAL = "proces_verbal"
    OTHER = "other"


class DocComisie(BaseModel):
    """Un document emis de o comisie parlamentară (raport, aviz, sinteza, etc.)."""

    id: str = Field(description="sha256(url_pdf)[:16].")
    pdf_url: HttpUrl = Field(description="Link PDF cu textul documentului.")
    data: date | None = Field(default=None, description="Data documentului.")
    tip: str = Field(description="raport / aviz / sinteza / proces_verbal / other.")
    titlu: str = Field(description="Titlu/descriere (truncat la 500 caractere).")
    # Pentru rapoarte/avize — cross-link la proiect
    idp: int | None = Field(default=None, description="Cdep_idp pentru cross-link cu /proiecte.")
    nr_proiect: str | None = Field(
        default=None, description="Numărul proiectului (ex. 'PL 553/2025')."
    )
    # Comisiile emitente — pot fi multiple
    comisii: list[dict] = Field(
        default_factory=list,
        description="Lista comisiilor emitente: [{idc, nume, leg}]. Cross-link cu /comisii.",
    )
    source_url: HttpUrl
