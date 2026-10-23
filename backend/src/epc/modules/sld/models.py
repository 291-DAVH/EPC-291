from typing import List, Optional

from pydantic import BaseModel


class Board(BaseModel):
    name: str = ""
    voltage_v: float = 380
    system: str = "TN-S"                    # TN-S | TN-C-S | IT
    icc_ka: float = 10
    fp_default: float = 0.85
    frequency_hz: float = 50
    project: str = ""
    feeder_length_m: float = 20             # supply cable length (acometida)


class Circuit(BaseModel):
    tag: str
    description: str = ""
    load: Optional[float] = None            # empty for a parent that sums its children
    unit: str = "kW"                        # A | W | kW | MW | VA | kVA | MVA | HP
    destination: str = ""
    parent_tag: str = ""
    topology: str = "single"
    phase: str = "3F"                       # 3F | 1F | 3F+N
    length_m: float = 0
    fp: Optional[float] = None
    efficiency: Optional[float] = None
    kind: str = "auto"
    notes: str = ""
    cable_type: str = "tetra_sep"


class Titleblock(BaseModel):
    company: str = ""
    company_cuit: str = ""
    client: str = ""
    client_cuit: str = ""
    drawn_by: str = ""
    checked_by: str = ""
    approved_by: str = ""
    description: str = ""
    location: str = ""
    scale: str = "1:50"
    revision: str = "A"
    status: str = "Emitido"


class SldIn(BaseModel):
    board: Board
    circuits: List[Circuit]
    titleblock: Titleblock = Titleblock()
