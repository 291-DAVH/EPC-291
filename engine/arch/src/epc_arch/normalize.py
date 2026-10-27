"""From the frame of a source to the plan space (see `model`): y down, origin at the top left, and a standard size for a vector source. An image already is a picture: it is left as it is."""
from typing import Optional, Tuple

from epc_arch.config import PARAMS
from epc_arch.model import Arc, ArchError, Block, Line, Primitives

Size = Tuple[float, float]


def bounds(prims: Primitives) -> Optional[Tuple[float, float, float, float]]:
    xs = [p[0] for l in prims.lines for p in (l.a, l.b)] + [v for a in prims.arcs for v in (a.c[0] - a.r, a.c[0] + a.r)] + [b.at[0] for b in prims.blocks]
    ys = [p[1] for l in prims.lines for p in (l.a, l.b)] + [v for a in prims.arcs for v in (a.c[1] - a.r, a.c[1] + a.r)] + [b.at[1] for b in prims.blocks]
    return (min(xs), min(ys), max(xs), max(ys)) if xs and ys else None


def _flip_arc(a: Arc) -> Arc:
    """The same arc seen with y down: counter-clockwise becomes growing angle, so the ends swap and change sign."""
    return Arc(a.c, a.r, (-a.end) % 360.0, (-a.start) % 360.0, a.layer)


def _map(prims: Primitives, fn, scale: float, flip: bool, units: Optional[float]) -> Primitives:
    out = Primitives(source=prims.source, y_up=False, fit=False, units_per_metre=units, warnings=list(prims.warnings))
    out.lines = [Line(fn(l.a), fn(l.b), l.width * scale, l.layer) for l in prims.lines]
    arcs = [_flip_arc(a) if flip else a for a in prims.arcs]
    out.arcs = [Arc(fn(a.c), a.r * scale, a.start, a.end, a.layer) for a in arcs]
    out.blocks = [Block(b.name, fn(b.at), b.width * scale, -b.rotation if flip else b.rotation, b.layer) for b in prims.blocks]
    return out


def normalize(prims: Primitives) -> Tuple[Primitives, Size]:
    """The primitives in the plan space and the size of the plan. Raises ArchError when there is nothing to recognize."""
    if prims.extent is not None:
        prims.y_up = False
        return prims, prims.extent
    box = bounds(prims)
    if box is None or max(box[2] - box[0], box[3] - box[1]) <= 0:
        raise ArchError("the plan has no lines to read")
    x0, y0, x1, y1 = box
    scale = PARAMS["plan"]["target_side"] / max(x1 - x0, y1 - y0) if prims.fit else 1.0
    fn = (lambda p: ((p[0] - x0) * scale, (y1 - p[1]) * scale)) if prims.y_up else (lambda p: ((p[0] - x0) * scale, (p[1] - y0) * scale))
    units = prims.units_per_metre * scale if prims.units_per_metre else None
    return _map(prims, fn, scale, prims.y_up, units), ((x1 - x0) * scale, (y1 - y0) * scale)
