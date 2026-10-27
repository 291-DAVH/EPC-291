"""PDF reader. A vector PDF (one made from CAD) is read path by path: its lines and the quarter circles of its door swings are exact. A PDF with no vector drawing in it (a scan) falls back to the
picture of its page, read like any image. Page, rotation of the page and nested forms are not interpreted: the first page as the CAD program wrote it."""
import ctypes
import io
import math
from typing import List, Optional, Tuple

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from PIL import Image

from epc_arch.config import PARAMS
from epc_arch.geometry import circle_through
from epc_arch.model import Arc, ArchError, Line, Options, Primitives
from epc_arch.sources import register
from epc_arch.sources.raster import read_image
from epc_arch.sources.render import render_or_fail

MIN_VECTOR = 12                                          # fewer strokes than this and the page is a picture
Seg = Tuple[int, float, float, bool]                     # type, x, y, closes the subpath


def _matrix(path) -> Tuple[float, float, float, float, float, float]:
    m = raw.FS_MATRIX()
    raw.FPDFPageObj_GetMatrix(path, m)
    return m.a, m.b, m.c, m.d, m.e, m.f


def _segments(path) -> List[Seg]:
    out = []
    for i in range(raw.FPDFPath_CountSegments(path)):
        seg = raw.FPDFPath_GetPathSegment(path, i)
        x, y = ctypes.c_float(), ctypes.c_float()
        raw.FPDFPathSegment_GetPoint(seg, x, y)
        out.append((raw.FPDFPathSegment_GetType(seg), x.value, y.value, bool(raw.FPDFPathSegment_GetClose(seg))))
    return out


def _stroke_width(path, m) -> float:
    w = ctypes.c_float()
    raw.FPDFPageObj_GetStrokeWidth(path, w)
    return float(w.value) * math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))


def arc_from_bezier(p0, c1, c2, p3) -> Optional[Arc]:
    """A cubic Bézier that is (nearly) a circular arc, as the arc: CAD programs draw a door swing that way. None for any other curve."""
    pt = lambda t: tuple((1 - t) ** 3 * p0[k] + 3 * (1 - t) ** 2 * t * c1[k] + 3 * (1 - t) * t * t * c2[k] + t ** 3 * p3[k] for k in (0, 1))      # noqa: E731
    fit = circle_through(p0, pt(0.5), p3)
    if fit is None:
        return None
    c, r = fit
    if any(abs(math.hypot(pt(t)[0] - c[0], pt(t)[1] - c[1]) - r) > 0.03 * r for t in (0.25, 0.75)):
        return None
    ang = lambda p: math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360.0                    # noqa: E731
    a0, am, a3 = ang(p0), ang(pt(0.5)), ang(p3)
    ccw = (am - a0) % 360.0 < (a3 - a0) % 360.0
    return Arc(c, r, a0 if ccw else a3, a3 if ccw else a0)


def _apply(m, x: float, y: float) -> Tuple[float, float]:
    return m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]


def _path_geometry(path, prims: Primitives, skipped: List[int]) -> None:
    m = _matrix(path)
    width = _stroke_width(path, m)
    start = cur = None
    bez: List[Tuple[float, float]] = []
    for typ, x, y, close in _segments(path):
        p = _apply(m, x, y)
        if typ == raw.FPDF_SEGMENT_MOVETO:
            start = cur = p
        elif typ == raw.FPDF_SEGMENT_LINETO and cur is not None:
            prims.lines.append(Line(cur, p, width))
            cur = p
        elif typ == raw.FPDF_SEGMENT_BEZIERTO and cur is not None:
            bez.append(p)
            if len(bez) == 3:
                arc = arc_from_bezier(cur, bez[0], bez[1], bez[2])
                prims.arcs.append(arc) if arc else skipped.append(1)
                cur, bez = bez[2], []
        if close and start is not None and cur is not None and cur != start:
            prims.lines.append(Line(cur, start, width))
            cur = start


def _is_frame(line: Line, page: Tuple[float, float]) -> bool:
    """The border of the sheet: a long stroke along the edge of the page, which is not part of the plan."""
    w, h = page
    near = lambda v, edge: abs(v - edge) < 0.01 * max(w, h)          # noqa: E731
    horiz = near(line.a[1], line.b[1]) and (near(line.a[1], 0) or near(line.a[1], h))
    vert = near(line.a[0], line.b[0]) and (near(line.a[0], 0) or near(line.a[0], w))
    return (horiz or vert) and math.hypot(line.b[0] - line.a[0], line.b[1] - line.a[1]) > 0.9 * min(w, h)


def read_vector(data: bytes, options: Options) -> Primitives:
    try:
        page = pdfium.PdfDocument(data)[options.page]
    except Exception:                                         # noqa: BLE001 - damaged, protected or no such page
        raise ArchError("the PDF cannot be read: it may be damaged or protected")
    prims = Primitives(source="pdf", y_up=True, fit=True, units_per_metre=options.units_per_metre)
    skipped: List[int] = []
    for obj in page.get_objects(filter=[raw.FPDF_PAGEOBJ_PATH]):
        _path_geometry(obj.raw, prims, skipped)
        if len(prims.lines) + len(prims.arcs) > PARAMS["plan"]["max_primitives"]:
            raise ArchError("the PDF has too many strokes to read")
    size = page.get_size()
    prims.lines = [l for l in prims.lines if not _is_frame(l, size)]
    if skipped:
        prims.warnings.append(f"pdf: {len(skipped)} curves that are not arcs were not read")
    return prims


@register
class PdfReader:
    kind = "pdf"

    def read(self, data: bytes, options: Options) -> Primitives:
        prims = read_vector(data, options)
        if len(prims.lines) + len(prims.arcs) >= MIN_VECTOR:
            return prims
        picture = Image.open(io.BytesIO(render_or_fail(data, options.page, PARAMS["raster"]["max_side"])))
        out = read_image(picture, options)
        out.source = "pdf-image"
        out.warnings.insert(0, "pdf: no vector drawing found, the picture of the page was read")
        return out
