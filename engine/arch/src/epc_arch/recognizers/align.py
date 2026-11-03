"""The plans of one sheet are the floors of one building: they have to share a frame, so that a wall, a door or a point has the same coordinates on every floor. The floors are laid over each other by their
walls: the shift under which the walls of a floor and the walls of the reference floor coincide most is found by correlating their masks. When the walls do not agree enough (the floors share little),
the floors are put corner to corner instead and the result says so."""
import math
from dataclasses import replace
from typing import List, Optional, Tuple

import numpy as np

from epc_arch.config import PARAMS
from epc_arch.model import Architecture, Line, Marks, Primitives, Pt, Text, Wall

Shift = Tuple[float, float]


def _mask(walls: List[Wall], cell: float, shape: Tuple[int, int]) -> np.ndarray:
    """The floor of the walls as a picture: one pixel is `cell` plan units."""
    m = np.zeros(shape, dtype=np.float32)
    for w in walls:
        length = math.hypot(w.b[0] - w.a[0], w.b[1] - w.a[1]) or 1e-9
        ux, uy = (w.b[0] - w.a[0]) / length, (w.b[1] - w.a[1]) / length
        along = np.linspace(0.0, length, int(length / (cell / 2)) + 2)[:, None]
        across = np.linspace(-w.thickness / 2, w.thickness / 2, max(2, int(w.thickness / (cell / 2)) + 1))[None, :]
        xs = ((w.a[0] + ux * along - uy * across) / cell).astype(int)
        ys = ((w.a[1] + uy * along + ux * across) / cell).astype(int)
        ok = (xs >= 0) & (xs < shape[1]) & (ys >= 0) & (ys < shape[0])
        m[ys[ok], xs[ok]] = 1.0
    return m


def _bounds(walls: List[Wall]) -> Tuple[float, float, float, float]:
    xs = [c for w in walls for c in (w.a[0], w.b[0])]
    ys = [c for w in walls for c in (w.a[1], w.b[1])]
    return min(xs), min(ys), max(xs), max(ys)


def _correlate(a: np.ndarray, b: np.ndarray) -> Tuple[int, int, float]:
    """The shift (rows, columns) that lays `b` best over `a`, and how much of the smaller floor then coincides."""
    s = (a.shape[0] + b.shape[0], a.shape[1] + b.shape[1])
    c = np.fft.irfft2(np.fft.rfft2(a, s) * np.conj(np.fft.rfft2(b, s)), s)
    iy, ix = np.unravel_index(int(np.argmax(c)), c.shape)
    dy, dx = (iy - s[0] if iy > s[0] // 2 else iy), (ix - s[1] if ix > s[1] // 2 else ix)
    return int(dy), int(dx), float(c[iy, ix]) / max(1.0, min(a.sum(), b.sum()))


def _axes(walls: List[Wall], axis: int) -> List[float]:
    """The positions of the walls that run square to `axis` (x of the vertical ones for 0, y of the horizontal ones for 1)."""
    other = 1 - axis
    return [(w.a[axis] + w.b[axis]) / 2 for w in walls if abs(w.a[axis] - w.b[axis]) < 0.2 * abs(w.a[other] - w.b[other])]


def _residual(ref: List[float], mine: List[float], shift: float, reach: float) -> float:
    """What is left of the shift after the coarse one: the median distance from each wall to the nearest wall of the reference, for those within reach."""
    gaps = sorted(r - (m + shift) for m in mine for r in [min(ref, key=lambda r: abs(r - (m + shift)))] if abs(r - (m + shift)) <= reach) if ref else []
    return gaps[len(gaps) // 2] if gaps else 0.0


def _refine(reference: Architecture, other: Architecture, dx: float, dy: float, reach: float) -> Shift:
    """The coarse shift is a whole number of pixels of the masks: the walls themselves say the rest."""
    return (dx + _residual(_axes(reference.walls, 0), _axes(other.walls, 0), dx, reach), dy + _residual(_axes(reference.walls, 1), _axes(other.walls, 1), dy, reach))


def shift_onto(reference: Architecture, other: Architecture, thickness: float) -> Tuple[Shift, bool]:
    """How far to move `other` to lay it over `reference`, and whether its walls agreed with the reference ones (else it was put corner to corner)."""
    cfg = PARAMS["sheet"]
    cell = max(1.0, thickness * cfg["align_cell_in_walls"])
    shape = (int(max(reference.size[1], other.size[1]) / cell) + 2, int(max(reference.size[0], other.size[0]) / cell) + 2)
    dy, dx, overlap = _correlate(_mask(reference.walls, cell, shape), _mask(other.walls, cell, shape))
    if overlap >= cfg["align_min_overlap"]:
        return _refine(reference, other, dx * cell, dy * cell, cell), True
    ra, oa = _bounds(reference.walls), _bounds(other.walls)
    return (ra[0] - oa[0], ra[1] - oa[1]), False


def _pt(p: Optional[Pt], dx: float, dy: float) -> Optional[Pt]:
    return None if p is None else (p[0] + dx, p[1] + dy)


def move(arch: Architecture, dx: float, dy: float, size: Tuple[float, float], reference: Pt) -> Architecture:
    """The architecture seen from the shared frame: everything shifted by (dx, dy), in a frame of `size`."""
    walls = [replace(w, a=_pt(w.a, dx, dy), b=_pt(w.b, dx, dy)) for w in arch.walls]
    openings = [replace(o, at=_pt(o.at, dx, dy), hinge=_pt(o.hinge, dx, dy), swing=_pt(o.swing, dx, dy)) for o in arch.openings]
    rooms = [replace(r, at=_pt(r.at, dx, dy), rects=[(x0 + dx, y0 + dy, x1 + dx, y1 + dy) for x0, y0, x1, y1 in r.rects]) for r in arch.rooms]
    marks = {k: Marks([Line(_pt(l.a, dx, dy), _pt(l.b, dx, dy), l.width, l.layer) for l in m.lines], [replace(a, c=_pt(a.c, dx, dy)) for a in m.arcs],
                     [Text(t.value, _pt(t.at, dx, dy), t.height) for t in m.texts]) for k, m in arch.annotations.items()}
    return replace(arch, walls=walls, openings=openings, rooms=rooms, size=size, reference=reference, annotations=marks)


def move_prims(prims: Primitives, dx: float, dy: float) -> Primitives:
    """The strokes of a plan shifted the same way (the faint background of its drawing)."""
    out = Primitives(**{**prims.__dict__, "ink": None, "faint": None, "alternatives": []})
    out.lines = [Line(_pt(l.a, dx, dy), _pt(l.b, dx, dy), l.width, l.layer) for l in prims.lines]
    out.arcs = [replace(a, c=_pt(a.c, dx, dy)) for a in prims.arcs]
    return out
