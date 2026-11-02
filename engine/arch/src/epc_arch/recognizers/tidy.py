"""Tidying the walls into a network. What the strokes give is a heap of stretches that are almost aligned, almost in line and almost touching. A plan is not that: its walls run along two
directions, the walls of one line share one axis, the thickness is one, and each wall ends in another wall. This step brings the stretches to that, so corners and T joins close and the drawing is clean."""
from typing import Dict, List, Optional, Tuple

from epc_arch.geometry import angle_gap, axis_of, seg_angle, seg_length
from epc_arch.model import Wall
from epc_arch.recognizers import Context

# A stretch while it is tidied: [theta, offset, t0, t1, thickness, confidence, reasons]
Item = List


def _dominant(walls: List[Wall]) -> Optional[float]:
    """The direction most of the length of the walls runs along (1 degree bins), the one the drawing is aligned to."""
    weight: Dict[int, float] = {}
    for w in walls:
        k = int(round(seg_angle(w.a, w.b))) % 180
        weight[k] = weight.get(k, 0.0) + seg_length(w.a, w.b)
    if not weight:
        return None
    smooth = {k: sum(weight.get((k + d) % 180, 0.0) for d in (-1, 0, 1)) for k in weight}
    best = max(smooth, key=lambda k: smooth[k])
    near = [(k, weight[k]) for k in weight if angle_gap(k, best) <= 2]
    return sum(k * v for k, v in near) / sum(v for _, v in near) if near else float(best)


def _snapped(w: Wall, axes: List[float], tol: float) -> Item:
    """The wall on the axis nearest to its own direction when that is within `tol` degrees."""
    theta = seg_angle(w.a, w.b)
    best = min(axes, key=lambda a: angle_gap(a, theta))
    if angle_gap(best, theta) <= tol:
        theta = best
    ax = axis_of(theta)
    mid = ((w.a[0] + w.b[0]) / 2, (w.a[1] + w.b[1]) / 2)
    t0, t1 = sorted((ax.t(w.a), ax.t(w.b)))
    return [theta, ax.o(mid), t0, t1, w.thickness, w.confidence, {r for r in w.reason.split("+")}]


def _share_axes(items: List[Item], tol: float) -> None:
    """Walls of one direction whose axes are within `tol` of each other get the same axis (the length-weighted mean), so a line of wall is a line."""
    items.sort(key=lambda i: (round(i[0], 3), i[1]))
    group: List[Item] = []

    def close() -> None:
        if group:
            total = sum(i[3] - i[2] for i in group) or 1.0
            mean = sum(i[1] * (i[3] - i[2]) for i in group) / total
            for i in group:
                i[1] = mean
            group.clear()

    for it in items:
        if group and (angle_gap(group[-1][0], it[0]) > 1e-6 or it[1] - group[-1][1] > tol):
            close()
        group.append(it)
    close()


def _merge_line(items: List[Item], gap: float) -> List[Item]:
    """Stretches on one axis that overlap or nearly touch are one."""
    out: List[Item] = []
    for it in sorted(items, key=lambda i: (round(i[0], 3), round(i[1], 3), i[2])):
        last = out[-1] if out else None
        if last and angle_gap(last[0], it[0]) < 1e-6 and abs(last[1] - it[1]) < 1e-6 and it[2] - last[3] <= gap:
            la, lb = last[3] - last[2], it[3] - it[2]
            last[4] = (last[4] * la + it[4] * lb) / ((la + lb) or 1.0)
            last[3] = max(last[3], it[3])
            last[5] = max(last[5], it[5])
            last[6] = last[6] | it[6]
        else:
            out.append(list(it))
    return out


def _close_joins(items: List[Item], T: float) -> None:
    """Each end of a wall that stops short of (or runs a little past) another wall across it is brought to that wall's axis, so the corner or the T closes."""
    reach = 1.5 * T
    for it in items:
        ax = axis_of(it[0])
        for end in (2, 3):
            t_end = it[end]
            best: Optional[Tuple[float, float]] = None
            for ot in items:
                if ot is it or angle_gap(ot[0], it[0]) < 60.0:
                    continue
                bx = axis_of(ot[0])
                p = ax.at(t_end, it[1])
                den = ax.ux * bx.nx + ax.uy * bx.ny                    # how fast the position across the other wall changes as we move along this one
                if abs(den) < 1e-9:
                    continue
                t_hit = t_end + (ot[1] - bx.o(p)) / den
                s_hit = bx.t(ax.at(t_hit, it[1]))
                if ot[2] - reach <= s_hit <= ot[3] + reach and abs(t_hit - t_end) <= reach and (best is None or abs(t_hit - t_end) < best[0]):
                    best = (abs(t_hit - t_end), t_hit)
            if best is not None:
                it[end] = best[1]


def tidy_walls(walls: List[Wall], T: float, ctx: Context) -> List[Wall]:
    """The walls on two directions, on shared axes, with one thickness, merged along their lines and joined at their ends."""
    cfg = ctx.params["walls"]
    d = _dominant(walls)
    if d is None or len(walls) < 2:
        return walls
    axes = [d % 180.0, (d + 90.0) % 180.0]
    items = [_snapped(w, axes, cfg["axis_snap_deg"]) for w in walls]
    _share_axes(items, 0.5 * T)
    merged = _merge_line(items, cfg["merge_gap_factor"] * T)
    _close_joins(merged, T)
    out = []
    for theta, off, t0, t1, thick, conf, reasons in merged:
        if t1 - t0 < ctx.params["relative"]["min_wall_length_factor"] * min(T, thick):         # a stub beside a door is short: measured by its own thickness
            continue
        ax = axis_of(theta)
        out.append(Wall("", ax.at(t0, off), ax.at(t1, off), T if abs(thick - T) <= 0.2 * T else thick, conf, "+".join(sorted(reasons))))
    out.sort(key=lambda w: (round(w.a[1] / T), w.a[0]))
    return [Wall(f"w{i + 1}", w.a, w.b, w.thickness, w.confidence, w.reason) for i, w in enumerate(out)]
