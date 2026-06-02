"""Schema pentru ordinea de zi a ședințelor plenului Camerei Deputaților."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, HttpUrl

from schemas.ordine_zi_entities import OrdineZiItemEntities


class DocOrdineZiItem(BaseModel):
    """Un document asociat unui punct de pe ordinea de zi (din more_docs_pl)."""

    data: date | None = Field(default=None, description="Data documentului.")
    titlu: str = Field(description="Denumirea documentului.")
    pdf_url: HttpUrl | None = Field(default=None, description="Link PDF la document.")
    sursa: str = Field(default="fisa_pl", description='"fisa_pl" sau "caseta".')


class OrdineZiItem(BaseModel):
    """Un punct de pe ordinea de zi."""

    pozitie: int | None = Field(
        default=None,
        description="Poziția numerică (1, 2, 3...). None pentru info-uri procedurale fără număr.",
    )
    nr_inregistrare: str | None = Field(
        default=None,
        description="Identificator proiect (ex. 'Pl-x 464/2023'). None dacă nu e proiect.",
    )
    idp: int | None = Field(
        default=None,
        description="Cdep_idp pentru cross-link cu /proiecte endpoint. None dacă nu e proiect.",
    )
    descriere: str = Field(description="Textul descriptiv al punctului (poate conține markup HTML: <b>, <i>, <br>).")
    doc_pdf_url: HttpUrl | None = Field(
        default=None, description="Link PDF cu textul punctului (alocuțiune, comunicare etc.)."
    )
    ozitm: int | None = Field(
        default=None,
        description="ID intern cdep.ro pentru documentele asociate (`more_docs_pl?ozitm=N`).",
    )
    docs: list[DocOrdineZiItem] = Field(
        default_factory=list, description="Documente asociate din more_docs_pl (fisa PL + caseta)."
    )
    entities: OrdineZiItemEntities | None = Field(
        default=None, description="Entități extrase din câmpul descriere (populate de build_ordine_zi_entities.py)."
    )


class OrdineZi(BaseModel):
    """Ordinea de zi pentru o ședință a plenului."""

    id: str = Field(description="Hash unic: sha256('{cam}|{session_date}')[:16].")
    session_date: date = Field(description="Data ședinței (prima zi dacă e multi-zi).")
    session_date_end: date | None = Field(
        default=None,
        description="Ultima zi a ședinței dacă e multi-zi (ex. 26-27 mai → end=27).",
    )
    legislatura: int
    cam: int = 2
    titlu: str = Field(description="Titlul complet din heading.")
    data_aprobare: date | None = Field(default=None, description="Data la care a fost aprobată.")
    pdf_url: HttpUrl | None = Field(default=None, description="PDF cu ordinea de zi completă.")
    items: list[OrdineZiItem] = Field(
        default_factory=list, description="Lista punctelor pe ordinea de zi."
    )
    source_url: HttpUrl
