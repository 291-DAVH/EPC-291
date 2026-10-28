"""Distribution of the luminaires: a uniform grid parallel to the room axes.

UPV lumen-method article, step 3: rows across the width N_w = sqrt(N * a / b),
columns along the length N_l = N_w * b / a, wall distance = half the spacing,
and spacing e <= ratio * h. Rounding to the nearest integer can leave the grid
short of the required count, so it is grown until it holds at least N.
"""
import math
from itertools import count
from typing import Any, Dict, Iterator, List, Optional, Tuple

from epc_lighting.config import PARAMS, data
from epc_lighting.model import Estimate, Luminaire, Options, Room, rnd


def _half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def grid_counts(n_total: int, width_m: float, length_m: float) -> Tuple[int, int]:
    """(rows across the width, columns along the length), holding at least n_total."""
    rows_exact = math.sqrt(n_total * width_m / length_m)
    rows = max(1, _half_up(rows_exact))
    cols = max(1, _half_up(rows_exact * length_m / width_m))
    while rows * cols < n_total:
        rows, cols = _grow(rows, cols, n_total, width_m, length_m)
    return rows, cols


def _grow(rows: int, cols: int, n_total: int, width_m: float, length_m: float) -> Tuple[int, int]:
    """Add one row or one column: the cheapest grid that holds n_total, else the axis with the wider spacing."""
    candidates = [(rows + 1, cols), (rows, cols + 1)]
    holding = [c for c in candidates if c[0] * c[1] >= n_total]
    if holding:
        return min(holding, key=lambda c: (c[0] * c[1], -max(width_m / c[0], length_m / c[1])))
    return candidates[0] if width_m / rows >= length_m / cols else candidates[1]


def spacing_ratio(room: Room, lum: Luminaire, options: Options) -> Estimate:
    """Maximum spacing as a multiple of h: the luminaire's own value, else the chosen basis."""
    if lum.spacing_ratio is not None:
        return Estimate(lum.spacing_ratio, f"declared by luminaire '{lum.id}'", 1.0)
    if options.spacing_basis == "distribution":
        system_id = lum.distribution or room.system
        ratio = data("lighting_systems")["systems"][system_id]["spacing_ratio"]
        if ratio is not None:
            return Estimate(ratio, f"UNAC 2.6, {system_id} lighting", 0.9)
    return _by_height(room.height_m)


def _by_height(height_m: float) -> Estimate:
    for entry in sorted(data("spacing")["by_room_height"], key=lambda e: -e["height_over_m"]):
        if height_m > entry["height_over_m"] or entry["height_over_m"] == 0:
            return Estimate(entry["ratio"], f"UPV table 7, {entry['label']['en']}, room height {height_m} m", 0.9)
    raise AssertionError("spacing.json has no class for height 0")  # pragma: no cover


def check_axis(count_: int, dimension_m: float, h: float, ratio: float) -> Dict[str, Any]:
    """Compare the spacing along one axis with the maximum."""
    if count_ < 2:
        return {"checked": False, "reason": "a single luminaire on this axis: no spacing to check (UNAC 2.6)"}
    spacing = dimension_m / count_
    limit = ratio * h
    tolerance = PARAMS["spacing"]["tolerance"]
    if spacing <= limit * (1 + 1e-9):
        status = "ok"
    elif spacing <= limit * (1 + tolerance):
        status = "within_tolerance"
    else:
        status = "exceeds"
    return {"checked": True, "spacing_m": rnd(spacing), "max_spacing_m": rnd(limit), "ratio_used": rnd(spacing / h), "status": status}


def _status(count_: int, dimension_m: float, h: float, ratio: float) -> str:
    return check_axis(count_, dimension_m, h, ratio).get("status", "n/a")


def _enforce(rows: int, cols: int, room: Room, h: float, ratio: float) -> Tuple[int, int]:
    for _ in range(PARAMS["spacing"]["enforce_max_steps"]):
        bad_rows = _status(rows, room.width_m, h, ratio) == "exceeds"
        bad_cols = _status(cols, room.length_m, h, ratio) == "exceeds"
        if not (bad_rows or bad_cols):
            break
        rows += 1 if bad_rows else 0
        cols += 1 if bad_cols else 0
    return rows, cols


def _spacing_warning(axis_name: str, check: Dict[str, Any], ratio: Estimate) -> Optional[str]:
    if check.get("status") == "exceeds":
        return (
            f"spacing along the {axis_name} ({check['spacing_m']} m) exceeds the maximum {check['max_spacing_m']} m "
            f"({ratio.value} x h): the light will not be uniform; use less powerful lamps, more luminaires or luminaires "
            f"with fewer lamps (or set enforce_spacing)"
        )
    if check.get("status") == "within_tolerance":
        return (
            f"spacing along the {axis_name} ({check['spacing_m']} m) is above the maximum {check['max_spacing_m']} m "
            f"({ratio.value} x h) but within the {int(PARAMS['spacing']['tolerance'] * 100)}% tolerance "
            f"(the UPV article accepts 3 m against 2.8 m); acceptable"
        )
    return None


def _positions(rows: int, cols: int, room: Room, z: float, tags: Iterator[int]) -> List[Dict[str, Any]]:
    dx, dy = room.length_m / cols, room.width_m / rows
    return [
        {"tag": f"LU-{next(tags):03d}", "x_m": rnd((i + 0.5) * dx), "y_m": rnd((j + 0.5) * dy), "z_m": rnd(z)}
        for j in range(rows)
        for i in range(cols)
    ]


def plan(room: Room, lum: Luminaire, n_required: int, h: float, options: Options, tags: Iterator[int], warnings: List[str]) -> Dict[str, Any]:
    """The grid for the room, its spacing checks and the position of every luminaire."""
    rows, cols = grid_counts(n_required, room.width_m, room.length_m)
    ratio = spacing_ratio(room, lum, options)
    if options.enforce_spacing:
        rows, cols = _enforce(rows, cols, room, h, ratio.value)
    along_length = check_axis(cols, room.length_m, h, ratio.value)
    across_width = check_axis(rows, room.width_m, h, ratio.value)
    for name, check in (("length", along_length), ("width", across_width)):
        text = _spacing_warning(name, check, ratio)
        if text:
            warnings.append(text)
    return {
        "rows_across_width": rows,
        "columns_along_length": cols,
        "installed": rows * cols,
        "required": n_required,
        "spacing_x_m": rnd(room.length_m / cols),
        "spacing_y_m": rnd(room.width_m / rows),
        "wall_distance_x_m": rnd(room.length_m / cols / 2),
        "wall_distance_y_m": rnd(room.width_m / rows / 2),
        "max_spacing": ratio.as_dict(),
        "spacing_check": {"along_length": along_length, "across_width": across_width},
        "positions": _positions(rows, cols, room, room.work_plane_m + h, tags),
    }


def new_tag_counter() -> Iterator[int]:
    return count(1)
