from typing import Dict, List, Optional

from pydantic import BaseModel


class OrganizationIn(BaseModel):
    legal_name: str = ""            # e.g. "Villena y Sosa S.R.L."
    tax_id: str = ""                # CUIT / tax identifier
    email: str = ""
    website: str = ""
    address: str = ""
    phone: str = ""
    default_locale: str = "es-AR"


class IssuerIn(OrganizationIn):
    """A company the office issues documents in the name of (an engineer may work for several, each towards its own clients)."""
    id: str = ""                    # generated from the legal name when empty


class TeamIn(BaseModel):
    drawn_by: str = ""              # proyecta
    checked_by: str = ""            # verifica
    approved_by: str = ""           # valida


class PartiesIn(BaseModel):
    issuer: str = ""                # id of the issuing company of this project (empty: the default one)
    team: Dict[str, TeamIn] = {}    # per discipline of the project: who designs, checks and approves


class ClientIn(BaseModel):
    id: str                         # short code, also the folder name of its projects (e.g. FORD)
    name: str
    tax_id: str = ""
    email: str = ""
    website: str = ""
    address: str = ""


class PersonIn(BaseModel):
    id: str = ""                    # generated from the name when empty
    name: str
    role: str = ""                  # e.g. "Ingeniero proyectista"
    registration: str = ""          # professional registration number
    initials: Optional[str] = None
    roles: List[str] = []           # what they do in the organization (see PERSON_ROLES)
