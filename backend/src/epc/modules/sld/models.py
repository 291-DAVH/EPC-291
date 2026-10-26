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
    supplied_from: str = ""                 # id of the upstream board that feeds this one (empty: fed from the utility or a source outside the project)
    supply_tag: str = ""                    # circuit of the upstream board that is this board's supply


class Segment(BaseModel):
    """One stretch of the real route of a cable: how it is installed there decides its capacity."""
    kind: str                               # see epc_calc.aea_route.KINDS
    length_m: float
    label: str = ""
    ambient_c: Optional[float] = None       # air stretches (project value when empty)
    soil_c: Optional[float] = None          # buried stretches
    rho_kmw: Optional[float] = None         # soil thermal resistivity, buried stretches
    circuits: int = 1                       # circuits sharing the stretch, this one included
    depth_m: Optional[float] = None


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
    length_source: str = "auto"             # auto | plan | data: where the length comes from (see lengths.py)
    fp: Optional[float] = None
    efficiency: Optional[float] = None
    kind: str = "auto"
    notes: str = ""
    cable_type: str = "tetra_sep"
    route: List[Segment] = []               # real route of the outgoing cable; empty = installed as the circuit says; its total is the length


class Titleblock(BaseModel):
    """The sheet's title block. Company, client and people come from the project (issuer, client, team of the discipline) and are not stored here;
    what a board owns is its description, location, scale, revision and status."""
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
    drawing_type: str = ""                  # "Tipo de plano" of the title block
    replaces: str = ""                      # client code this drawing replaces
    replaced_by: str = ""                   # client code that replaces it
    internal_code: str = ""                 # the drawing's internal code (plano N°)


class SldIn(BaseModel):
    board: Board
    circuits: List[Circuit]
    titleblock: Titleblock = Titleblock()


class BoardIn(BaseModel):
    name: str
    supplied_from: str = ""
    supply_tag: str = ""
