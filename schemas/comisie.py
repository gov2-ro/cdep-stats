"""Comisie parlamentară — agregat din profilele deputaților.

Datele sunt deja în `data/v1/deputati/legislatura-*.json` (nested în `Deputat.comisii`).
Builderul din `scripts/build_comisii.py` le grupează după nume + tip și produce un
endpoint dedicat cu lista completă de membri pentru fiecare comisie.

Tipuri observate pe cdep.ro:
- permanenta — comisii permanente ale Camerei Deputaților
- speciala — comisii speciale ad-hoc
- comuna — comisii comune cu Senatul
- speciala_comuna — comisii speciale comune cu Senatul
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TipComisie(StrEnum):
    PERMANENTA = "permanenta"
    SPECIALA = "speciala"
    COMUNA = "comuna"
    SPECIALA_COMUNA = "speciala_comuna"


class RolMembru(StrEnum):
    PRESEDINTE = "Președinte"
    VICEPRESEDINTE = "Vicepreședinte"
    SECRETAR = "Secretar"
    MEMBRU = "Membru"


class ComisieMembru(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    deputat_canonical_id: str = Field(..., description="Hash stabil — match cu Deputat.id")
    deputat_nume: str
    deputat_cdep_idm: int = Field(..., description="ID-ul intern cdep.ro")
    partid: str | None = None
    rol: str = Field(default="Membru", description="Rolul în comisie")


class Comisie(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(..., description="Slug stabil derivat din nume + legislatură")
    nume: str = Field(..., description="Numele oficial al comisiei")
    tip: TipComisie
    legislatura: int

    # Statistici
    nr_membri: int = Field(..., description="Total membri")

    # Conducerea (poate fi None pentru comisii fără ierarhie completă)
    presedinte: str | None = None
    vicepresedinti: list[str] = Field(default_factory=list)
    secretari: list[str] = Field(default_factory=list)

    # Membri (toți, inclusiv conducerea)
    membri: list[ComisieMembru] = Field(default_factory=list)
