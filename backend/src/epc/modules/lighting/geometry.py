"""The geometry between the plan editor and the lighting engine, as pure functions.

The editor works in view units (the pixels of the plan); the engine in metres, with rooms that are rectangles: `length_m` along x, `width_m` along y, positions measured from
the corner of the room. A room that is a rectangle with the sides along the axes goes across exactly; any other outline goes across as its bounding box, which the caller says.
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from epc.modules.lighting.models import Scale

TOLERANCE = 0.01                                    # how much of the bounding box an outline may leave empty and still be a rectangle


class GeometryError(ValueError):
    """The outline or the scale cannot be used: the message says why."""


@dataclass(frozen=True)
class Rect:
    x0: float
    y0: float
    x1: float
    y1: float
    exact: bool                                     # the outline is a rectangle with its sides along the axes

    @property
    def width_u(self) -> float:
        return self.x1 - self.x0

    @property
    def height_u(self) -> float:
        return self.y1 - self.y0


def metres_per_unit(scale: Optional[Scale]) -> float:
    """How many metres a unit of the view is, from the two calibration points."""
    if scale is None:
        raise GeometryError("the sheet has no scale: calibrate it first")
    apart = math.hypot(scale.p2[0] - scale.p1[0], scale.p2[1] - scale.p1[1])
    if apart <= 0:
        raise GeometryError("the two points of the scale are the same point")
    return scale.distance_m / apart


def _area(points: Sequence[Sequence[float]]) -> float:
    """Area of a polygon by the shoelace formula (always positive)."""
    total = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, list(points[1:]) + [points[0]]))
    return abs(total) / 2


def rectangle(points: Sequence[Sequence[float]]) -> Rect:
    """The bounding box of an outline and whether the outline fills it (so it is a rectangle along the axes)."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    box = (x1 - x0) * (y1 - y0)
    if box <= 0:
        raise GeometryError("the outline has no area")
    return Rect(x0, y0, x1, y1, exact=_area(points) >= box * (1 - TOLERANCE))


def to_engine(rect: Rect, k: float) -> Tuple[float, float]:
    """(length_m, width_m) of the room for the engine: the extent along x and along y, in metres."""
    return round(rect.width_u * k, 4), round(rect.height_u * k, 4)


def to_view(rect: Rect, k: float, x_m: float, y_m: float) -> Tuple[float, float]:
    """A position of the engine (metres from the corner of the room) as a point of the view."""
    return round(rect.x0 + x_m / k, 3), round(rect.y0 + y_m / k, 3)


def corner(rect: Rect) -> List[float]:
    return [rect.x0, rect.y0]
