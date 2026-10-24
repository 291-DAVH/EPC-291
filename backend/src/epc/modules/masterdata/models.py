from typing import Optional

from pydantic import BaseModel


class OrganizationIn(BaseModel):
    legal_name: str = ""            # e.g. "Villena y Sosa S.R.L."
    tax_id: str = ""                # CUIT / tax identifier
    email: str = ""
    website: str = ""
    address: str = ""
    phone: str = ""
    default_locale: str = "es-AR"


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
