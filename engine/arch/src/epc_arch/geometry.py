"""Plane geometry the recognizers share. Pure functions; angles in degrees, y down (see `model`)."""
import math
from dataclasses import dataclass
from typing import Tuple

Pt = Tuple[float, float]


def seg_length(a: Pt, b: Pt) -> float:
    return math.hypot(b[0] - a[0], b[1] - a[1])


def seg_angle(a: Pt, b: Pt) -> float:
    """Direction of a segment as an undirected line: 0 <= angle < 180."""
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 180.0


def angle_gap(x: float, y: float) -> float:
    """Smallest angle between two undirected directions."""
    d = abs(x - y) % 180.0
    return min(d, 180.0 - d)


@dataclass(frozen=True)
class Axis:
    """A direction and its normal: along it a point has a position `t`, across it an offset `o`."""
    theta: float
    ux: float
    uy: float

    @property
    def nx(self) -> float:
        return -self.uy

    @property
    def ny(self) -> float:
        return self.ux

    def t(self, p: Pt) -> float:
        return p[0] * self.ux + p[1] * self.uy

    def o(self, p: Pt) -> float:
        return p[0] * self.nx + p[1] * self.ny

    def at(self, t: float, o: float) -> Pt:
        return (self.ux * t + self.nx * o, self.uy * t + self.ny * o)


def axis_of(theta: float) -> Axis:
    r = math.radians(theta)
    return Axis(theta, math.cos(r), math.sin(r))


def dist_point_segment(p: Pt, a: Pt, b: Pt) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def dist_point_line(p: Pt, a: Pt, b: Pt) -> float:
    """Distance from a point to the infinite line through a and b."""
    n = seg_length(a, b)
    return abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1])) / n if n else math.hypot(p[0] - a[0], p[1] - a[1])


def arc_span(start: float, end: float) -> float:
    """How many degrees an arc covers going from `start` to `end` in the direction of growing angle."""
    return (end - start) % 360.0


def arc_point(c: Pt, r: float, deg: float) -> Pt:
    return (c[0] + r * math.cos(math.radians(deg)), c[1] + r * math.sin(math.radians(deg)))


def circle_through(p: Pt, q: Pt, s: Pt):
    """Centre and radius of the circle through three points, or None when they are in line."""
    ax, ay = p
    bx, by = q
    cx, cy = s
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    return (ux, uy), math.hypot(ax - ux, ay - uy)
