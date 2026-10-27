"""Doors, windows and plain openings. A wall that stops and starts again leaves a gap; what lies in the gap says what it is: the swing of a leaf is a door, thin lines across it are a window,
nothing is just an opening. A door whose arc is drawn without a gap in the wall, and the blocks the drawing names as doors or windows, are found too."""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from epc_arch.geometry import angle_gap, arc_point, arc_span, axis_of, dist_point_line, dist_point_segment, seg_angle, seg_length
from epc_arch.model import Arc, Block, Line, Opening, Primitives, Wall
from epc_arch.recognizers import Context

Pt = Tuple[float, float]


@dataclass(frozen=True)
class Gap:
    at: Pt
    width: float
    theta: float
    offset: float
    t0: float
    t1: float
    wall: str


def _wall_axis(w: Wall):
    theta = seg_angle(w.a, w.b)
    ax = axis_of(theta)
    t0, t1 = sorted((ax.t(w.a), ax.t(w.b)))
    return theta, ax, ax.o(w.a), t0, t1


def _collinear_groups(walls: List[Wall], T: float, tol: float) -> List[List[Wall]]:
    groups: List[List[Wall]] = []
    for w in walls:
        theta, _, off, _, _ = _wall_axis(w)
        for g in groups:
            t2, _, o2, _, _ = _wall_axis(g[0])
            if angle_gap(theta, t2) <= tol and abs(off - o2) <= 0.5 * T:
                g.append(w)
                break
        else:
            groups.append([w])
    return groups


def opening_range(T: float, ctx: Context) -> Tuple[float, float]:
    if ctx.scale.known:
        return ctx.scale.opening_width
    lo, hi = ctx.params["relative"]["opening_width_in_walls"]
    return lo * T, hi * T


def door_range(T: float, ctx: Context) -> Tuple[float, float]:
    if ctx.scale.known:
        return ctx.scale.door_radius
    lo, hi = ctx.params["relative"]["door_radius_in_walls"]
    return lo * T, hi * T


def find_gaps(walls: List[Wall], T: float, ctx: Context) -> List[Gap]:
    """Where a line of wall stops and starts again a door's width further on."""
    lo, hi = opening_range(T, ctx)
    out: List[Gap] = []
    for g in _collinear_groups(walls, T, ctx.params["walls"]["angle_tolerance_deg"]):
        theta, ax, off, _, _ = _wall_axis(g[0])
        spans = sorted(((_wall_axis(w)[3], _wall_axis(w)[4], w.id) for w in g))
        for (_, e0, wid), (s1, _, _) in zip(spans, spans[1:]):
            if lo <= s1 - e0 <= hi:
                out.append(Gap(ax.at((e0 + s1) / 2, off), s1 - e0, theta, off, e0, s1, wid))
    return out


class LineIndex:
    """The end points of the strokes by place, to ask which strokes end near a point without reading them all."""

    def __init__(self, lines: List[Line], cell: float):
        self.cell = max(cell, 1e-6)
        self._grid: Dict[Tuple[int, int], List[Line]] = {}
        for l in lines:
            for p in (l.a, l.b):
                self._grid.setdefault((int(p[0] // self.cell), int(p[1] // self.cell)), []).append(l)

    def near(self, p: Pt, reach: float) -> List[Line]:
        span = int(reach // self.cell) + 1
        cx, cy = int(p[0] // self.cell), int(p[1] // self.cell)
        return [l for dx in range(-span, span + 1) for dy in range(-span, span + 1) for l in self._grid.get((cx + dx, cy + dy), [])]


def _ends(a: Arc) -> Tuple[Pt, Pt]:
    return arc_point(a.c, a.r, a.start), arc_point(a.c, a.r, a.end)


def _leaf(a: Arc, index: LineIndex, cfg: dict) -> Optional[Pt]:
    """The end of the arc where the leaf is drawn: a stroke from the hinge to that end, as long as the radius."""
    tol = cfg["leaf_match"] * a.r
    for end in _ends(a):
        for l in index.near(a.c, tol):
            for p, q in ((l.a, l.b), (l.b, l.a)):
                if math.hypot(p[0] - a.c[0], p[1] - a.c[1]) <= tol and abs(seg_length(p, q) - a.r) <= 2 * tol and math.hypot(q[0] - end[0], q[1] - end[1]) <= 2 * tol:
                    return end
    return None


def _nearest_wall(p: Pt, walls: List[Wall], reach: float) -> Optional[Wall]:
    best = min(walls, key=lambda w: dist_point_segment(p, w.a, w.b), default=None)
    return best if best is not None and dist_point_segment(p, best.a, best.b) <= reach else None


def _door_from_arc(a: Arc, walls: List[Wall], index: LineIndex, T: float, ctx: Context) -> Opening:
    cfg, conf = ctx.params["doors"], ctx.params["confidence"]
    e0, e1 = _ends(a)
    wall = _nearest_wall(a.c, walls, 1.2 * T)
    on_wall = min((e0, e1), key=lambda e: dist_point_line(e, wall.a, wall.b) if wall else 0.0)       # the end that lies along the wall: the other one is in the room
    leaf = _leaf(a, index, cfg)
    at = ((a.c[0] + on_wall[0]) / 2, (a.c[1] + on_wall[1]) / 2)
    angle = seg_angle(wall.a, wall.b) if wall else seg_angle(a.c, on_wall)
    reason = "arc and leaf" if leaf else "arc"
    return Opening("", "door", at, a.r, angle, wall.id if wall else "", conf["door_arc_gap_leaf"] if leaf else conf["door_arc_only"], reason, hinge=a.c, swing=on_wall if on_wall != leaf else None)


def door_arcs(prims: Primitives, T: float, ctx: Context) -> List[Arc]:
    lo, hi = door_range(T, ctx)
    smin, smax = ctx.params["doors"]["arc_span_deg"]
    return [a for a in prims.arcs if smin <= arc_span(a.start, a.end) <= smax and lo <= a.r <= hi and ctx.hints.of(a.layer) != "wall"]


def _match_gap(door: Opening, gaps: List[Gap], used: set, cfg: dict) -> Optional[int]:
    best, where = None, 0.0
    for i, g in enumerate(gaps):
        near = math.hypot(g.at[0] - door.at[0], g.at[1] - door.at[1])
        if i not in used and abs(g.width - door.width) <= cfg["gap_match"] * door.width and near <= 0.6 * door.width and (best is None or near < where):
            best, where = i, near
    return best


def _window_evidence(g: Gap, lines: List[Line], T: float, ctx: Context) -> int:
    """How many distinct thin strokes cross the gap along the wall: the panes and sill of a window."""
    cfg = ctx.params["windows"]
    ax = axis_of(g.theta)
    seen: List[float] = []
    for l in lines:
        if angle_gap(seg_angle(l.a, l.b), g.theta) > ctx.params["walls"]["angle_tolerance_deg"] * 2:
            continue
        t0, t1 = sorted((ax.t(l.a), ax.t(l.b)))
        o = ax.o(((l.a[0] + l.b[0]) / 2, (l.a[1] + l.b[1]) / 2))
        covers = min(t1, g.t1) - max(t0, g.t0) >= cfg["cover"] * g.width
        if covers and abs(o - g.offset) <= cfg["offset_factor"] * T and not any(abs(o - s) < T / 8 for s in seen):
            seen.append(o)
    return len(seen)


def _opening_from_gap(g: Gap, lines: List[Line], T: float, ctx: Context) -> Opening:
    conf, cfg = ctx.params["confidence"], ctx.params["windows"]
    n = _window_evidence(g, lines, T, ctx)
    if n >= cfg["min_lines"]:
        return Opening("", "window", g.at, g.width, g.theta, g.wall, conf["window_lines"], f"{n} lines across the gap")
    if n == 1:
        return Opening("", "window", g.at, g.width, g.theta, g.wall, conf["window_one_line"], "1 line across the gap")
    return Opening("", "opening", g.at, g.width, g.theta, g.wall, conf["opening_gap"], "gap in the wall")


def _from_gap_with_door(door: Opening, g: Gap) -> Opening:
    conf_wall = g.wall or door.wall
    return Opening("", "door", g.at, g.width, g.theta, conf_wall, min(0.95, door.confidence + 0.1), door.reason + " in a gap", hinge=door.hinge, swing=door.swing)


def _from_block(b: Block, kind: str, walls: List[Wall], T: float, ctx: Context) -> Opening:
    conf = ctx.params["confidence"]
    lo, hi = door_range(T, ctx) if kind == "door" else opening_range(T, ctx)
    wall = _nearest_wall(b.at, walls, 1.5 * T)
    width = b.width if lo <= b.width <= hi * 2 else lo * (1.0 if kind == "door" else 1.5)
    return Opening("", kind, b.at, width, seg_angle(wall.a, wall.b) if wall else b.rotation % 180.0, wall.id if wall else "", conf["door_block"], f"block {b.name}")


def _dedupe(found: List[Opening], T: float, ctx: Context) -> List[Opening]:
    """Two findings at the same place are one: the more confident stays, a door or window wins over a plain opening."""
    reach = ctx.params["dedupe"]["opening_distance_factor"]
    rank = {"door": 2, "window": 2, "opening": 1}
    kept: List[Opening] = []
    for o in sorted(found, key=lambda o: (-rank[o.kind], -o.confidence)):
        if not any(math.hypot(o.at[0] - k.at[0], o.at[1] - k.at[1]) <= reach * max(o.width, k.width) for k in kept):
            kept.append(o)
    return kept


def _number(found: List[Opening], T: float) -> List[Opening]:
    prefix = {"door": "d", "window": "v", "opening": "o"}
    count = {k: 0 for k in prefix}
    out = []
    for o in sorted(found, key=lambda o: (round(o.at[1] / T), o.at[0])):
        count[o.kind] += 1
        out.append(Opening(f"{prefix[o.kind]}{count[o.kind]}", o.kind, o.at, o.width, o.angle, o.wall, o.confidence, o.reason, o.hinge, o.swing))
    return out


def recognize_openings(prims: Primitives, walls: List[Wall], T: float, ctx: Context) -> List[Opening]:
    gaps = find_gaps(walls, T, ctx)
    index = LineIndex(prims.lines, T)
    doors = [_door_from_arc(a, walls, index, T, ctx) for a in door_arcs(prims, T, ctx)]
    used: set = set()
    found: List[Opening] = []
    for d in doors:
        i = _match_gap(d, gaps, used, ctx.params["doors"])
        if i is None:
            found.append(d)
        else:
            used.add(i)
            found.append(_from_gap_with_door(d, gaps[i]))
    found += [_opening_from_gap(g, prims.lines, T, ctx) for i, g in enumerate(gaps) if i not in used]
    found += [_from_block(b, kind, walls, T, ctx) for b in prims.blocks for kind in [ctx.hints.of(b.name)] if kind in ("door", "window")]
    return _number(_dedupe(found, T, ctx), T)
