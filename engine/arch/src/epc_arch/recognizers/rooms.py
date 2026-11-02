"""Rooms. A form appears when lines close a space: the walls, with their doors and windows shut, close the rooms of the plan. The walls are drawn on a grid, the openings closed across, the
outside flooded from the edge, and what stays dry are the rooms, each with its area and a place to write it."""
import math
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from epc_arch.geometry import axis_of
from epc_arch.model import Opening, Room, Wall
from epc_arch.recognizers import Context
from epc_arch.recognizers.openings import find_gaps

Pt = Tuple[float, float]
WALL, OUTSIDE = 255, 254


def _quad(a: Pt, b: Pt, half: float, ext: float) -> List[Pt]:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    a = (a[0] - ux * ext, a[1] - uy * ext)
    b = (b[0] + ux * ext, b[1] + uy * ext)
    ox, oy = -uy * half, ux * half
    return [(a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy), (b[0] - ox, b[1] - oy), (a[0] - ox, a[1] - oy)]


def _rects(mask: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """The cells of a room as rectangles (x0, y0, x1, y1), rows with the same runs merged: drawn together they are the room."""
    out: List[List[int]] = []
    open_: dict = {}
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            open_ = {}
            continue
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        runs = list(zip(np.nonzero(d == 1)[0].tolist(), np.nonzero(d == -1)[0].tolist()))
        nxt = {}
        for s, e in runs:
            r = open_.get((s, e))
            if r is None:
                r = [s, y, e, y + 1]
                out.append(r)
            else:
                r[3] = y + 1
            nxt[(s, e)] = r
        open_ = nxt
    return [tuple(r) for r in out]                                            # type: ignore[misc]


def _label_point(mask: np.ndarray) -> Tuple[int, int]:
    """A cell well inside the room for its label: the one farthest from the room's edge along its row and column."""
    ys, xs = np.nonzero(mask)
    cy, cx = int(np.median(ys)), int(np.median(xs))
    if mask[cy, cx]:
        return cx, cy
    i = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2))
    return int(xs[i]), int(ys[i])


def recognize_rooms(walls: List[Wall], openings: List[Opening], T: float, size: Tuple[float, float], units_per_metre: Optional[float], ctx: Context) -> List[Room]:
    if len(walls) < 3:
        return []
    cfg = ctx.params["rooms"]
    xs = [c for w in walls for c in (w.a[0], w.b[0])]
    ys = [c for w in walls for c in (w.a[1], w.b[1])]
    pad = (cfg["close_gap_in_walls"] + 3) * T                                 # room around the walls so the outside is one piece all round
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    cell = max(T / 3, max(x1 - x0, y1 - y0) / cfg["max_cells"])
    W, H = int((x1 - x0) / cell) + 2, int((y1 - y0) / cell) + 2
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    g = lambda p: ((p[0] - x0) / cell, (p[1] - y0) / cell)                    # noqa: E731
    for w in walls:
        d.polygon([g(p) for p in _quad(w.a, w.b, max(w.thickness, T) / 2, 0.6 * T)], fill=WALL)
    shut = [(o.at, o.angle, o.width) for o in openings] + [(gp.at, gp.theta, gp.width) for gp in find_gaps(walls, T, ctx)]
    for at, angle, width in shut:                                             # a door, a window or any gap a wall leaves, shut: the room is closed there
        ax = axis_of(angle)
        a = (at[0] - ax.ux * width / 2, at[1] - ax.uy * width / 2)
        b = (at[0] + ax.ux * width / 2, at[1] + ax.uy * width / 2)
        d.polygon([g(p) for p in _quad(a, b, T / 2, 0.6 * T)], fill=WALL)
    k = 2 * int(round(cfg["close_gap_in_walls"] * T / cell / 2)) + 1          # a wall that stops just short of another still closes the room: gaps this wide are shut
    img = img.filter(ImageFilter.MaxFilter(k)).filter(ImageFilter.MinFilter(k))
    grid = np.array(img)
    grid[0, :] = grid[-1, :] = 0
    grid[:, 0] = grid[:, -1] = 0                                              # the edge of the grid is outside, whatever the filters did there
    img = Image.fromarray(grid).copy()                                       # its own pixels: an image over a numpy buffer cannot be filled
    ImageDraw.floodfill(img, (0, 0), OUTSIDE)
    grid = np.array(img)
    rooms: List[Room] = []
    min_area = cfg["min_area_m2"] * units_per_metre ** 2 if units_per_metre else (cfg["min_side_in_walls"] * T) ** 2
    label = 1
    while label < 250:
        free = np.argwhere(grid == 0)
        if not len(free):
            break
        y, x = free[0]
        work = Image.fromarray(grid).copy()
        ImageDraw.floodfill(work, (int(x), int(y)), label)
        grid = np.array(work)
        mask = grid == label
        label += 1
        area = float(mask.sum()) * cell * cell
        if area < min_area:
            continue
        lx, ly = _label_point(mask)
        rects = [(x0 + a * cell, y0 + b * cell, x0 + c * cell, y0 + e * cell) for a, b, c, e in _rects(mask)]
        at = (x0 + (lx + 0.5) * cell, y0 + (ly + 0.5) * cell)
        rooms.append(Room("", area, area / units_per_metre ** 2 if units_per_metre else None, at, rects))
    rooms.sort(key=lambda r: (round(r.at[1] / (4 * T)), r.at[0]))
    return [Room(f"r{i + 1}", r.area, r.area_m2, r.at, r.rects) for i, r in enumerate(rooms)]
