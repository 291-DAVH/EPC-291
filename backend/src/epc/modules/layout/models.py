import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Scale(BaseModel):
    """Two points marked on the plan (view units) and the real distance between them."""
    p1: List[float]
    p2: List[float]
    distance_m: float


class NodeIn(BaseModel):
    id: str
    kind: str
    x: float
    y: float
    tag: str = ""
    board: str = ""                         # a board symbol stands for a board made in Engineering; a load is fed from one (its id): a reference, never created here
    circuit: str = ""                       # a load (luminaire, socket, HVAC...) belongs to a circuit of the board: a reference, never created here
    attrs: Dict[str, Any] = {}


class LineIn(BaseModel):
    id: str
    kind: str
    points: List[List[float]]
    tag: str = ""
    circuit: str = ""                       # tag of the circuit in the board: the line references it, it never creates it
    attrs: Dict[str, Any] = {}


class CircuitIn(BaseModel):
    """A circuit of the board routed over the drawing: from an origin node to a destination node, optionally through other nodes, with its parallel cables (ternas)."""
    model_config = ConfigDict(populate_by_name=True)
    tag: str = ""
    from_: str = Field("", alias="from")
    to: str = ""
    via: List[str] = []
    ternas: int = Field(1, ge=1, le=99)


class RoomIn(BaseModel):
    """A room marked on the plan (view units): its name and its outline. The automatic design makes a circuit of each family of load in each room."""
    id: str
    name: str = ""
    points: List[List[float]] = Field(min_length=3)
    lighting: Optional[Dict[str, Any]] = None        # what the person says about its lighting (activity, luminaire, method...): the lighting panel reads it, the engine never does


class DrawingIn(BaseModel):
    """What the person drew on one level of the project, in the units of the view (the pixels of the plan)."""
    discipline: str = "electrica_BT"
    subdiscipline: str = Field("", max_length=40)   # what this plan draws within its discipline (lighting, sockets, MV distribution...): decides the kinds the editor offers
    plan_name: str = Field("", max_length=60)      # what the person calls this plan when a discipline has several on a level ("Iluminación", "Tomacorrientes")
    scale: Optional[Scale] = None
    origin: List[float] = [0.0, 0.0]        # the point 0,0 the person set
    nodes: List[NodeIn] = []
    lines: List[LineIn] = []
    circuits: List[CircuitIn] = []
    rooms: List[RoomIn] = []                # rooms marked on the plan: editor and design only, the engine never reads them
    outlet: str = ""                        # node where a network drains to
    outlet_invert_m: Optional[float] = None
    dxf_version: str = ""
    underlay_opts: Dict[str, Any] = {}      # how the plan underlay is shown (opacity, rotation, locked, hidden, crop): editor-only, the engine never reads it
    lighting_settings: Dict[str, Any] = {}  # what the person set for the lighting panel of this sheet (limit, tariff, hours, templates...): the panel reads it, the engine never does

    @field_validator("lighting_settings")
    @classmethod
    def _small(cls, v):
        if len(json.dumps(v)) > 20000:
            raise ValueError("up to 20 000 characters")
        return v


class TemplateIn(BaseModel):
    """A group of nodes and lines saved to be put again, in the drawing's own units, with positions relative to the corner of the group."""
    discipline: str = "electrica_BT"
    nodes: List[Dict[str, Any]] = []
    lines: List[Dict[str, Any]] = []


class ArchIn(BaseModel):
    """How to recognize the architecture of the plan the person uploaded: the scale if they know it."""
    units_per_metre: Optional[float] = Field(None, gt=0)


class DesignIn(BaseModel):
    """Ask for a proposal of circuits and runs for the drawing as it is on the screen; `families` overrides, by family of load, the limit of outlets per circuit and the power per outlet."""
    drawing: DrawingIn
    board: str = ""
    families: Dict[str, Dict[str, float]] = {}


class NewCircuit(BaseModel):
    tag: str
    description: str = ""
    load: Optional[float] = None
    unit: str = "VA"


class NewCircuits(BaseModel):
    circuits: List[NewCircuit]
    board: str = ""                         # the board of the project that receives them (the first one when empty)
