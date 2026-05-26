"""Schema pentru averile parsate din PDF-urile ANI.

Structură pe 2 niveluri:
- AvereDeputat = un deputat + lista cronologică a tuturor declarațiilor lui
- AvereDeclaratie = o declarație specifică (la o dată anume) cu categoriile parsate
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class AvereImobil(BaseModel):
    """Un teren sau o clădire declarată."""

    categorie: str = Field(description="teren | cladire")
    suprafata_mp: float | None = Field(default=None, description="Suprafață în m²")
    anul_dobandirii: int | None = None
    cota_parte: str | None = Field(default=None, description="Ex: '50%', '100%'")
    modul_dobandirii: str | None = Field(default=None, description="Moștenire, cumpărare, etc.")


class AvereDeclaratie(BaseModel):
    """O declarație individuală depusă la o anumită dată."""

    data_depunere: date | None = Field(description="Data depunerii la ANI")
    pdf_url: HttpUrl
    text_extracted: bool = Field(description="True dacă pdfplumber a citit text")
    error: str | None = None

    # Categorii numerice agregate
    terenuri_count: int = 0
    cladiri_count: int = 0
    suprafata_total_mp: float = 0.0
    conturi_total_ron: float = Field(default=0.0, description="Active financiare normalizat la RON")
    venituri_anuale_ron: float = Field(
        default=0.0, description="Suma veniturilor anuale (salarii, dividende, chirii)"
    )
    datorii_total_ron: float = 0.0
    auto_count: int = Field(default=0, description="Mențiuni autoturism (proxy)")

    # Detalii imobile (opțional, pentru când vrem listă completă)
    imobile_detaliate: list[AvereImobil] = Field(default_factory=list)


class AvereDeputat(BaseModel):
    """Un deputat cu toate declarațiile lui cronologic."""

    id: str = Field(description="sha256('{leg}|{cdep_idm}|avere')[:16]")
    cdep_idm: int
    deputat_nume: str
    deputat_canonical_id: str | None = None
    legislatura: int
    partid_short: str | None = None

    # Cronologie: cele mai vechi întâi
    declaratii: list[AvereDeclaratie] = Field(
        default_factory=list, description="Toate declarațiile, sortate cronologic"
    )

    # Snapshot final (ultima declarație) — pentru sumar/index rapid
    ultima_data: date | None = None
    ultima_conturi_ron: float = 0.0
    ultima_venituri_ron: float = 0.0
    ultima_imobile_count: int = 0

    # Delta — diferență între prima și ultima declarație
    delta_conturi_ron: float = Field(
        default=0.0, description="Schimbare conturi între prima și ultima declarație"
    )
    delta_imobile: int = Field(
        default=0, description="Schimbare nr. imobile între prima și ultima declarație"
    )


class AvereSummary(BaseModel):
    """Sumar pentru index — fără declarațiile complete."""

    id: str
    cdep_idm: int
    deputat_nume: str
    legislatura: int
    partid_short: str | None = None
    n_declaratii: int = 0
    ultima_data: date | None = None
    ultima_conturi_ron: float = 0.0
    ultima_venituri_ron: float = 0.0
    ultima_imobile_count: int = 0
    delta_conturi_ron: float = 0.0
    delta_imobile: int = 0
    detail_url: str
