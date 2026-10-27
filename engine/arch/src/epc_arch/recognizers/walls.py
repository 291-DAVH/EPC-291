"""Walls. Two strategies look for a wall candidate (a stretch with a thickness) in the strokes: a thick stroke is a wall drawn as a band; two parallel strokes close together are a wall drawn as two
lines. The thickness the candidates agree on is the thickness of the walls of this plan (`calibrate`); candidates of that thickness are merged into walls."""
import math
from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple

from epc_arch.geometry import Axis, angle_gap, axis_of, seg_angle, seg_length
from epc_arch.model import Line, Primitives, Wall
from epc_arch.recognizers import Context

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


def calibrate(cands: List[Candidate], ctx: Context) -> Optional[float]:
    """The thickness most of the candidates agree on (weighted by their length), or None when nothing stands out: a plan with no walls drawn as walls."""
    lo, hi = ctx.scale.wall_thickness
    bins = ctx.params["walls"]["bins"]
    if not cands or hi <= lo:
        return None
    k = bins / math.log(hi / lo)
    weight = [0.0] * bins
    count = [0] * bins
    for c in cands:
        b = min(bins - 1, max(0, int(math.log(max(c.thickness, lo) / lo) * k)))
        weight[b] += c.weight
        count[b] += 1
    smooth = [weight[i] + 0.5 * (weight[i - 1] if i else 0.0) + 0.5 * (weight[i + 1] if i + 1 < bins else 0.0) for i in range(bins)]
    peak = max(range(bins), key=lambda i: smooth[i])
    near = [c for c in cands if abs(int(math.log(max(c.thickness, lo) / lo) * k) - peak) <= 1]
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


def build_walls(cands: List[Candidate], T: float, ctx: Context) -> List[Wall]:
    """Candidates of the thickness the plan agreed on, merged along their lines into walls with a centre line, a thickness and a confidence."""
    cfg = ctx.params["walls"]
    lo, hi = cfg["thickness_tolerance"]
    kept = [c for c in cands if lo * T <= c.thickness <= hi * T]
    walls: List[Wall] = []
    for group in _cluster(kept, cfg["angle_tolerance_deg"], 0.5 * T):
        for theta, offset, t0, t1, thick in _merge(group, cfg["merge_gap_factor"] * T):
            if t1 - t0 < ctx.params["relative"]["min_wall_length_factor"] * T:
                continue
            ax = axis_of(theta)
            walls.append(Wall("", ax.at(t0, offset), ax.at(t1, offset), thick, _confidence(group, t1 - t0, T, ctx), "+".join(sorted({c.reason for c in group}))))
    walls.sort(key=lambda w: (round(w.a[1] / T), w.a[0]))
    return [Wall(f"w{i + 1}", w.a, w.b, w.thickness, w.confidence, w.reason) for i, w in enumerate(walls)]


def usable_lines(prims: Primitives, ctx: Context) -> Tuple[List[Line], bool]:
    """The strokes a wall can be made of: those of layers named as walls when there are any, else all but those named as doors or windows. The flag says a layer vouched for them."""
    named = [l for l in prims.lines if ctx.hints.of(l.layer) == "wall"]
    if named:
        return named, True
    return [l for l in prims.lines if ctx.hints.of(l.layer) not in ("door", "window")], False


def strongest(lines: List[Line], ctx: Context) -> List[Candidate]:
    """The candidates of the first strategy that has enough of them. A wall drawn as a band is surer than two strokes that happen to be a wall's thickness apart (the panes of a window are), so
    the pairs are looked for only when there are not enough bands."""
    for strategy in STRATEGIES:
        found = strategy.candidates(lines, ctx)
        if len(found) >= ctx.params["walls"]["min_votes"]:
            return found
    return []


def recognize_walls(prims: Primitives, ctx: Context) -> Tuple[List[Wall], Optional[float], bool]:
    lines, vouched = usable_lines(prims, ctx)
    cands = strongest(lines, ctx)
    T = calibrate(cands, ctx)
    if T is None:
        return [], None, vouched
    return build_walls(cands, T, ctx), T, vouched
