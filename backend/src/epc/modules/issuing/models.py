from typing import List, Optional

from pydantic import BaseModel


class IssueItem(BaseModel):
    source: str                         # id from the candidates list, e.g. electrical/PQ-01/drawing/SLD_TGBT-01
    name: Optional[str] = None          # deliverable title; defaults to the file name


class IssueIn(BaseModel):
    emission: str = "ifa"               # ifa | ifc | as-built
    client_rev: str = "00"              # the revision the client sees (Rev 00)
    internal_rev: str = "00.0.0"        # internal revision 00.R.C, recorded in the transmittal
    items: List[IssueItem]
    notes: str = ""
