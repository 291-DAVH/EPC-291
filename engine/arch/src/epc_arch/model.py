"""The values the engine passes around: primitives (what a source gives), and walls, openings and the architecture (what the recognizers find). All immutable but the containers.

Everything downstream of the readers lives in the *plan space*: x to the right, y down, origin at the top left, so a drawing, an image and an SVG share one frame and the editor can lay
the recognized elements over the picture with no conversion. An angle in the plan space grows clockwise on the screen.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

Pt = Tuple[float, float]


@dataclass(frozen=True)
class Line:
    a: Pt
    b: Pt
    width: float = 0.0                    # stroke width, in the units of the drawing (0 = a hairline)
    layer: str = ""


@dataclass(frozen=True)
class Arc:
    c: Pt
    r: float
    start: float                          # degrees; the arc goes from `start` to `end` in the direction of growing angle
    end: float
    layer: str = ""


@dataclass(frozen=True)
class Block:
    name: str
    at: Pt
    width: float = 0.0                    # extent of what the block draws, 0 when unknown
    rotation: float = 0.0
    layer: str = ""


@dataclass
class Primitives:
    """What a reader found: the geometry of the plan and where it came from. `y_up` and `fit` say how to bring it to the plan space (see `normalize`)."""
    source: str
    lines: List[Line] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    blocks: List[Block] = field(default_factory=list)
    y_up: bool = False
    fit: bool = False                     # a vector source is scaled to a standard size; an image keeps its pixels
    units_per_metre: Optional[float] = None
    scale: Optional[int] = None           # the scale the sheet says it is drawn at (1:scale), when it says so
    extent: Optional[Tuple[float, float]] = None   # the size of the picture when the source is one (an image keeps its own frame)
    warnings: List[str] = field(default_factory=list)
    ink: Optional[Any] = None             # an image keeps its ink mask (numpy bool, rows = y) so that what a stroke list cannot say, the swing of a door, can be looked for in the picture
    faint: Optional[Any] = None           # every mark on the paper, however light (door swings drawn in a pale grey)
    ink_scale: float = 1.0                # picture pixels per mask pixel (the mask may be a reduced copy)
    alternatives: List[List[Line]] = field(default_factory=list)    # other readings of the same picture (walls drawn as pairs of lines, shut into bands)


@dataclass(frozen=True)
class Wall:
    id: str
    a: Pt
    b: Pt
    thickness: float
    confidence: float
    reason: str


@dataclass(frozen=True)
class Opening:
    id: str
    kind: str                             # door, window or opening (something that interrupts a wall and is neither)
    at: Pt
    width: float
    angle: float                          # direction of the wall it opens, degrees in 0..180
    wall: str
    confidence: float
    reason: str
    hinge: Optional[Pt] = None            # doors: where the leaf turns and where its free end swings to
    swing: Optional[Pt] = None


@dataclass(frozen=True)
class Room:
    id: str
    area: float                           # in plan units squared
    area_m2: Optional[float]              # when the units are known
    at: Pt                                # where to write its name or area
    rects: List[Tuple[float, float, float, float]] = field(default_factory=list)    # its floor as rectangles (x0, y0, x1, y1)


def _r3(p: Pt) -> List[float]:
    return [round(p[0], 3), round(p[1], 3)]


def _wall_dict(w: "Wall") -> Dict[str, Any]:
    return {"id": w.id, "a": _r3(w.a), "b": _r3(w.b), "thickness": round(w.thickness, 3), "confidence": round(w.confidence, 2), "reason": w.reason}


def _opening_dict(o: "Opening") -> Dict[str, Any]:
    out = {"id": o.id, "kind": o.kind, "at": _r3(o.at), "width": round(o.width, 3), "angle": round(o.angle, 2), "wall": o.wall, "confidence": round(o.confidence, 2), "reason": o.reason}
    if o.hinge:
        out["hinge"] = _r3(o.hinge)
    if o.swing:
        out["swing"] = _r3(o.swing)
    return out


def _room_dict(r: "Room") -> Dict[str, Any]:
    return {"id": r.id, "area": round(r.area, 1), "area_m2": None if r.area_m2 is None else round(r.area_m2, 2), "at": _r3(r.at)}


@dataclass
class Architecture:
    source: str
    size: Tuple[float, float]
    units_per_metre: Optional[float]
    scale_hint: Optional[Dict[str, Any]]
    wall_thickness: Optional[float]
    walls: List[Wall] = field(default_factory=list)
    openings: List[Opening] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    drawing_scale: Optional[int] = None

    def counts(self) -> Dict[str, int]:
        return {"walls": len(self.walls), "doors": sum(1 for o in self.openings if o.kind == "door"), "windows": sum(1 for o in self.openings if o.kind == "window"),
                "openings": sum(1 for o in self.openings if o.kind == "opening")}

    def as_dict(self) -> Dict[str, Any]:
        return {"schema_version": "1.0", "source": self.source, "size": [round(self.size[0], 3), round(self.size[1], 3)], "units_per_metre": self.units_per_metre, "drawing_scale": self.drawing_scale, "scale_hint": self.scale_hint,
                "wall_thickness": None if self.wall_thickness is None else round(self.wall_thickness, 3), "walls": [_wall_dict(w) for w in self.walls],
                "openings": [_opening_dict(o) for o in self.openings], "rooms": [_room_dict(r) for r in self.rooms], "counts": self.counts(), "warnings": self.warnings}


@dataclass(frozen=True)
class Options:
    """What the caller may say about the file: its kind (else it is recognized from its bytes), the scale if known, the page of a PDF."""
    kind: str = ""
    units_per_metre: Optional[float] = None
    page: int = 0
    background: bool = True               # draw the original linework faintly under the recognized elements


class ArchError(ValueError):
    """The file cannot be recognized: the message says why."""
