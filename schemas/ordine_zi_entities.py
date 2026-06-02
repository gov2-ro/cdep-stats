"""Schema pentru entitățile extrase din descrierea punctelor ordinii de zi."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class ReferencedAct(BaseModel):
    """Un act normativ menționat în descrierea unui punct."""

    act_type: str = Field(description="Tipul actului: OUG, OG, Lege, HotarareParlament, HotarareCamDepuati, CCR.")
    nr: str = Field(description="Numărul actului (ex. '38').")
    year: int | None = Field(default=None, description="Anul actului (ex. 2025). None pentru CCR.")
    raw: str = Field(description="Fragmentul de text original din care a fost extras.")


class OrdineZiItemEntities(BaseModel):
    """Entități extrase din câmpul `descriere` al unui punct de pe ordinea de zi."""

    item_type: str | None = Field(
        default=None,
        description=(
            "Tipul documentului: proiect_lege, proiect_hotarare, propunere_legislativa, "
            "reexaminare, motiune_simpla, motiune_cenzura, informare, informare_casete, "
            "declaratie, dezbateri_politice, raport, solicitare, vacantare, alocutiuni, moment_reculegere."
        ),
    )
    action: str | None = Field(
        default=None,
        description=(
            "Acțiunea legislativă: aprobare_oug, aprobare_og, modificare, completare, "
            "modificare_si_completare, modificare_anexa, abilitare, constituire, "
            "aprobare_componenta, aprobare, revocare, vacantare_act, transmitere, privind."
        ),
    )
    law_category: str | None = Field(
        default=None,
        description="Categoria legii: lege_organica, lege_ordinara. None dacă nu se aplică.",
    )
    flags: list[str] = Field(
        default_factory=list,
        description=(
            "Indicatori procedurali: procedura_urgenta, prioritate_legislativa, "
            "camera_decizionala, rezerva_raport, retrimis_comisie, vot_secret_bile, "
            "vot_deschis_electronic, adoptat_art115."
        ),
    )
    senate_adoption_date: date | None = Field(
        default=None, description="Data adoptării de Senat (dacă e menționată)."
    )
    referenced_acts: list[ReferencedAct] = Field(
        default_factory=list, description="Acte normative referențiate în descriere."
    )
    commissions: list[str] = Field(
        default_factory=list, description="Comisiile menționate în secțiunea Raport/Raport comun."
    )
    initiator_group: str | None = Field(
        default=None, description="Grupul parlamentar inițiator (ex. 'AUR', 'S.O.S. - România')."
    )
    initiator_count: int | None = Field(
        default=None, description="Numărul de inițiatori (deputați/senatori) pentru moțiuni."
    )
    initiator_type: str | None = Field(
        default=None,
        description="Tipul inițiatorilor: deputati, senatori, deputati_si_senatori.",
    )
    subject: str | None = Field(
        default=None,
        description="Subiectul principal al punctului (text curat fără metadata procedurală).",
    )
    institutions: list[str] = Field(
        default_factory=list,
        description=(
            "Instituții menționate explicit: UE (Comisia Europeană, Parlamentul European, "
            "Comitetul Regiunilor, CESE, Consiliul UE) și române (BNR, CSM, CCR, Curtea de Conturi)."
        ),
    )
