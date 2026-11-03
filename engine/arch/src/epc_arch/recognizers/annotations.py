"""What a plan carries that is not the building: grid axes with their bubbles, dimension lines with their ticks and figures, and labels (names of rooms, tags of doors, windows and walls, with the box round
them and the leader to the element). They are not walls, but they are not rubbish either: they are set apart in layers of their own (`axes`, `dimensions`, `labels`), so that the architecture is seen
with them and every other discipline sees only the walls, doors and windows. What is left is what the recognizers of walls and openings read.

Each kind is found by what it is, not by how it looks: axes are chains of dashes along one line with no wall face beside them; a dimension line is crossed by oblique ticks; a bubble is a circle
with a short text; a label is a text, the small box round it and the short leader that goes from it to the element. Nothing is taken that is long enough to be a wall."""
import math
import re
from collections import defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from epc_arch.config import PARAMS
from epc_arch.geometry import angle_gap, arc_point, dist_point_segment, seg_angle, seg_length
from epc_arch.model import Arc, Line, Marks, Primitives, Text

Pt = Tuple[float, float]
KINDS = ("axes", "dimensions", "labels")
NUMBER = re.compile(r"^[+\-]?\d+([.,]\d+)?\s*(m|cm|mm|%)?$", re.I)


def _orthogonal(l: Line, tol: float = 2.0) -> bool:
    a = seg_angle(l.a, l.b)
    return min(a, abs(a - 90.0), abs(a - 180.0)) <= tol


def _near(p: Pt, q: Pt, eps: float) -> bool:
    return math.hypot(p[0] - q[0], p[1] - q[1]) <= eps


class _Grid:
    """The lines by place, to ask which are near a point or a box without looking at all of them."""

    def __init__(self, lines: List[Line], cell: float):
        self.cell, self.lines = cell, lines
        self.cells: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for i, l in enumerate(lines):
            for c in self._cells(min(l.a[0], l.b[0]), min(l.a[1], l.b[1]), max(l.a[0], l.b[0]), max(l.a[1], l.b[1])):
                self.cells[c].append(i)

    def _cells(self, x0: float, y0: float, x1: float, y1: float) -> Iterable[Tuple[int, int]]:
        k = self.cell
        return ((x, y) for x in range(int(x0 // k), int(x1 // k) + 1) for y in range(int(y0 // k), int(y1 // k) + 1))

    def around(self, x0: float, y0: float, x1: float, y1: float) -> Set[int]:
        return {i for c in self._cells(x0, y0, x1, y1) for i in self.cells.get(c, ())}

    def at(self, p: Pt, r: float) -> Set[int]:
        return {i for i in self.around(p[0] - r, p[1] - r, p[0] + r, p[1] + r) if dist_point_segment(p, self.lines[i].a, self.lines[i].b) <= r}


class Sketch:
    """The primitives of a plan while they are being sorted: which line, arc or text belongs to which kind of annotation."""

    def __init__(self, prims: Primitives, size: Tuple[float, float]):
        self.prims = prims
        self.side = max(size)
        self.eps = max(self.side * PARAMS["annotations"]["touch"], 1e-6)
        self.grid = _Grid(prims.lines, 8 * self.eps)
        self.lines: Dict[int, str] = {}
        self.arcs: Dict[int, str] = {}
        self.texts: Dict[int, str] = {}

    def length(self, i: int) -> float:
        return seg_length(self.prims.lines[i].a, self.prims.lines[i].b)

    def free(self, i: int) -> bool:
        return i not in self.lines

    def take(self, kind: str, lines: Iterable[int] = (), arcs: Iterable[int] = (), texts: Iterable[int] = ()) -> None:
        for i in lines:
            self.lines.setdefault(i, kind)
        for i in arcs:
            self.arcs.setdefault(i, kind)
        for i in texts:
            self.texts.setdefault(i, kind)

    def has_partner(self, i: int) -> bool:
        """A line with another beside it, parallel, about a wall's thickness away and alongside it for at least half its length, is the face of a wall."""
        l = self.prims.lines[i]
        ang, reach = seg_angle(l.a, l.b), 0.012 * self.side
        mid = ((l.a[0] + l.b[0]) / 2, (l.a[1] + l.b[1]) / 2)
        for j in self.grid.around(mid[0] - reach - self.length(i), mid[1] - reach - self.length(i), mid[0] + reach + self.length(i), mid[1] + reach + self.length(i)):
            o = self.prims.lines[j]
            if j != i and angle_gap(ang, seg_angle(o.a, o.b)) < 2.0 and 0.4 * self.eps < dist_point_segment(mid, o.a, o.b) <= reach and _alongside(l, o) >= 0.5 * self.length(i):
                return True
        return False


def _alongside(l: Line, o: Line) -> float:
    """How far two parallel lines run side by side."""
    ux, uy = l.b[0] - l.a[0], l.b[1] - l.a[1]
    n = math.hypot(ux, uy) or 1e-9
    ux, uy = ux / n, uy / n
    t = sorted((l.a[0] * ux + l.a[1] * uy, l.b[0] * ux + l.b[1] * uy))
    u = sorted((o.a[0] * ux + o.a[1] * uy, o.b[0] * ux + o.b[1] * uy))
    return max(0.0, min(t[1], u[1]) - max(t[0], u[0]))


# ---------------------------------------------------------------- grid axes
def _chains(s: Sketch) -> List[List[int]]:
    """Lines of one orientation and position, in order along it, with a short gap between each and the next: dashes of one line."""
    cfg = PARAMS["annotations"]
    groups: Dict[Tuple[bool, int], List[int]] = defaultdict(list)
    for i, l in enumerate(s.prims.lines):
        if _orthogonal(l) and s.length(i) <= cfg["dash_max"] * s.side:
            horizontal = abs(l.a[1] - l.b[1]) < abs(l.a[0] - l.b[0])
            groups[(horizontal, round(((l.a[1] + l.b[1]) if horizontal else (l.a[0] + l.b[0])) / 2 / (2 * s.eps)))].append(i)
    out = []
    for (horizontal, _), ids in groups.items():
        k = 0 if horizontal else 1
        ids.sort(key=lambda i: min(s.prims.lines[i].a[k], s.prims.lines[i].b[k]))
        chain = [ids[0]]
        for i in ids[1:]:
            last = s.prims.lines[chain[-1]]
            gap = min(s.prims.lines[i].a[k], s.prims.lines[i].b[k]) - max(last.a[k], last.b[k])
            if gap <= cfg["dash_gap"] * s.side:
                chain.append(i)
                continue
            out.append(chain)
            chain = [i]
        out.append(chain)
    return out


def _caps(s: Sketch, dashes: List[int]) -> List[int]:
    """The tiny strokes that close the ends of a dash drawn as a thin rectangle."""
    out = []
    for i in dashes:
        for end in (s.prims.lines[i].a, s.prims.lines[i].b):
            out += [j for j in s.grid.at(end, 1.5 * s.eps) if j != i and s.free(j) and s.length(j) <= 0.5 * s.eps]
    return out


def axes(s: Sketch) -> None:
    """Dashes strung along one line, with no wall face beside them."""
    for chain in _chains(s):
        dashes = [i for i in chain if not s.has_partner(i)]
        if len(dashes) >= PARAMS["annotations"]["dash_min"]:
            s.take("axes", lines=dashes)
            s.take("axes", lines=_caps(s, dashes))


def _circles(arcs: List[Arc], eps: float) -> List[List[int]]:
    """Arcs that share a centre and a radius and together close a circle (a bubble is drawn as four quarter circles)."""
    groups: Dict[Tuple[int, int, int], List[int]] = defaultdict(list)
    for i, a in enumerate(arcs):
        groups[(round(a.c[0] / (2 * eps)), round(a.c[1] / (2 * eps)), round(a.r / (2 * eps)))].append(i)
    return [ids for ids in groups.values() if sum((arcs[i].end - arcs[i].start) % 360.0 or 360.0 for i in ids) >= 340.0]


def _inside(t: Text, c: Pt, r: float) -> bool:
    return math.hypot(t.at[0] - c[0], t.at[1] - c[1]) <= r * 1.2


def bubbles(s: Sketch) -> None:
    """Circles with a short text inside (a letter or a number): the bubbles of the grid. A circle with a longer text is the tag of a door or a wall, a label."""
    cfg = PARAMS["annotations"]
    for ids in _circles(s.prims.arcs, s.eps):
        a = s.prims.arcs[ids[0]]
        if a.r > cfg["bubble_max"] * s.side:
            continue
        inside = [k for k, t in enumerate(s.prims.texts) if _inside(t, a.c, a.r)]
        if inside:
            s.take("axes" if all(len(s.prims.texts[k].value) <= 2 for k in inside) else "labels", arcs=ids, texts=inside)


# ---------------------------------------------------------------- dimensions
def _crossing_ticks(s: Sketch, i: int, ticks: Set[int]) -> List[Pt]:
    """Where oblique short strokes cross line `i` from one side to the other."""
    l = s.prims.lines[i]
    out = []
    for j in s.grid.around(min(l.a[0], l.b[0]) - s.eps, min(l.a[1], l.b[1]) - s.eps, max(l.a[0], l.b[0]) + s.eps, max(l.a[1], l.b[1]) + s.eps) & ticks:
        t = s.prims.lines[j]
        da, db = _side(l, t.a), _side(l, t.b)
        if da * db < 0 and abs(da) > s.eps * 0.3 and abs(db) > s.eps * 0.3 and dist_point_segment(_cross(l, t), l.a, l.b) <= s.eps:
            out.append(_cross(l, t))
    return out


def _side(l: Line, p: Pt) -> float:
    return (l.b[0] - l.a[0]) * (p[1] - l.a[1]) - (l.b[1] - l.a[1]) * (p[0] - l.a[0])


def _cross(l: Line, t: Line) -> Pt:
    da, db = _side(l, t.a), _side(l, t.b)
    f = da / (da - db)
    return (t.a[0] + (t.b[0] - t.a[0]) * f, t.a[1] + (t.b[1] - t.a[1]) * f)


def _horizontal(l: Line) -> bool:
    return abs(l.a[1] - l.b[1]) < abs(l.a[0] - l.b[0])


def _collinear(s: Sketch, i: int, marks: List[Pt]) -> List[int]:
    """The pieces of the dimension line that `i` belongs to: lines on the same line, within the span of its ticks, that are not the face of a wall."""
    l = s.prims.lines[i]
    k = 0 if _horizontal(l) else 1
    lo, hi = min(m[k] for m in marks) - s.eps, max(m[k] for m in marks) + s.eps
    pos = (l.a[1 - k] + l.b[1 - k]) / 2

    def piece(j: int) -> bool:
        o = s.prims.lines[j]
        return (_orthogonal(o) and _horizontal(o) == _horizontal(l) and abs((o.a[1 - k] + o.b[1 - k]) / 2 - pos) <= s.eps
                and max(o.a[k], o.b[k]) >= lo and min(o.a[k], o.b[k]) <= hi and not s.has_partner(j))
    return [j for j in range(len(s.prims.lines)) if piece(j)]


def _dimension(s: Sketch, i: int, ticks: Set[int]) -> None:
    """Line `i`, if it is a dimension line, with its pieces, extension lines, ticks and figures."""
    marks = _crossing_ticks(s, i, ticks)
    if len(marks) < 2:
        return
    pieces = _collinear(s, i, marks) or [i]
    figures = _figures(s, pieces)
    if not figures:                                              # a line with oblique strokes across it and no figure beside it is not a dimension (the arrow of a stair)
        return
    s.take("dimensions", lines=pieces, texts=figures)
    s.take("dimensions", lines=_extensions(s, pieces, marks, ticks))
    s.take("dimensions", lines=[j for j in ticks if any(_near(m, _mid(s.prims.lines[j]), s.eps * 2) for m in marks)])


def dimensions(s: Sketch) -> None:
    """A dimension line is a thin line crossed by oblique ticks at each end of every measure. Its extension lines (square to it, starting at it, free at the other end) and its figures go with it."""
    ticks = {i for i, l in enumerate(s.prims.lines) if not _orthogonal(l, 6.0) and s.length(i) <= PARAMS["annotations"]["tick_max"] * s.side}
    if len(ticks) < 2:
        return
    for i, l in enumerate(s.prims.lines):
        if s.free(i) and _orthogonal(l):
            _dimension(s, i, ticks)


def _mid(l: Line) -> Pt:
    return ((l.a[0] + l.b[0]) / 2, (l.a[1] + l.b[1]) / 2)


def _extensions(s: Sketch, pieces: List[int], marks: List[Pt], ticks: Set[int]) -> List[int]:
    """Lines that meet the dimension line at one of its ticks and square to it, no longer than a fraction of the plan: the extension lines."""
    base = s.prims.lines[pieces[0]]
    ang = seg_angle(base.a, base.b)
    out = []
    for m in marks:
        for j in s.grid.at(m, s.eps * 1.5):
            o = s.prims.lines[j]
            if j not in pieces and j not in ticks and s.free(j) and abs(angle_gap(ang, seg_angle(o.a, o.b)) - 90.0) < 3.0 and s.length(j) <= PARAMS["annotations"]["extension_max"] * s.side and not s.has_partner(j):
                out.append(j)
    return out


def _figures(s: Sketch, pieces: List[int]) -> List[int]:
    """The numbers written along the dimension line."""
    out = []
    for k, t in enumerate(s.prims.texts):
        if k not in s.texts and NUMBER.match(t.value.strip()):
            p = (t.at[0] + len(t.value) * t.height * 0.3, t.at[1] - t.height / 2)
            if any(dist_point_segment(p, s.prims.lines[j].a, s.prims.lines[j].b) <= 2.5 * max(t.height, s.eps) for j in pieces):
                out.append(k)
    return out


# ---------------------------------------------------------------- labels
Node = Tuple[str, int]


def _ends(s: Sketch, node: Node) -> List[Pt]:
    kind, i = node
    if kind == "l":
        return [s.prims.lines[i].a, s.prims.lines[i].b]
    a = s.prims.arcs[i]
    return [arc_point(a.c, a.r, a.start), arc_point(a.c, a.r, a.end)]


class _Groups:
    """Union-find over the strokes: which belong to one group."""

    def __init__(self, nodes: List[Node]):
        self.parent = {n: n for n in nodes}

    def find(self, n: Node) -> Node:
        while self.parent[n] != n:
            self.parent[n] = self.parent[self.parent[n]]
            n = self.parent[n]
        return n

    def join(self, a: Node, b: Node) -> None:
        self.parent[self.find(a)] = self.find(b)

    def groups(self) -> List[List[Node]]:
        out: Dict[Node, List[Node]] = defaultdict(list)
        for n in self.parent:
            out[self.find(n)].append(n)
        return list(out.values())


def _short(s: Sketch, walls_too: bool = False) -> List[Node]:
    """The strokes a tag can be made of: short lines (with no wall face beside them, unless `walls_too`) and arcs."""
    limit = PARAMS["annotations"]["leader_max"] * s.side
    return ([("l", i) for i in range(len(s.prims.lines)) if s.free(i) and s.length(i) <= limit and (walls_too or not s.has_partner(i))]
            + [("a", k) for k in range(len(s.prims.arcs)) if k not in s.arcs])


def _spots(s: Sketch, nodes: List[Node], cell: float):
    """The ends of the strokes by place."""
    spots = defaultdict(list)
    for n in nodes:
        for p in _ends(s, n):
            spots[(int(p[0] // cell), int(p[1] // cell))].append((n, p))
    return spots


def _join_ends(s: Sketch, nodes: List[Node], groups: _Groups) -> None:
    """Strokes that end where another ends."""
    cell = 2 * s.eps
    spots = _spots(s, nodes, cell)
    for (cx, cy), here in spots.items():
        around = [x for dx in (-1, 0, 1) for dy in (-1, 0, 1) for x in spots.get((cx + dx, cy + dy), ())]
        for (n, p), (m, q) in ((a, b) for a in here for b in around):
            if n != m and _near(p, q, 1.5 * s.eps):
                groups.join(n, m)


def _join_sides(s: Sketch, nodes: List[Node], groups: _Groups) -> None:
    """A leader that ends on the side of a box, not at its corner."""
    for kind, i in nodes:
        if kind == "l":
            for end in _ends(s, (kind, i)):
                for j in s.grid.at(end, 1.5 * s.eps):
                    if ("l", j) in groups.parent and j != i:
                        groups.join(("l", i), ("l", j))


def _shapes(s: Sketch, walls_too: bool = False) -> List[List[Node]]:
    """Groups of short strokes (lines and arcs) that touch one another: the box, the hexagon or the circle of a tag with its leader, a mark, a symbol."""
    nodes = _short(s, walls_too)
    groups = _Groups(nodes)
    _join_ends(s, nodes, groups)
    _join_sides(s, nodes, groups)
    return groups.groups()


def _closed(s: Sketch, shape: List[Node]) -> bool:
    """A loop: every stroke ends on another stroke of the group at both ends (the box round a text, never a stretch of wall)."""
    ends = {n: _ends(s, n) for n in shape}
    return all(any(m != n and any(_near(p, q, 1.5 * s.eps) for q in ends[m]) for m in shape) for n in shape for p in ends[n])


def _bbox(s: Sketch, shape: List[Node]) -> Tuple[float, float, float, float]:
    pts = [p for n in shape for p in _ends(s, n)]
    return min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)


def _is_door(s: Sketch, shape: List[Node]) -> bool:
    """A leaf and the quarter circle it sweeps: a door, not a label."""
    return any(n[0] == "a" and 70.0 <= (s.prims.arcs[n[1]].end - s.prims.arcs[n[1]].start) % 360.0 <= 110.0 and s.prims.arcs[n[1]].r >= 0.02 * s.side for n in shape)


def _held(s: Sketch, shape: List[Node], anchors: List[Tuple[int, Pt]]) -> List[int]:
    """The texts that sit inside the box of a group of strokes, when the group can be a label (small, and not a door)."""
    x0, y0, x1, y1 = _bbox(s, shape)
    if max(x1 - x0, y1 - y0) > PARAMS["annotations"]["tag_max"] * s.side or _is_door(s, shape):
        return []
    return [k for k, (px, py) in anchors if x0 - s.eps <= px <= x1 + s.eps and y0 - s.eps <= py <= y1 + s.eps]


def _held(s: Sketch, shape: List[Node], anchors: List[Tuple[int, Pt]]) -> List[int]:
    """The texts that sit inside the box of a group of strokes, when the group can be a label (small, and not a door)."""
    x0, y0, x1, y1 = _bbox(s, shape)
    if max(x1 - x0, y1 - y0) > PARAMS["annotations"]["tag_max"] * s.side or _is_door(s, shape):
        return []
    return [k for k, (px, py) in anchors if x0 - s.eps <= px <= x1 + s.eps and y0 - s.eps <= py <= y1 + s.eps]


def _take_shape(s: Sketch, shape: List[Node], held: List[int]) -> None:
    s.take("labels", lines=[i for kind, i in shape if kind == "l"], arcs=[i for kind, i in shape if kind == "a"], texts=held)


def labels(s: Sketch) -> None:
    """Every text that is not a figure or a bubble is a label, and so is the small group of strokes that holds it: the box, the hexagon or the circle of the tag and the leader to the element.
    A box drawn against a wall has a wall face beside its sides: it is taken too, but only when it is a closed loop."""
    anchors = [(k, (t.at[0] + len(t.value) * t.height * 0.3, t.at[1] - t.height / 2)) for k, t in enumerate(s.prims.texts) if k not in s.texts]
    for shape in _shapes(s):
        held = _held(s, shape, anchors)
        if held:
            _take_shape(s, shape, held)
    for shape in _shapes(s, walls_too=True):
        held = _held(s, shape, anchors) if _closed(s, shape) else []
        if held:
            _take_shape(s, shape, held)
    s.take("labels", texts=[k for k, _ in anchors])


# ---------------------------------------------------------------- the whole
def split(prims: Primitives, size: Tuple[float, float]) -> Tuple[Primitives, Dict[str, Marks]]:
    """The primitives without the annotations, and the annotations by kind. A plan with no lines or no texts to anchor on comes back as it was."""
    if not prims.lines or prims.ink is not None:                       # a picture has no text layer and its strokes are runs of pixels: nothing here to tell
        return prims, {}
    s = Sketch(prims, size)
    axes(s)
    bubbles(s)
    dimensions(s)
    labels(s)
    marks = {k: Marks() for k in KINDS}
    for i, kind in s.lines.items():
        marks[kind].lines.append(prims.lines[i])
    for i, kind in s.arcs.items():
        marks[kind].arcs.append(prims.arcs[i])
    for i, kind in s.texts.items():
        marks[kind].texts.append(prims.texts[i])
    clean = Primitives(**{**prims.__dict__, "lines": [l for i, l in enumerate(prims.lines) if i not in s.lines], "arcs": [a for i, a in enumerate(prims.arcs) if i not in s.arcs],
                          "texts": [t for i, t in enumerate(prims.texts) if i not in s.texts]})
    return clean, marks
