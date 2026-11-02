"""Image reader: dark strokes become lines. Only horizontal and vertical strokes are read (that is how most plans are drawn); a thick stroke keeps its thickness, which is how a wall drawn
as a filled band is recognized. Coordinates are those of the picture itself, so what is found lies exactly over the image shown to the person."""
import io
import math
from typing import Dict, List, Optional, Tuple

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


def _overlap(s: int, e: int, bs: float, be: float) -> bool:
    """Are two runs about the same stretch: nearly as long as each other and sharing most of it?"""
    short, long_ = sorted((e - s, be - bs))
    return short >= 0.6 * long_ and min(e, be) - max(s, bs) >= 0.7 * short


def _extend(by_end: Dict[int, List[List]], by_start: Dict[int, List[List]], row: int, start: int, end: int, tol: int, q: int):
    """The band of the previous row this run continues: one that ends (or starts) in the same place and overlaps it. A door leaf or a piece of furniture touching a wall makes the other end drift
    from row to row; the wall is still one band."""
    for table, value, at in ((by_end, end, 5), (by_start, start, 4)):
        for d in (-1, 0, 1):
            for band in table.get(value // q + d, ()):
                if band[3] != row and abs(band[at] - value) <= tol and _overlap(start, end, band[4], band[5]):
                    return band
    return None


def merge_rows(rows, starts, ends, tol: int) -> List[Band]:
    """Runs on consecutive rows that continue one another make one band: its first and last row give its thickness and the middle of its ends gives its length (the median over its rows)."""
    bands: List[List] = []
    by_end: Dict[int, List[List]] = {}
    by_start: Dict[int, List[List]] = {}
    last_row, q = None, 2 * tol + 1
    new_end: Dict[int, List[List]] = {}
    new_start: Dict[int, List[List]] = {}
    for r, s, e in zip(rows.tolist(), starts.tolist(), ends.tolist()):
        if r != last_row:
            consecutive = last_row is not None and r == last_row + 1
            last_row = r
            by_end, by_start = ({}, {}) if not consecutive else (new_end, new_start)
            new_end, new_start = {}, {}
        band = _extend(by_end, by_start, r, s, e, tol, q)
        if band is None:
            band = [s, e, r, r, s, e, [s], [e]]                       # [start, end, first row, last row, latest start, latest end, all starts, all ends]
            bands.append(band)
        else:
            band[4], band[5] = s, e
            band[6].append(s)
            band[7].append(e)
        band[3] = r
        new_end.setdefault(e // q, []).append(band)
        new_start.setdefault(s // q, []).append(band)
    out = []
    for b in bands:
        b[0] = sorted(b[6])[len(b[6]) // 2]
        b[1] = sorted(b[7])[len(b[7]) // 2]
        out.append((b[0], b[1], b[2], b[3]))
    return out


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


def drop_frame(lines: List[Line], w: int, h: int, edge: float = 0.015, span: float = 0.6) -> List[Line]:
    """The border of the sheet or of a screenshot: a long stroke along the edge of the picture is not part of the plan."""
    def frame(l: Line) -> bool:
        horiz = l.a[1] == l.b[1]
        pos, length, side, extent = (l.a[1], abs(l.b[0] - l.a[0]), h, w) if horiz else (l.a[0], abs(l.b[1] - l.a[1]), w, h)
        return (length >= span * extent and (pos <= edge * side or pos >= (1 - edge) * side)) or (length >= 0.97 * extent and (pos <= 0.05 * side or pos >= 0.95 * side))
    return [l for l in lines if not frame(l)]


def close_gaps(ink: np.ndarray) -> np.ndarray:
    """Fill the seams of one or two pixels that anti-aliasing and joined polygons leave inside a stroke, so a wall drawn as a band is one band and not two."""
    d = ink.copy()
    d[1:] |= ink[:-1]
    d[:-1] |= ink[1:]
    d[:, 1:] |= ink[:, :-1]
    d[:, :-1] |= ink[:, 1:]
    e = d.copy()
    e[1:] &= d[:-1]
    e[:-1] &= d[1:]
    e[:, 1:] &= d[:, :-1]
    e[:, :-1] &= d[:, 1:]
    return e


def _box_sum(a: np.ndarray, k: int) -> np.ndarray:
    """Sum of every (2k+1) x (2k+1) window of a 0/1 array, by integral image."""
    s = np.pad(a.astype(np.int32), ((k + 1, k), (k + 1, k))).cumsum(0).cumsum(1)
    n = 2 * k + 1
    return s[n:, n:] - s[:-n, n:] - s[n:, :-n] + s[:-n, :-n]


def opening(ink: np.ndarray, k: int) -> np.ndarray:
    """What survives of the ink when everything narrower than 2k+1 pixels is taken away: fine lines, lettering and hatching go; thick strokes keep their shape."""
    full = (2 * k + 1) ** 2
    return _box_sum(_box_sum(ink, k) == full, k) > 0


def wall_size(solid: np.ndarray) -> Optional[int]:
    """How thick the walls are in pixels, from how the ink thins out as it is opened by wider and wider squares: a plan whose walls are thick bands keeps most of that ink up to the width of its
    walls and loses it at once beyond. None when it does not (walls drawn as two thin lines). Measured on the full picture: a reduced copy would erase thin walls."""
    areas = {}
    for k in (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 24):
        areas[k] = int(opening(solid, k).sum())
        if not areas[k]:
            break
    if not areas.get(2) or areas[2] < 0.25 * areas[1]:
        return None
    knee = max(k for k, a in areas.items() if k >= 2 and a >= 0.5 * areas[2])
    return 2 * knee + 1


def wall_bands(solid: np.ndarray, size: int, min_len: int, tol: int) -> List[Line]:
    """The thick strokes of the picture as bands, one per stretch of wall: found on the ink opened to just below the wall thickness, so a wall is one band however many fine lines cross or
    hatch it, and lettering, dimension lines and furniture are not there."""
    k = max(2, int(round(0.3 * (size - 1) / 2)))
    mask = opening(solid, k)
    bands = _lines(merge_rows(*runs(mask, min_len), tol), True) + _lines(merge_rows(*runs(mask.T, min_len), tol), False)
    return [Line(l.a, l.b, l.width, "wall") for l in bands if 2 * k + 1 <= l.width <= 2.5 * size and math.hypot(l.b[0] - l.a[0], l.b[1] - l.a[1]) >= 2.5 * l.width]   # far thicker than a wall: a title block, a filled area


def axis_lines(strokes: List[Line], shape, span: float = 0.45, min_cross: int = 3) -> List[Line]:
    """The structural axes (and grid lines) of the sheet: thin straight lines running across a good part of it that cross others of their kind in their middle. A wall meets other walls at
    its ends or in a T; an axis crosses them."""
    H, W = shape
    m = 0.03 * max(W, H)
    horiz = [l for l in strokes if l.width <= 3 and l.a[1] == l.b[1] and abs(l.b[0] - l.a[0]) >= span * W]
    vert = [l for l in strokes if l.width <= 3 and l.a[0] == l.b[0] and abs(l.b[1] - l.a[1]) >= span * H]

    def crossings(l: Line, others: List[Line], h: bool) -> int:
        n = 0
        for o in others:
            (x, y), (xa, xb), (ya, yb) = ((o.a[0], l.a[1]), sorted((l.a[0], l.b[0])), sorted((o.a[1], o.b[1]))) if h else                                           ((l.a[0], o.a[1]), sorted((o.a[0], o.b[0])), sorted((l.a[1], l.b[1])))
            n += xa + m < x < xb - m and ya + m < y < yb - m
        return n
    return [l for l in horiz if crossings(l, vert, True) >= min_cross] + [l for l in vert if crossings(l, horiz, False) >= min_cross]


def erase_thin(ink: np.ndarray, lines: List[Line]) -> np.ndarray:
    """The ink without these thin lines, except where something thicker crosses them (a wall the axis runs through keeps its pixels)."""
    out = ink.copy()
    H, W = ink.shape
    for l in lines:
        h = l.a[1] == l.b[1]
        half = int(math.ceil(l.width / 2)) + 1
        if h:
            y, x0, x1 = int(l.a[1]), int(min(l.a[0], l.b[0])), int(max(l.a[0], l.b[0]))
            above, below = ink[max(0, y - half - 1), x0:x1], ink[min(H - 1, y + half + 1), x0:x1]
            keep = above & below
            band = out[max(0, y - half):y + half + 1, x0:x1]
            band[:, ~keep] = False
        else:
            x, y0, y1 = int(l.a[0]), int(min(l.a[1], l.b[1])), int(max(l.a[1], l.b[1]))
            left, right = ink[y0:y1, max(0, x - half - 1)], ink[y0:y1, min(W - 1, x + half + 1)]
            keep = left & right
            band = out[y0:y1, max(0, x - half):x + half + 1]
            band[~keep, :] = False
    return out


def closing(ink: np.ndarray, r: int) -> np.ndarray:
    """The ink with every gap narrower than about 2r+1 pixels filled: the two thin faces of a wall drawn as a pair of lines become one band."""
    grown = _box_sum(ink.astype(np.uint8), r) > 0
    return ~(_box_sum((~grown).astype(np.uint8), r) > 0)


def face_shares(band: Line, marks: np.ndarray) -> Tuple[float, float]:
    """How much of each face of the band is a straight unbroken mark (an outline, or the edge of a fill), looking a few pixels either side of where the face should be."""
    h = band.a[1] == band.b[1]
    half = band.width / 2
    s0, s1 = sorted((band.a[0], band.b[0])) if h else sorted((band.a[1], band.b[1]))
    along = np.arange(int(s0) + 1, int(s1) - 1)
    if len(along) < 3:
        return 0.0, 0.0
    H, W = marks.shape
    shares = []
    for side in (-1, 1):
        best = 0.0
        for k in range(-3, 4):
            pos = int(round((band.a[1] if h else band.a[0]) + side * (half - 0.5) + k))
            if h and 0 <= pos < H:
                best = max(best, float(marks[pos, np.clip(along, 0, W - 1)].mean()))
            elif not h and 0 <= pos < W:
                best = max(best, float(marks[np.clip(along, 0, H - 1), pos].mean()))
        shares.append(best)
    return shares[0], shares[1]


def wall_shaped(bands: List[Line], marks: np.ndarray) -> List[Line]:
    """The bands that are walls by their shape. A wall is a long box whose two faces are straight and unbroken, and the walls of a plan are about one width: the bands with perfect
    faces give that width, and a band of that width whose faces are broken here and there (a window, a door frame) is a wall too. Lettering, dashes and furniture shut into a band have
    ragged faces and are narrower."""
    cfg = PARAMS["raster"]
    shares = [face_shares(b, marks) for b in bands]
    sure = [b for b, (p, q) in zip(bands, shares) if min(p, q) >= cfg["face_share"]]
    if not sure:
        return []
    widths = sorted(b.width for b in sure)
    usual = widths[len(widths) // 2]
    return [b for b, (p, q) in zip(bands, shares)
            if min(p, q) >= cfg["face_share"] or (abs(b.width - usual) <= cfg["width_match"] * usual and min(p, q) >= cfg["face_share_broken"])]


def diagonal_bands(mask: np.ndarray, marks: np.ndarray, size: int, min_len: int, tol: int) -> List[Line]:
    """Walls at 45 degrees (a cut corner): the picture turned an eighth of a turn makes them level, where they are read like any other band and turned back."""
    cfg = PARAMS["raster"]
    H, W = mask.shape
    out: List[Line] = []
    for angle in (45,):                                                       # one eighth turn: the walls at 45 degrees lie level, those at 135 upright
        rot = lambda a: np.asarray(Image.fromarray(a.astype(np.uint8) * 255).rotate(angle, resample=Image.NEAREST, expand=True)) > 127   # noqa: E731
        m, k = rot(mask), rot(marks)
        H2, W2 = m.shape
        th = math.radians(angle)
        c, s = math.cos(th), math.sin(th)

        def back(p):                                                           # a point of the turned picture, in the picture
            dx, dy = p[0] - W2 / 2, p[1] - H2 / 2
            return (W / 2 + dx * c - dy * s, H / 2 + dx * s + dy * c)
        bands = [b for b in wall_bands(m, size, min_len, tol) if math.hypot(b.b[0] - b.a[0], b.b[1] - b.a[1]) >= cfg["diagonal_min_length"] * b.width]
        for b in wall_shaped(bands, k):
            if abs(b.width - size) <= 0.5 * size:
                out.append(Line(back(b.a), back(b.b), b.width, "wall"))
    return out


def _with_bands(strokes: List[Line], mask: np.ndarray, min_len: int, tol: int, shape, marks: Optional[np.ndarray] = None) -> Optional[List[Line]]:
    """The strokes of the picture with the walls found as bands in `mask` in place of the thick ones, or None when the mask has no bands. When the mask was made by shutting outlines and
    hatching, `marks` is the picture before that: only the bands whose faces are drawn straight there are walls."""
    size = wall_size(mask)
    if not size:
        return None
    bands = drop_frame(wall_bands(mask, size, min_len, tol), shape[1], shape[0])
    if marks is not None:
        bands = wall_shaped(bands, marks) + diagonal_bands(mask, marks, size, min_len, tol)
    if len(bands) < PARAMS["walls"]["min_votes"]:
        return None
    return [l for l in strokes if l.width < size * 0.45] + bands


def read_image(img: Image.Image, options: Options) -> Primitives:
    cfg = PARAMS["raster"]
    full_w, full_h = img.size
    factor = max(1.0, max(img.size) / cfg["max_side"])
    work = img.convert("L") if factor == 1.0 else img.convert("L").resize((int(full_w / factor), int(full_h / factor)), Image.LANCZOS)
    gray = np.asarray(work)
    level = otsu(gray)
    ink = gray <= level
    inverted = ink.mean() > cfg["max_ink"]                           # light strokes on a dark ground (a blueprint): the strokes are the minority
    if inverted:
        ink = gray > level
    elif ((gray > 50) & (gray < 205)).mean() > cfg["max_midtones"]:
        raise ArchError("the picture is a render or a photo, not a drawing in lines: send the plan as a line drawing, a vector PDF or a DXF")
    min_len = max(8, int(cfg["min_run_factor"] * max(gray.shape)))
    tol = cfg["merge_tolerance"]
    solid = close_gaps(ink)
    horizontal = _lines(merge_rows(*runs(solid, min_len), tol), True)
    vertical = _lines(merge_rows(*runs(solid.T, min_len), tol), False)
    strokes = drop_frame(prune(horizontal + vertical), gray.shape[1], gray.shape[0])
    axes = axis_lines(strokes, gray.shape)
    faint_axes: List[Line] = []
    if not inverted:                                                            # axes drawn in a pale dash-dot line: joined up among every mark, the long thin lines that cross each other
        joined = closing(close_gaps(gray <= cfg["paper_level"]), 3)
        f_strokes = _lines(merge_rows(*runs(joined, min_len), tol), True) + _lines(merge_rows(*runs(joined.T, min_len), tol), False)
        faint_axes = axis_lines(f_strokes, gray.shape, cfg["axis_span"], 1)
    if axes:                                                                    # structural axes cross the whole plan: they are not walls and must not close rooms
        solid = erase_thin(solid, axes)
        strokes = [l for l in strokes if l not in axes]
    with_bands = lambda mask: _with_bands(strokes, mask, min_len, tol, gray.shape)          # noqa: E731
    lines = with_bands(solid) or strokes
    scale = lambda ls: [Line((l.a[0] * factor, l.a[1] * factor), (l.b[0] * factor, l.b[1] * factor), l.width * factor, l.layer) for l in ls]   # noqa: E731
    scaled = scale(lines)
    prims = Primitives(source="image", lines=scaled, y_up=False, fit=False, units_per_metre=options.units_per_metre, extent=(float(full_w), float(full_h)))
    for r in cfg["double_line_closings"]:                                      # walls drawn as two thin lines: shut the space between them and they are bands too
        alt = _with_bands(strokes, closing(solid, r), min_len, tol, gray.shape, solid)
        if alt:
            prims.alternatives.append(scale(alt))
    if not inverted:
        # A plan with tinted floors: the threshold takes the tints as ink. The walls are the neutral ink, or the darkest: read those alone as well.
        rgb = img.convert("RGB") if factor == 1.0 else img.convert("RGB").resize(work.size, Image.LANCZOS)
        sat = np.asarray(rgb.convert("HSV"))[..., 1]
        masks = []
        coloured = (sat > cfg["colour_saturation"]) & ink
        if coloured.mean() > cfg["min_coloured_share"] * max(ink.mean(), 1e-6):
            masks.append(ink & ~coloured)
        masks.append(gray <= cfg["paper_level"])                            # every mark on the paper, whatever its colour: a wall is a shape, a long band of even width
        for grey in cfg["dark_levels"]:
            if grey < level - 20 and (gray <= grey).mean() > 0.005:
                masks.append(gray <= grey)
        for raw_mask in masks:
            m = close_gaps(raw_mask)
            if faint_axes:
                m = erase_thin(m, faint_axes)
            m_strokes = drop_frame(prune(_lines(merge_rows(*runs(m, min_len), tol), True) + _lines(merge_rows(*runs(m.T, min_len), tol), False)), gray.shape[1], gray.shape[0])
            for mask in (m, closing(m, 3), closing(m, 5)):                     # outlines and hatching shut into the solid band they draw
                alt = _with_bands(m_strokes, mask, min_len, tol, gray.shape, None if mask is m else m) or (m_strokes if mask is m else None)
                if alt:
                    prims.alternatives.append(scale(alt))
    marks = ink if inverted else gray <= max(level, cfg["swing_max_grey"])          # door swings are often drawn in a light grey line
    prims.ink, prims.ink_scale = marks, factor
    if not inverted:
        prims.faint = gray <= max(level, cfg["paper_level"])                    # and some in a grey so light that only "any mark on the paper" sees them
    if inverted:
        prims.warnings.append("image: light strokes on a dark ground (a blueprint), read inverted")
    prims.warnings.append("image: only horizontal and vertical strokes are read; door swings are looked for in the picture around the gaps of the walls")
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

