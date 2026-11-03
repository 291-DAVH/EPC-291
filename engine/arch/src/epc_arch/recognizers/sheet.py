"""A drawing sheet is not a plan: it carries several views (plans of each floor, a section, an elevation, a perspective), a frame, a title block with its notes and tables, grid bubbles and dimension lines.
Read as one plan, the section's slabs and the elevation's bands set the wall thickness and the plans are lost. Here the sheet is taken apart before anything is recognized: the strokes that touch each
other (or nearly) form a view, the frame with its title block is the view that holds all the others and is left out, and each remaining view is cut out as a plan of its own."""
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from epc_arch.config import PARAMS
from epc_arch.model import Arc, Block, Line, Primitives, Text
from epc_arch.recognizers.levels import named

Box = Tuple[float, float, float, float]
Cell = Tuple[int, int]


@dataclass
class View:
    box: Box                                  # where it lies on the sheet, in the plan space of the sheet
    prims: Primitives                         # its strokes, in a frame of its own (origin at the top left of the box)
    items: int
    texts: List[Text] = field(default_factory=list)       # the texts of the sheet around it, in the frame of the sheet

    @property
    def size(self) -> Tuple[float, float]:
        return self.box[2] - self.box[0], self.box[3] - self.box[1]


def _line_cells(l: Line, cell: float) -> List[Cell]:
    n = max(1, int(max(abs(l.b[0] - l.a[0]), abs(l.b[1] - l.a[1])) / (cell / 2)))
    return [(int((l.a[0] + (l.b[0] - l.a[0]) * k / n) // cell), int((l.a[1] + (l.b[1] - l.a[1]) * k / n) // cell)) for k in range(n + 1)]


def _arc_cells(a: Arc, cell: float) -> List[Cell]:
    """The cells along the arc itself (its ends, which touch the wall and the leaf, and points between)."""
    span = (a.end - a.start) % 360.0 or 360.0
    steps = max(4, int(math.radians(span) * a.r / (cell / 2)))
    pts = [(a.c[0] + a.r * math.cos(math.radians(a.start + span * k / steps)), a.c[1] + a.r * math.sin(math.radians(a.start + span * k / steps))) for k in range(steps + 1)]
    return [(int(x // cell), int(y // cell)) for x, y in pts]


def _items(prims: Primitives, cell: float) -> List[Tuple[str, int, List[Cell]]]:
    """Every stroke as (kind, index, the cells it passes through)."""
    out = [("l", i, _line_cells(l, cell)) for i, l in enumerate(prims.lines)]
    out += [("a", i, _arc_cells(a, cell)) for i, a in enumerate(prims.arcs)]
    out += [("b", i, [(int(b.at[0] // cell), int(b.at[1] // cell))]) for i, b in enumerate(prims.blocks)]
    return out


def _labels(cells: List[Cell], reach: int) -> Dict[Cell, int]:
    """Connected groups of occupied cells, where cells up to `reach` apart are connected: the group of each cell."""
    occupied = set(cells)
    label: Dict[Cell, int] = {}
    window = [(dx, dy) for dx in range(-reach, reach + 1) for dy in range(-reach, reach + 1)]
    n = 0
    for start in occupied:
        if start in label:
            continue
        label[start] = n
        todo = [start]
        while todo:
            x, y = todo.pop()
            for dx, dy in window:
                q = (x + dx, y + dy)
                if q in occupied and q not in label:
                    label[q] = n
                    todo.append(q)
        n += 1
    return label


def _group_boxes(items, label: Dict[Cell, int], cell: float) -> Tuple[Dict[Tuple[str, int], int], Dict[int, Box]]:
    """The group of each stroke and the box of each group."""
    of: Dict[Tuple[str, int], int] = {}
    boxes: Dict[int, Box] = {}
    for kind, i, cells in items:
        g = label[cells[0]]
        of[(kind, i)] = g
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        x0, y0, x1, y1 = min(xs) * cell, min(ys) * cell, (max(xs) + 1) * cell, (max(ys) + 1) * cell
        old = boxes.get(g)
        boxes[g] = (x0, y0, x1, y1) if old is None else (min(old[0], x0), min(old[1], y0), max(old[2], x1), max(old[3], y1))
    return of, boxes


def _covers(box: Box, size: Tuple[float, float], share: float) -> bool:
    return (box[2] - box[0]) >= share * size[0] and (box[3] - box[1]) >= share * size[1]


def _within(inner: Box, outer: Box) -> bool:
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def _significant(boxes: Dict[int, Box], counts: Dict[int, int], size: Tuple[float, float], cfg) -> List[int]:
    """The groups big enough to be a view of the sheet: not a bubble, a north arrow or a table cell."""
    side = max(size)
    return [g for g, b in boxes.items() if max(b[2] - b[0], b[3] - b[1]) >= cfg["min_view_side"] * side and counts[g] >= cfg["min_view_items"]]


def _without_frame(groups: List[int], boxes: Dict[int, Box], size: Tuple[float, float], cfg) -> Tuple[List[int], bool]:
    """The frame with its title block is the group that spans the sheet and holds the others: it is left out. Returns the views and whether a frame was found."""
    frame = [g for g in groups if _covers(boxes[g], size, cfg["frame_cover"]) and all(_within(boxes[h], boxes[g]) for h in groups if h != g)]
    if len(groups) < 2 or not frame:
        return groups, False
    return [g for g in groups if g not in frame], True


def _shift(p, dx: float, dy: float):
    return (p[0] - dx, p[1] - dy)


def _snap(box: Box, step: float) -> Box:
    """A box on the grid of a picture's mask, so that cutting the mask and shifting the strokes agree to the pixel."""
    if step <= 1.0:
        return box
    return (box[0] // step * step, box[1] // step * step, -(-box[2] // step) * step, -(-box[3] // step) * step)


def _cut_mask(mask, box: Box, step: float):
    if mask is None:
        return None
    return mask[int(box[1] / step):int(box[3] / step) + 1, int(box[0] / step):int(box[2] / step) + 1]


def _view_prims(prims: Primitives, ids, box: Box) -> Primitives:
    dx, dy = box[0], box[1]
    keep = lambda kind, i: (kind, i) in ids                                              # noqa: E731
    out = Primitives(**{**prims.__dict__, "lines": [], "arcs": [], "blocks": [], "texts": [], "alternatives": []})
    out.lines = [Line(_shift(l.a, dx, dy), _shift(l.b, dx, dy), l.width, l.layer) for i, l in enumerate(prims.lines) if keep("l", i)]
    out.arcs = [Arc(_shift(a.c, dx, dy), a.r, a.start, a.end, a.layer) for i, a in enumerate(prims.arcs) if keep("a", i)]
    out.blocks = [Block(b.name, _shift(b.at, dx, dy), b.width, b.rotation, b.layer) for i, b in enumerate(prims.blocks) if keep("b", i)]
    if prims.ink is not None:
        step = prims.ink_scale
        out.ink, out.faint = _cut_mask(prims.ink, box, step), _cut_mask(prims.faint, box, step)
        out.extent = (box[2] - box[0], box[3] - box[1])
        out.alternatives = [[Line(_shift(l.a, dx, dy), _shift(l.b, dx, dy), l.width, l.layer) for l in alt if _inside(l.a, box) and _inside(l.b, box)] for alt in prims.alternatives]
    return out


def _inside(p, box: Box) -> bool:
    return box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3]


def _cell_box(items, cell: float) -> Box:
    xs = [c[0] for _, _, cells in items for c in cells]
    ys = [c[1] for _, _, cells in items for c in cells]
    return min(xs) * cell, min(ys) * cell, (max(xs) + 1) * cell, (max(ys) + 1) * cell


def _is_view(items, cell: float, size: Tuple[float, float], cfg) -> bool:
    b = _cell_box(items, cell)
    return max(b[2] - b[0], b[3] - b[1]) >= cfg["min_view_side"] * max(size) and len(items) >= cfg["min_view_items"]


def _valleys(items, axis: int, limit: int, cfg_share: float):
    """Where a few strokes at most (`limit`) cross a line across the drawing: as (strokes crossing, strokes before, strokes after), one for the best place of each run of such places.
    A few strokes can cross the space between two views (a grid line, a bubble that touches the next view), so the space need not be empty."""
    spans = [(min(c[axis] for c in it[2]), max(c[axis] for c in it[2])) for it in items]
    lo, hi = min(a for a, _ in spans), max(b for _, b in spans)
    crossing = [0] * (hi - lo + 2)
    for a, b in spans:
        crossing[a - lo] += 1
        crossing[b - lo + 1] -= 1
    for k in range(1, len(crossing)):
        crossing[k] += crossing[k - 1]
    runs, run = [], []
    for k in range(1, hi - lo):
        if crossing[k] <= limit:
            run.append(k)
        elif run:
            runs.append(run)
            run = []
    runs += [run] if run else []
    out = []
    typical = sorted(crossing[1:hi - lo])[(hi - lo) // 2] if hi - lo > 1 else 0          # what a place inside a drawing is crossed by
    for r in runs:
        k = min(r, key=lambda k: crossing[k])
        if crossing[k] > cfg_share * typical:
            continue
        before = [it for it, (a, b) in zip(items, spans) if (a + b) / 2 <= lo + k]
        out.append((crossing[k], before, [it for it in items if all(it is not x for x in before)], len(r)))
    return out


def _cut(items, cell: float, size: Tuple[float, float], cfg) -> List[list]:
    """Strokes that touch can still be two views (the plans of a sheet are drawn close together): they are taken apart where fewest strokes cross, if that leaves a view on each side."""
    if len(items) < cfg["cut_min_items"]:                                  # a small drawing is not a row of views: it is not cut
        return [items]
    limit = max(cfg["cut_cross"], int(cfg["cut_cross_share"] * len(items)))
    cuts = sorted(_valleys(items, 0, limit, cfg["cut_valley"]) + _valleys(items, 1, limit, cfg["cut_valley"]), key=lambda c: (c[0], -c[3]))
    for _, a, b, _ in cuts:
        if a and b and _is_view(a, cell, size, cfg) and _is_view(b, cell, size, cfg):
            return _cut(a, cell, size, cfg) + _cut(b, cell, size, cfg)
    return [items]


def _give_texts(views: List[View], prims: Primitives, size: Tuple[float, float], cfg) -> None:
    """Each view gets the texts around it (in the frame of the sheet, to find its title) and the texts inside it (in its own frame, for the annotations)."""
    for v in views:
        v.texts = [t for t in prims.texts if _near(t, v.box, cfg["label_reach"], size)]
        v.prims.texts = [Text(t.value, _shift(t.at, v.box[0], v.box[1]), t.height) for t in prims.texts if _inside(t.at, v.box)]


def split(prims: Primitives, size: Tuple[float, float]) -> List[View]:
    """The views of a sheet, left to right and top to bottom, without its frame and title block. Empty when the file is one drawing (nothing to take apart)."""
    cfg = PARAMS["sheet"]
    cell = max(size) / cfg["cells"]
    items = _items(prims, cell)
    if not items:
        return []
    label = _labels([c for _, _, cells in items for c in cells], cfg["link_cells"])
    of, boxes = _group_boxes(items, label, cell)
    counts: Dict[int, int] = {}
    for g in of.values():
        counts[g] = counts.get(g, 0) + 1
    groups, framed = _without_frame(_significant(boxes, counts, size, cfg), boxes, size, cfg)
    pieces = [piece for g in groups for piece in _cut([it for it in items if of[(it[0], it[1])] == g], cell, size, cfg)]
    out = []
    for piece in pieces:
        box = _snap(_cell_box(piece, cell), prims.ink_scale if prims.ink is not None else 1.0)
        out.append(View(box, _view_prims(prims, {(k, i) for k, i, _ in piece}, box), len(piece)))
    row = lambda v: round((v.box[1] + v.box[3]) / 2 / (cfg["row_share"] * max(size)))      # noqa: E731
    out.sort(key=lambda v: (row(v), v.box[0]))
    _give_texts(out, prims, size, cfg)
    titled = sum(1 for v in out if named(v.texts, v.box))
    return out if framed or titled >= 2 else []                      # strokes that merely do not touch (a flat cut by the gaps of its door and window) are not views: a sheet has a frame or titles its plans


def _near(t: Text, box: Box, reach: List[float], size: Tuple[float, float]) -> bool:
    """A text close to a view (its title sits under or over it): within `reach` of the sheet's side beyond its box."""
    r = reach[0] * max(size)
    return box[0] - r <= t.at[0] <= box[2] + r and box[1] - r <= t.at[1] <= box[3] + reach[1] * max(size)
