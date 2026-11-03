"""Walls. Two strategies look for a wall candidate (a stretch with a thickness) in the strokes: a thick stroke is a wall drawn as a band; two parallel strokes close together are a wall drawn as two
lines. The thickness the candidates agree on is the thickness of the walls of this plan (`calibrate`); candidates of that thickness are merged into walls."""
import math
from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple

from epc_arch.geometry import Axis, angle_gap, axis_of, seg_angle, seg_length, segment_distance
from epc_arch.model import Line, Primitives, Wall
from epc_arch.recognizers import Context
from epc_arch.recognizers.tidy import tidy_walls

Pt = Tuple[float, float]
MAX_STRIPS = 20000
MAX_PAIRS_PER_STRIP = 40


@dataclass(frozen=True)
class Candidate:
    theta: float
    offset: float
    t0: float
    t1: float
    thickness: float
    weight: float
    reason: str


class Strategy(Protocol):
    name: str

    def candidates(self, lines: List[Line], ctx: Context) -> List[Candidate]: ...


def _strip(line: Line, axis: Axis) -> Tuple[float, float, float]:
    """Where a stroke sits in the frame of a direction: its offset across and its interval along."""
    mid = ((line.a[0] + line.b[0]) / 2, (line.a[1] + line.b[1]) / 2)
    t0, t1 = sorted((axis.t(line.a), axis.t(line.b)))
    return axis.o(mid), t0, t1


class ThickStrokes:
    """A stroke as thick as a wall is a wall: how a filled band, or a polyline with width, is drawn."""
    name = "thick"

    def candidates(self, lines: List[Line], ctx: Context) -> List[Candidate]:
        lo, hi = ctx.scale.wall_thickness
        lo = max(lo, ctx.params["walls"]["thick_stroke_min_factor"] * max(ctx.size))
        out = []
        for l in lines:
            if lo <= l.width <= hi and seg_length(l.a, l.b) >= ctx.params["relative"]["min_wall_length_factor"] * l.width:
                theta = seg_angle(l.a, l.b)
                axis = axis_of(theta)
                o, t0, t1 = _strip(l, axis)
                out.append(Candidate(theta, o, t0, t1, l.width, t1 - t0, self.name))
        return out


def _buckets(lines: List[Line], tol: float) -> List[List[Tuple[float, Line]]]:
    """Strokes grouped by direction (within `tol` degrees): a bucket holds the strokes that can be the two sides of one wall."""
    marked = sorted(((seg_angle(l.a, l.b), l) for l in lines), key=lambda x: x[0])
    marked = [((t - 180.0) if t > 180.0 - tol else t, l) for t, l in marked]
    marked.sort(key=lambda x: x[0])
    out: List[List[Tuple[float, Line]]] = []
    for t, l in marked:
        if out and t - out[-1][0][0] <= tol:
            out[-1].append((t, l))
        else:
            out.append([(t, l)])
    return out


def _pairs(bucket: List[Tuple[float, Line]], lo: float, hi: float, min_overlap: float, reason: str) -> List[Candidate]:
    theta = (sum(t for t, _ in bucket) / len(bucket)) % 180.0
    axis = axis_of(theta)
    strips = sorted((_strip(l, axis) for _, l in bucket), key=lambda s: s[0])
    out: List[Candidate] = []
    for i, (o1, a0, a1) in enumerate(strips):
        taken = 0
        for o2, b0, b1 in strips[i + 1:]:
            d = o2 - o1
            if d > hi or taken >= MAX_PAIRS_PER_STRIP:
                break
            lap = min(a1, b1) - max(a0, b0)
            if d >= lo and lap >= min_overlap * d:
                out.append(Candidate(theta, (o1 + o2) / 2, max(a0, b0), min(a1, b1), d, lap, reason))
                taken += 1
    return out


class ParallelPairs:
    """Two strokes side by side, as far apart as a wall is thick and overlapping along a good stretch, are the two faces of a wall."""
    name = "pair"

    def candidates(self, lines: List[Line], ctx: Context) -> List[Candidate]:
        lo, hi = ctx.scale.wall_thickness
        cfg = ctx.params["walls"]
        longest = sorted(lines, key=lambda l: -seg_length(l.a, l.b))[:MAX_STRIPS]
        out: List[Candidate] = []
        for bucket in _buckets([l for l in longest if seg_length(l.a, l.b) >= cfg["min_overlap_factor"] * lo], cfg["angle_tolerance_deg"]):
            out += _pairs(bucket, lo, hi, cfg["min_overlap_factor"], self.name)
        return out


STRATEGIES: List[Strategy] = [ThickStrokes(), ParallelPairs()]


def _bin(thickness: float, lo: float, k: float, bins: int) -> int:
    """The bin of a thickness in a histogram that is finer for thin walls (logarithmic: a wall is thick or thin in proportion)."""
    return min(bins - 1, max(0, int(math.log(max(thickness, lo) / lo) * k)))


def _peak(cands: List[Candidate], lo: float, k: float, bins: int) -> Tuple[int, float]:
    """The bin where the candidates put most ink (their length times their thickness, counting a little of the neighbours), and how much. Dimension lines, ticks, trees and lettering are strokes too,
    but thin: weighing by thickness as well as by length lets a wall outweigh them even when there is less of it."""
    weight = [0.0] * bins
    for c in cands:
        weight[_bin(c.thickness, lo, k, bins)] += c.weight
    smooth = [weight[i] + 0.5 * (weight[i - 1] if i else 0.0) + 0.5 * (weight[i + 1] if i + 1 < bins else 0.0) for i in range(bins)]
    area = [smooth[i] * lo * math.exp((i + 0.5) / k) for i in range(bins)]                 # length times thickness: the ink a thickness puts on the page, which favours walls over fine lines
    best = max(range(bins), key=lambda i: area[i])
    return best, area[best]


def calibrate(cands: List[Candidate], ctx: Context) -> Optional[float]:
    """The thickness most of the candidates agree on (weighted by their length), or None when nothing stands out: a plan with no walls drawn as walls."""
    lo, hi = ctx.scale.wall_thickness
    bins = ctx.params["walls"]["bins"]
    if not cands or hi <= lo:
        return None
    k = bins / math.log(hi / lo)
    peak, _ = _peak(cands, lo, k, bins)
    near = [c for c in cands if abs(_bin(c.thickness, lo, k, bins) - peak) <= 1]
    if len(near) < ctx.params["walls"]["min_votes"]:
        return None
    return sum(c.thickness * c.weight for c in near) / sum(c.weight for c in near)


def _cluster(cands: List[Candidate], tol_theta: float, tol_offset: float) -> List[List[Candidate]]:
    """Candidates of the same line of wall (same direction, same offset), to be merged into stretches."""
    groups: List[List[Candidate]] = []
    for c in sorted(cands, key=lambda c: (c.theta, c.offset)):
        for g in groups:
            if angle_gap(g[0].theta, c.theta) <= tol_theta and abs(g[0].offset - c.offset) <= tol_offset:
                g.append(c)
                break
        else:
            groups.append([c])
    return groups


def _merge(group: List[Candidate], gap: float) -> List[Tuple[float, float, float, float]]:
    """Intervals of one line of wall that touch or nearly touch become one: (theta, offset, t0, t1, thickness)."""
    theta = sum(c.theta for c in group) / len(group)
    offset = sum(c.offset for c in group) / len(group)
    out: List[List[float]] = []
    for c in sorted(group, key=lambda c: c.t0):
        if out and c.t0 - out[-1][1] <= gap:
            out[-1][1] = max(out[-1][1], c.t1)
            out[-1][2] += c.thickness * (c.t1 - c.t0)
            out[-1][3] += c.t1 - c.t0
        else:
            out.append([c.t0, c.t1, c.thickness * (c.t1 - c.t0), c.t1 - c.t0])
    return [(theta, offset, o[0], o[1], o[2] / o[3]) for o in out]  # type: ignore[misc]


def _confidence(cands: List[Candidate], length: float, T: float, ctx: Context) -> float:
    conf = ctx.params["confidence"]
    base = max(conf["wall_pair"] if c.reason == "pair" else conf["wall_thick"] for c in cands)
    return min(0.95, base + min(0.2, length / (60.0 * T)))


def build_walls(cands: List[Candidate], T: float, ctx: Context, tolerance: Optional[Tuple[float, float]] = None) -> List[Wall]:
    """Candidates of the thickness the plan agreed on, merged along their lines into walls with a centre line, a thickness and a confidence."""
    cfg = ctx.params["walls"]
    lo, hi = tolerance or cfg["thickness_tolerance"]
    kept = [c for c in cands if lo * T <= c.thickness <= hi * T]
    walls: List[Wall] = []
    for group in _cluster(kept, cfg["angle_tolerance_deg"], 0.5 * T):
        for theta, offset, t0, t1, thick in _merge(group, cfg["merge_gap_factor"] * T):
            if t1 - t0 < ctx.params["relative"]["min_wall_length_factor"] * min(T, thick):
                continue
            ax = axis_of(theta)
            walls.append(Wall("", ax.at(t0, offset), ax.at(t1, offset), thick, _confidence(group, t1 - t0, T, ctx), "+".join(sorted({c.reason for c in group}))))
    walls.sort(key=lambda w: (round(w.a[1] / T), w.a[0]))
    return [Wall(f"w{i + 1}", w.a, w.b, w.thickness, w.confidence, w.reason) for i, w in enumerate(walls)]


def _components(walls: List[Wall], reach: float, bridge: float = 0.0, tol: float = 1.5) -> List[List[int]]:
    """Walls that touch (or nearly) one another, as groups of indices: the walls of a building form one network. Walls in line with a gap of up to `bridge` between them belong together too: the gap is
    a door or a window."""
    parent = list(range(len(walls)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    boxes = [(min(w.a[0], w.b[0]) - reach, min(w.a[1], w.b[1]) - reach, max(w.a[0], w.b[0]) + reach, max(w.a[1], w.b[1]) + reach) for w in walls]
    order = sorted(range(len(walls)), key=lambda i: boxes[i][0])
    for k, i in enumerate(order):
        for j in order[k + 1:]:
            if boxes[j][0] > boxes[i][2]:
                break
            if boxes[j][1] > boxes[i][3] or boxes[j][3] < boxes[i][1] or find(i) == find(j):
                continue
            if segment_distance(walls[i].a, walls[i].b, walls[j].a, walls[j].b) <= reach:
                parent[find(i)] = find(j)
    if bridge:
        for i in range(len(walls)):
            ai = axis_of(seg_angle(walls[i].a, walls[i].b))
            ti = sorted((ai.t(walls[i].a), ai.t(walls[i].b)))
            for j in range(i + 1, len(walls)):
                if find(i) == find(j) or angle_gap(seg_angle(walls[i].a, walls[i].b), seg_angle(walls[j].a, walls[j].b)) > tol or abs(ai.o(walls[i].a) - ai.o(walls[j].a)) > 0.5 * reach:
                    continue
                tj = sorted((ai.t(walls[j].a), ai.t(walls[j].b)))
                if max(ti[0], tj[0]) - min(ti[1], tj[1]) <= bridge:
                    parent[find(i)] = find(j)
    groups: dict = {}
    for i in range(len(walls)):
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def drop_stray(walls: List[Wall], T: float, ctx: Context) -> List[Wall]:
    """Dimension lines, frames and lettering leave strokes that look like walls but touch nothing: a group of walls much smaller than the main building is left out."""
    cfg = ctx.params["walls"]
    if len(walls) < 4:
        return walls
    groups = _components(walls, cfg["touch_factor"] * T, ctx.params["relative"]["opening_width_in_walls"][1] * T, cfg["angle_tolerance_deg"])
    size = [sum(seg_length(walls[i].a, walls[i].b) for i in g) for g in groups]
    biggest = max(size)
    keep = {i for g, s in zip(groups, size) if s >= cfg["stray_share"] * biggest for i in g}
    return [w for i, w in enumerate(walls) if i in keep]


def usable_lines(prims: Primitives, ctx: Context) -> Tuple[List[Line], bool]:
    """The strokes a wall can be made of: those of layers named as walls when there are any, else all but those named as doors or windows. The flag says a layer vouched for them."""
    named = [l for l in prims.lines if ctx.hints.of(l.layer) == "wall"]
    if named:
        return named, True
    return [l for l in prims.lines if ctx.hints.of(l.layer) not in ("door", "window")], False


def _ink(found: List[Candidate], ctx: Context) -> float:
    """How strongly the candidates agree on one thickness: the ink of their best thickness (see `_peak`)."""
    lo, hi = ctx.scale.wall_thickness
    if not found or hi <= lo:
        return 0.0
    k = ctx.params["walls"]["bins"] / math.log(hi / lo)
    return _peak(found, lo, k, ctx.params["walls"]["bins"])[1]


def strongest(lines: List[Line], ctx: Context) -> List[Candidate]:
    """The candidates of the strategy whose thickness stands out most. A wall drawn as a band is surer than two strokes that happen to be a wall's thickness apart (the panes of a window are),
    so a band wins unless the pairs put clearly more ink on one thickness: a plan whose walls are filled shapes has thick outlines that are no bands, and its pairs are the walls."""
    votes, sure = ctx.params["walls"]["min_votes"], ctx.params["walls"]["pairs_win"]
    found = [(s, s.candidates(lines, ctx)) for s in STRATEGIES]
    found = [(s, c) for s, c in found if len(c) >= votes]
    if not found:
        return []
    first = found[0]
    best = max(found, key=lambda x: _ink(x[1], ctx))
    return best[1] if best is not first and _ink(best[1], ctx) >= sure * _ink(first[1], ctx) else first[1]


def _covered(c: Candidate, same: List[Candidate]) -> float:
    """The share of a candidate's length that the candidates on its line already draw."""
    done, end = 0.0, c.t0
    for p in sorted(same, key=lambda p: p.t0):
        lo, hi = max(p.t0, c.t0, end), min(p.t1, c.t1)
        if hi > lo:
            done += hi - lo
            end = hi
    return done / max(c.t1 - c.t0, 1e-9)


def _new_lines(extra: List[Candidate], primary: List[Candidate], T: float, ctx: Context) -> List[Candidate]:
    """Of what another strategy found, what is not inside a wall the first one already drew: on a line where it found walls, a stretch lying between them is a gap (the panes of a window are two
    strokes a wall's thickness apart and would close it); a stretch that goes beyond them, mostly lies where they are not, or is on a line where it found nothing, is another wall."""
    tol = ctx.params["walls"]["angle_tolerance_deg"]
    out = []
    for c in extra:
        same = [p for p in primary if angle_gap(p.theta, c.theta) <= tol and abs(p.offset - c.offset) <= 0.5 * T]
        if same and c.t0 >= min(p.t0 for p in same) - T and c.t1 <= max(p.t1 for p in same) + T and _covered(c, same) < 0.5:
            continue
        out.append(c)
    return out


def recognize_walls(prims: Primitives, ctx: Context) -> Tuple[List[Wall], Optional[float], bool]:
    lines, vouched = usable_lines(prims, ctx)
    cands = strongest(lines, ctx)
    T = calibrate(cands, ctx)
    if T is None:
        return [], None, vouched
    # A plan often draws some walls as bands (interior, solid) and others as two lines (exterior, hollow): once the thickness is known, every strategy contributes the stretches of that thickness.
    wide = tuple(ctx.params["walls"]["band_tolerance"]) if vouched else None      # walls a layer or a picture vouches for keep their own thickness: the outer wall is thicker than the inner ones
    if wide is not None and prims.ink is None:
        # A drawing's wall layer: the walls of the plan's thickness first, then thinner or thicker ones (a partition, a party wall) where they do not lie in the line of those
        # (two lines a little apart in the gap of a wall are the panes of a window).
        lo, hi = ctx.params["walls"]["thickness_tolerance"]
        primary = [c for c in cands if lo * T <= c.thickness <= hi * T]
        cands = primary + _new_lines([c for c in cands if not lo * T <= c.thickness <= hi * T], primary, T, ctx)
    if wide is None:
        first = cands[0].reason if cands else ""
        primary = cands
        for strategy in STRATEGIES:
            if strategy.name != first:
                cands = cands + _new_lines([c for c in strategy.candidates(lines, ctx) if abs(c.thickness - T) <= 0.35 * T], primary, T, ctx)
    walls = drop_stray(tidy_walls(drop_stray(build_walls(cands, T, ctx, wide), T, ctx), T, ctx), T, ctx)
    return [Wall(f"w{i + 1}", w.a, w.b, w.thickness, w.confidence, w.reason) for i, w in enumerate(walls)], T, vouched
