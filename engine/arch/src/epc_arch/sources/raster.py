"""Image reader: dark strokes become lines. Only horizontal and vertical strokes are read (that is how most plans are drawn); a thick stroke keeps its thickness, which is how a wall drawn
as a filled band is recognized. Coordinates are those of the picture itself, so what is found lies exactly over the image shown to the person."""
import io
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image

from epc_arch.config import PARAMS
from epc_arch.model import ArchError, Line, Options, Primitives
from epc_arch.sources import register

Band = Tuple[float, float, float, float]            # start, end, first row, last row (inclusive)


def otsu(gray: np.ndarray) -> int:
    """The grey level that best separates ink from paper."""
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    total = hist.sum()
    levels = np.arange(256)
    w0 = np.cumsum(hist)
    m0 = np.cumsum(hist * levels)
    w1 = total - w0
    with np.errstate(divide="ignore", invalid="ignore"):
        between = (w0 * w1) * (m0 / w0 - (m0[-1] - m0) / w1) ** 2
    return int(np.nanargmax(between)) if np.isfinite(between).any() else 128


def runs(ink: np.ndarray, min_len: int):
    """Every run of ink at least `min_len` long along each row: (rows, starts, ends), the run covering [start, end)."""
    pad = np.zeros((ink.shape[0], 1), dtype=np.int8)
    d = np.diff(np.concatenate([pad, ink.astype(np.int8), pad], axis=1), axis=1)
    rows, starts = np.nonzero(d == 1)
    _, ends = np.nonzero(d == -1)
    keep = (ends - starts) >= min_len
    return rows[keep], starts[keep], ends[keep]


def _extend(active: Dict, key: Tuple[int, int], start: int, end: int, tol: int):
    """The band of the previous row this run continues, looking at the neighbouring cells of the grid."""
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            band = active.get((key[0] + dx, key[1] + dy))
            if band is not None and abs(band[0] - start) <= tol and abs(band[1] - end) <= tol:
                return band
    return None


def merge_rows(rows, starts, ends, tol: int) -> List[Band]:
    """Runs on consecutive rows with (almost) the same ends make one band: its first and last row give its thickness."""
    bands: List[List[float]] = []
    prev: Dict[Tuple[int, int], List[float]] = {}
    cur: Dict[Tuple[int, int], List[float]] = {}
    last_row, q = None, 2 * tol + 1
    for r, s, e in zip(rows.tolist(), starts.tolist(), ends.tolist()):
        if r != last_row:
            prev, cur, last_row = (cur if last_row is not None and r == last_row + 1 else {}), {}, r
        key = (s // q, e // q)
        band = _extend(prev, key, s, e, tol)
        if band is None:
            band = [s, e, r, r]
            bands.append(band)
        band[3] = r
        cur[key] = band
    return [(b[0], b[1], b[2], b[3]) for b in bands]


def _lines(bands: List[Band], horizontal: bool) -> List[Line]:
    out = []
    for s, e, r0, r1 in bands:
        mid = (r0 + r1 + 1) / 2
        a, b = ((s, mid), (e, mid)) if horizontal else ((mid, s), (mid, e))
        out.append(Line(a, b, float(r1 - r0 + 1)))
    return out


def _inside(thin: Line, thick: Line) -> bool:
    """The thin stroke lies within the rectangle of the thick one (it is the edge of a wall band, not a line of its own)."""
    h = thick.a[1] == thick.b[1]
    ax, bx = sorted((thick.a[0], thick.b[0])) if h else (thick.a[0] - thick.width / 2, thick.a[0] + thick.width / 2)
    ay, by = (thick.a[1] - thick.width / 2, thick.a[1] + thick.width / 2) if h else sorted((thick.a[1], thick.b[1]))
    xs, ys = (thin.a[0], thin.b[0]), (thin.a[1], thin.b[1])
    return all(ax - 1 <= x <= bx + 1 for x in xs) and all(ay - 1 <= y <= by + 1 for y in ys)


def prune(lines: List[Line], thick_from: float = 6.0, thin_to: float = 2.0) -> List[Line]:
    """Remove the thin strokes found inside thick bands: the edges a band leaves in the other direction."""
    thick = [l for l in lines if l.width >= thick_from]
    return [l for l in lines if l.width > thin_to or not any(_inside(l, t) for t in thick)]


def read_image(img: Image.Image, options: Options) -> Primitives:
    cfg = PARAMS["raster"]
    full_w, full_h = img.size
    factor = max(1.0, max(img.size) / cfg["max_side"])
    work = img.convert("L") if factor == 1.0 else img.convert("L").resize((int(full_w / factor), int(full_h / factor)), Image.LANCZOS)
    gray = np.asarray(work)
    ink = gray <= otsu(gray)
    min_len = max(8, int(cfg["min_run_factor"] * max(gray.shape)))
    tol = cfg["merge_tolerance"]
    horizontal = _lines(merge_rows(*runs(ink, min_len), tol), True)
    vertical = _lines(merge_rows(*runs(ink.T, min_len), tol), False)
    lines = prune(horizontal + vertical)
    scaled = [Line((l.a[0] * factor, l.a[1] * factor), (l.b[0] * factor, l.b[1] * factor), l.width * factor) for l in lines]
    prims = Primitives(source="image", lines=scaled, y_up=False, fit=False, units_per_metre=options.units_per_metre, extent=(float(full_w), float(full_h)))
    prims.warnings.append("image: only horizontal and vertical strokes are read, and door arcs are not")
    if len(scaled) > PARAMS["plan"]["max_primitives"]:
        raise ArchError("the image has too many strokes to read: send a cleaner or smaller one")
    return prims


@register
class RasterReader:
    kind = "image"

    def read(self, data: bytes, options: Options) -> Primitives:
        try:
            img = Image.open(io.BytesIO(data))
            img.load()
        except (OSError, ValueError, Image.DecompressionBombError):
            raise ArchError("the image cannot be read")
        return read_image(img, options)

