"""Schema pentru declarații de avere și interese ale deputaților."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl


class DeclaratieFisier(BaseModel):
    """Un fișier PDF de declarație (poate fi inițială sau modificare)."""

    url: HttpUrl
    data: date | None = Field(default=None, description="Data declarației (DD.MM.YYYY).")


class DeclaratieDeputat(BaseModel):
    """Declarațiile (avere + interese) ale unui deputat dintr-o legislatură."""

    id: str = Field(description="sha256('{leg}|{cdep_idm}')[:16].")
    cdep_idm: int
    deputat_nume: str
    deputat_canonical_id: str | None = Field(
        default=None, description="Cross-link cu /deputati canonical_id."
    )
    legislatura: int
    partid_short: str | None = Field(default=None, description="Abrevierea grupului parlamentar.")
    avere: list[DeclaratieFisier] = Field(
        default_factory=list, description="Declarațiile de avere (inițială + modificări)."
    )
    interese: list[DeclaratieFisier] = Field(
        default_factory=list, description="Declarațiile de interese (inițială + modificări)."
    )
    source_url: HttpUrl
