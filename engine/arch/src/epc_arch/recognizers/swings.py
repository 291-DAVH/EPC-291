"""Door swings read from the picture. A raster has no arcs, but a door is always the same shape whatever its size: a leaf square to the wall from a jamb and the quarter circle it sweeps. It
is looked for at every wall end, at every width a door can have, and the ink along that shape says it is a door, which jamb is the hinge and to which side it opens."""
import math

import numpy as np

from epc_arch.geometry import axis_of, seg_angle
from epc_arch.model import Opening, Primitives
from epc_arch.recognizers import Context

SAMPLES = 40


_DILATED: list = []                       # (ink, its dilation): the last picture's, kept while that very array is in use


def _dilated(ink: np.ndarray) -> np.ndarray:
    """The ink grown by two pixels, once per picture: a swing drawn a little off the radius tried is still on it."""
    if _DILATED and _DILATED[0][0] is ink:
        return _DILATED[0][1]
    d = ink.copy()
    for _ in range(2):                                                        # two pixels: the radii are tried a few pixels apart
        e = d.copy()
        e[1:] |= d[:-1]
        e[:-1] |= d[1:]
        e[:, 1:] |= d[:, :-1]
        e[:, :-1] |= d[:, 1:]
        d = e
    _DILATED[:] = [(ink, d)]
    return d


def _hits(mask: np.ndarray, xs: np.ndarray, ys: np.ndarray, scale: float) -> np.ndarray:
    """For each point, whether it falls on ink."""
    h, w = mask.shape
    xi = np.clip(np.round(xs / scale).astype(int), 0, w - 1)
    yi = np.clip(np.round(ys / scale).astype(int), 0, h - 1)
    inside = (xs / scale >= 0) & (xs / scale < w) & (ys / scale >= 0) & (ys / scale < h)
    return mask[yi, xi] & inside


def _share(mask: np.ndarray, xs: np.ndarray, ys: np.ndarray, scale: float) -> np.ndarray:
    """For each row of points (one candidate per row), the share that falls on ink."""
    h, w = mask.shape
    xi = np.clip(np.round(xs / scale).astype(int), 0, w - 1)
    yi = np.clip(np.round(ys / scale).astype(int), 0, h - 1)
    inside = (xs / scale >= 0) & (xs / scale < w) & (ys / scale >= 0) & (ys / scale < h)
    return (mask[yi, xi] & inside).mean(axis=1)


def _segments(walls) -> np.ndarray:
    """The walls as an array of (ax, ay, bx, by, half thickness)."""
    return np.array([(w.a[0], w.a[1], w.b[0], w.b[1], w.thickness / 2) for w in walls], dtype=float)


def _walled(points: np.ndarray, own: int, segs: np.ndarray, T: float) -> np.ndarray:
    """For each point, is it inside a wall other than the one the door hangs from? (A thin line across a doorway, a threshold, is drawn in many plans: only a wall closes it.)"""
    if not len(points):
        return np.zeros(0, dtype=bool)
    ax, ay, bx, by = segs[:, 0], segs[:, 1], segs[:, 2], segs[:, 3]
    dx, dy = bx - ax, by - ay
    n = np.maximum(dx * dx + dy * dy, 1e-12)
    px, py = points[:, 0:1], points[:, 1:2]
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / n, 0.0, 1.0)
    d = np.hypot(px - (ax + t * dx), py - (ay + t * dy))
    reach = 0.9 * np.maximum(segs[:, 4], T / 2)
    hit = d <= reach
    hit[:, own] = False
    return hit.any(axis=1)


def doors_at_wall_ends(prims: Primitives, walls, T: float, ctx: Context):
    """Doors found where they hinge: at the end of a wall. From each end the swing is looked for at every radius a door can have, both ways round, and a door is taken where the quarter
    circle is drawn, the space it sweeps is empty, the arc is a thin line and the doorway where the leaf shuts is not wall."""
    if prims.ink is None or not walls:
        return []
    cfg = ctx.params["swings"]
    mask = _dilated(prims.ink)
    s = prims.ink_scale
    if ctx.scale.known:
        r_lo, r_hi = ctx.scale.door_radius
    else:
        r_lo, r_hi = cfg["min_width_in_walls"] * T, cfg["max_width_in_walls"] * T
    radii = np.exp(np.linspace(math.log(r_lo), math.log(r_hi), cfg["radius_steps"]))
    phis = (np.arange(SAMPLES) + 0.5) / SAMPLES * (math.pi / 2)
    tl = np.linspace(0.15, 0.85, 12)
    found = []
    segs = _segments(walls)
    for wi, w in enumerate(walls):
        ax = axis_of(seg_angle(w.a, w.b))
        t0, t1 = sorted((ax.t(w.a), ax.t(w.b)))
        off = ax.o(w.a)
        for t_end, sign in ((t1, 1.0), (t0, -1.0)):
            out_ = np.array([ax.ux * sign, ax.uy * sign])                      # out of the wall's end, across the doorway
            for far in (False, True):                                          # hinged at this wall's end, or at the far jamb with the leaf shutting back towards it
                u = -out_ if far else out_
                for side_sign in (1.0, -1.0):
                    n = np.array([ax.nx * side_sign, ax.ny * side_sign])     # the side the leaf opens to
                    for shift in (-0.5 * w.thickness, 0.0, 0.5 * w.thickness):            # the jamb is on a face of this wall, or on its axis
                        end = np.array(ax.at(t_end, off + shift))
                        hx = end[0] + (out_[0] * radii if far else 0 * radii)     # one hinge per radius
                        hy = end[1] + (out_[1] * radii if far else 0 * radii)
                        pts = lambda k: (hx[:, None] + (k * radii)[:, None] * (np.cos(phis) * u[0] + np.sin(phis) * n[0]),      # noqa: E731
                                         hy[:, None] + (k * radii)[:, None] * (np.cos(phis) * u[1] + np.sin(phis) * n[1]))
                        hits = _hits(mask, *pts(1.0), s)
                        arc = hits.mean(axis=1)
                        q = max(1, SAMPLES // 5)
                        ends = np.minimum(hits[:, :q].mean(axis=1), hits[:, -q:].mean(axis=1))   # a swing reaches both the jamb and the open leaf, whatever hides its middle
                        ok = (arc >= cfg["min_arc_end"]) & ((arc >= 0.9) | (ends >= cfg["min_arc_ends"]))                                 # a swing drawn whole: looked for everywhere, a partial arc is too often a curve of furniture
                        if not ok.any():
                            continue
                        inside = _share(mask, *pts(0.6), s)
                        ring = np.maximum(_share(mask, *pts(0.75), s), _share(mask, *pts(1.25), s))
                        leaf = _share(mask, hx[:, None] + radii[:, None] * tl * n[0], hy[:, None] + radii[:, None] * tl * n[1], s)
                        good = ok & (inside <= cfg["max_inside"]) & (ring <= cfg["max_inside"]) & (leaf >= cfg["min_leaf"])   # the open leaf is drawn too
                        if good.any():                                                  # the doorway the leaf shuts must not be wall (checked only where all else holds)
                            k = np.nonzero(good)[0]
                            good[k] &= ~_walled(end[None, :] + out_[None, :] * radii[k, None] * 0.5, wi, segs, T)
                        if not good.any():
                            continue
                        score = np.where(good, arc * (0.75 + 0.25 * leaf), 0.0)
                        i = int(np.argmax(score))
                        r = float(radii[i])
                        hinge = (float(hx[i]), float(hy[i]))
                        at = (float(end[0] + out_[0] * r / 2), float(end[1] + out_[1] * r / 2))
                        swing = (hinge[0] + float(n[0]) * r, hinge[1] + float(n[1]) * r)
                        conf = min(0.95, ctx.params["confidence"]["door_arc_only"] + 0.4 * (float(score[i]) - cfg["min_arc_end"]) / (1 - cfg["min_arc_end"]))
                        found.append(Opening("", "door", at, r, seg_angle(w.a, w.b), w.id, round(conf, 2), f"swing at a wall end ({float(score[i]):.2f})", hinge=hinge, swing=swing))
    return found
