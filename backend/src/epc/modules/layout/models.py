from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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


class DrawingIn(BaseModel):
    """What the person drew on one level of the project, in the units of the view (the pixels of the plan)."""
    discipline: str = "electrica_BT"
    scale: Optional[Scale] = None
    origin: List[float] = [0.0, 0.0]        # the point 0,0 the person set
    nodes: List[NodeIn] = []
    lines: List[LineIn] = []
    circuits: List[CircuitIn] = []
    outlet: str = ""                        # node where a network drains to
    outlet_invert_m: Optional[float] = None
    dxf_version: str = ""
