"""DXF reader: lines, polylines (with their arcs and width), arcs, hatch boundaries and the blocks that are inserted, in the layers that are visible."""
import math
import tempfile
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import ezdxf
from ezdxf import units as dxf_units
from ezdxf.math import bulge_to_arc

from epc_arch.model import Arc, ArchError, Block, Line, Options, Primitives
from epc_arch.sources import register

SKIPPED = ("TEXT", "MTEXT", "DIMENSION", "SPLINE", "ELLIPSE", "IMAGE", "LEADER", "POINT", "CIRCLE", "SOLID", "TRACE")
MAX_DEPTH = 3


def _xy(p) -> Tuple[float, float]:
    return (float(p[0]), float(p[1]))


def _polyline_segments(points: List[Tuple[float, float, float]], closed: bool, width: float, layer: str):
    """Straight pieces become lines, pieces with a bulge become arcs (a door swing is often drawn that way)."""
    lines, arcs = [], []
    n = len(points)
    for i in range(n if closed else n - 1):
        (x0, y0, b), (x1, y1, _) = points[i], points[(i + 1) % n]
        if abs(b) < 1e-9:
            lines.append(Line((x0, y0), (x1, y1), width, layer))
            continue
        c, a0, a1, r = bulge_to_arc((x0, y0), (x1, y1), b)
        arcs.append(Arc(_xy(c), float(r), math.degrees(a0), math.degrees(a1), layer))
    return lines, arcs


def _lwpolyline(e):
    pts = [(p[0], p[1], p[2]) for p in e.get_points("xyb")]
    return _polyline_segments(pts, bool(e.closed), float(e.dxf.get("const_width", 0.0) or 0.0), e.dxf.layer)


def _polyline(e):
    if not e.is_2d_polyline:
        return [], []
    pts = [(v.dxf.location.x, v.dxf.location.y, v.dxf.get("bulge", 0.0)) for v in e.vertices]
    return _polyline_segments(pts, bool(e.is_closed), 0.0, e.dxf.layer)


def _hatch(e):
    lines = []
    for path in e.paths:
        verts = [(v[0], v[1], 0.0) for v in getattr(path, "vertices", [])]
        if len(verts) >= 2:
            lines += _polyline_segments(verts, True, 0.0, e.dxf.layer)[0]
    return lines, []


def _entity(e):
    """(lines, arcs) of one entity, or None when it is not geometry this reader uses."""
    kind = e.dxftype()
    if kind == "LINE":
        return [Line(_xy(e.dxf.start), _xy(e.dxf.end), 0.0, e.dxf.layer)], []
    if kind == "ARC":
        return [], [Arc(_xy(e.dxf.center), float(e.dxf.radius), float(e.dxf.start_angle), float(e.dxf.end_angle), e.dxf.layer)]
    if kind == "LWPOLYLINE":
        return _lwpolyline(e)
    if kind == "POLYLINE":
        return _polyline(e)
    return _hatch(e) if kind == "HATCH" else None


def _insert_width(virtual) -> float:
    xs = [p for v in virtual if v.dxftype() == "LINE" for p in (v.dxf.start.x, v.dxf.end.x)]
    return float(max(xs) - min(xs)) if xs else 0.0


def _walk(entities: Iterable, prims: Primitives, skipped: Counter, depth: int, visible) -> None:
    for e in entities:
        if not visible(e.dxf.layer):
            continue
        if e.dxftype() == "INSERT" and depth < MAX_DEPTH:
            virtual = list(e.virtual_entities())
            prims.blocks.append(Block(e.dxf.name, _xy(e.dxf.insert), _insert_width(virtual), float(e.dxf.get("rotation", 0.0)), e.dxf.layer))
            _walk(virtual, prims, skipped, depth + 1, visible)
            continue
        got = _entity(e)
        if got is None:
            skipped[e.dxftype()] += 1
            continue
        prims.lines += got[0]
        prims.arcs += got[1]


def _units_per_metre(doc) -> Optional[float]:
    code = int(doc.units or 0)
    if code == 0:
        return None
    try:
        factor = dxf_units.conversion_factor(code, dxf_units.M)
    except (KeyError, ValueError):
        return None
    return 1.0 / factor if factor else None


def _open(data: bytes):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "plan.dxf"
        path.write_bytes(data)
        try:
            return ezdxf.readfile(str(path))
        except Exception:                                    # noqa: BLE001 - the parser fails in many ways on a file that is not a DXF (StopIteration, struct errors, ...)
            raise ArchError("the DXF cannot be read: it is not a valid DXF file")


@register
class DxfReader:
    kind = "dxf"

    def read(self, data: bytes, options: Options) -> Primitives:
        doc = _open(data)
        layers = doc.layers
        visible = lambda name: not (name in layers and (layers.get(name).is_off() or layers.get(name).is_frozen()))     # noqa: E731
        prims = Primitives(source="dxf", y_up=True, fit=True, units_per_metre=options.units_per_metre or _units_per_metre(doc))
        skipped: Counter = Counter()
        _walk(doc.modelspace(), prims, skipped, 0, visible)
        if skipped:
            prims.warnings.append("not read: " + ", ".join(f"{n} {k.lower()}" for k, n in sorted(skipped.items())))
        return prims
