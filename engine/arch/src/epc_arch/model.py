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
    extent: Optional[Tuple[float, float]] = None   # the size of the picture when the source is one (an image keeps its own frame)
    warnings: List[str] = field(default_factory=list)


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

    def as_dict(self) -> Dict[str, Any]:
        r3 = lambda p: [round(p[0], 3), round(p[1], 3)]                          # noqa: E731
        return {"schema_version": "1.0", "source": self.source, "size": [round(self.size[0], 3), round(self.size[1], 3)], "units_per_metre": self.units_per_metre, "scale_hint": self.scale_hint,
                "wall_thickness": None if self.wall_thickness is None else round(self.wall_thickness, 3),
                "walls": [{"id": w.id, "a": r3(w.a), "b": r3(w.b), "thickness": round(w.thickness, 3), "confidence": round(w.confidence, 2), "reason": w.reason} for w in self.walls],
                "openings": [{"id": o.id, "kind": o.kind, "at": r3(o.at), "width": round(o.width, 3), "angle": round(o.angle, 2), "wall": o.wall, "confidence": round(o.confidence, 2), "reason": o.reason,
                              **({"hinge": r3(o.hinge)} if o.hinge else {}), **({"swing": r3(o.swing)} if o.swing else {})} for o in self.openings],
                "counts": {"walls": len(self.walls), "doors": sum(1 for o in self.openings if o.kind == "door"), "windows": sum(1 for o in self.openings if o.kind == "window"),
                           "openings": sum(1 for o in self.openings if o.kind == "opening")},
                "warnings": self.warnings}


@dataclass(frozen=True)
class Options:
    """What the caller may say about the file: its kind (else it is recognized from its bytes), the scale if known, the page of a PDF."""
    kind: str = ""
    units_per_metre: Optional[float] = None
    page: int = 0
    background: bool = True               # draw the original linework faintly under the recognized elements


class ArchError(ValueError):
    """The file cannot be recognized: the message says why."""
