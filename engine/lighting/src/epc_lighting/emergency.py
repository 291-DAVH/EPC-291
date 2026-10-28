"""Antipanic emergency lighting and escape routes: the smallest regular grid of emergency luminaires that keeps the minimum illuminance and the max/min ratio on the floor.

Ported from `epc_aea90364.lighting` (CAL-001), which this engine replaces. The emergency luminaire is taken as a Lambertian point source (I = I0 cos(theta), I0 = flux / pi) and only the direct
component counts, so the figures are conservative: E = (flux / pi) h^2 / d^4 with d^2 = dx^2 + dy^2 + h^2 on a horizontal plane at the floor. The criteria (0.5 lux, ratio 40) are the usual
antipanic ones as the engineer recalls them: they are given as estimates with low confidence and the document can set its own.
"""
import math
from typing import Any, Dict, Iterator, List, Sequence, Tuple

from epc_lighting.config import PARAMS
from epc_lighting.model import Emergency, Estimate, LightingError, Luminaire, rnd

Point = Tuple[float, float]
_TOL = 1e-9


def lambertian_lux(flux_lm: float, height_m: float, dx_m: float, dy_m: float) -> float:
    """Direct illuminance on a horizontal plane under a Lambertian source `height_m` above it."""
    d2 = dx_m * dx_m + dy_m * dy_m + height_m * height_m
    return (flux_lm / math.pi) * (height_m * height_m) / (d2 * d2)


def grid_positions(length_m: float, width_m: float, columns: int, rows: int) -> List[Point]:
    """Centre of every cell of a grid of `columns` along the length and `rows` across the width."""
    return [((i + 0.5) * length_m / columns, (j + 0.5) * width_m / rows) for i in range(columns) for j in range(rows)]


def illuminance_at(positions: Sequence[Point], flux_lm: float, height_m: float, x_m: float, y_m: float) -> float:
    return sum(lambertian_lux(flux_lm, height_m, x_m - px, y_m - py) for px, py in positions)


def evaluate(length_m: float, width_m: float, positions: Sequence[Point], flux_lm: float, height_m: float, band_m: float, step_m: float) -> Dict[str, float]:
    """Illuminance on a grid of points over the floor, leaving out a band along the walls: lowest, average and highest lux, and the ratio between the highest and the lowest."""
    if band_m < 0:
        raise LightingError("the band left out along the walls cannot be negative")
    if 2 * band_m >= length_m or 2 * band_m >= width_m:
        raise LightingError("the band left out along the walls takes the whole room: make it smaller")
    nx = int(math.floor((length_m - 2 * band_m) / step_m + _TOL)) + 1
    ny = int(math.floor((width_m - 2 * band_m) / step_m + _TOL)) + 1
    values = [illuminance_at(positions, flux_lm, height_m, band_m + i * step_m, band_m + j * step_m) for i in range(nx) for j in range(ny)]
    low, high = min(values), max(values)
    return {"e_min": low, "e_avg": sum(values) / len(values), "e_max": high, "max_over_min": high / low if low > 0 else math.inf, "points": len(values)}


def _grids(count: int, length_m: float, width_m: float, spacing_ratio_max: float) -> Iterator[Tuple[int, int]]:
    """The grids of exactly `count` luminaires whose two spacings differ by no more than the ratio."""
    for columns in range(1, count + 1):
        if count % columns:
            continue
        rows = count // columns
        sx, sy = length_m / columns, width_m / rows
        if max(sx, sy) / min(sx, sy) <= spacing_ratio_max + _TOL:
            yield columns, rows


def size_antipanic(length_m: float, width_m: float, height_m: float, flux_lm: float, e_min_lux: float, ratio_max: float, band_m: float, step_m: float, n_max: int,
                   spacing_ratio_max: float) -> Dict[str, Any]:
    """The fewest luminaires, on a regular grid, with the lowest lux at least `e_min_lux` and the highest over the lowest at most `ratio_max`; None when no grid of up to `n_max` does."""
    for count in range(1, n_max + 1):
        for columns, rows in _grids(count, length_m, width_m, spacing_ratio_max):
            positions = grid_positions(length_m, width_m, columns, rows)
            found = evaluate(length_m, width_m, positions, flux_lm, height_m, band_m, step_m)
            if found["e_min"] >= e_min_lux and found["max_over_min"] <= ratio_max:
                return {"count": count, "columns": columns, "rows": rows, "positions": positions, **found}
    return {}


def route_axis(positions: Sequence[Point], flux_lm: float, height_m: float, start: Point, end: Point, step_m: float) -> Dict[str, float]:
    """Illuminance along the axis of an escape route (a segment from `start` to `end`, the end included): lowest, average and highest lux."""
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length <= 0:
        raise LightingError("the axis of an escape route has no length: give two different points")
    n = int(math.floor(length / step_m + _TOL)) + 1
    along = [(start[0] + (end[0] - start[0]) * k * step_m / length, start[1] + (end[1] - start[1]) * k * step_m / length) for k in range(n)]
    if length - (n - 1) * step_m > _TOL:
        along.append(end)
    values = [illuminance_at(positions, flux_lm, height_m, x, y) for x, y in along]
    return {"e_min": min(values), "e_avg": sum(values) / len(values), "e_max": max(values), "points": len(values)}


def _criterion(given, default_key: str, label: str) -> Estimate:
    if given is not None:
        return Estimate(given, "given in the document", 1.0)
    return Estimate(PARAMS["emergency"][default_key], f"usual antipanic {label} (as recalled, EN 1838): confirm it with the project standard", 0.5)


def _route(route, positions: Sequence[Point], flux_lm: float, height_m: float, step_m: float, default_min: float) -> Dict[str, Any]:
    found = route_axis(positions, flux_lm, height_m, route.start, route.end, step_m)
    required = route.e_min_lux if route.e_min_lux is not None else default_min
    return {"id": route.id, "points": found["points"], "min_lux": rnd(found["e_min"]), "average_lux": rnd(found["e_avg"]), "max_lux": rnd(found["e_max"]),
            "target_min_lux": rnd(required), "complies": found["e_min"] >= required - _TOL}


def _layout(found: Dict[str, Any], height_m: float, tags: Iterator[int]) -> Dict[str, Any]:
    return {"installed": found.get("count", 0), "columns_along_length": found.get("columns", 0), "rows_across_width": found.get("rows", 0),
            "positions": [{"tag": f"LE-{next(tags):03d}", "x_m": rnd(x), "y_m": rnd(y), "z_m": rnd(height_m)} for x, y in found.get("positions", [])]}


def calculate(item: Emergency, lum: Luminaire, tags: Iterator[int], warnings: List[str]) -> Dict[str, Any]:
    """Size the antipanic grid of one room and check its escape routes. A room where no grid meets the criteria is reported as not complying, with the warning that says what to change."""
    e_min = _criterion(item.e_min_lux, "antipanic_e_min_lux", "minimum illuminance")
    ratio = _criterion(item.ratio_max, "antipanic_max_over_min", "max/min ratio")
    band, step = (item.band_m if item.band_m is not None else PARAMS["emergency"]["band_m"]), (item.step_m or PARAMS["emergency"]["step_m"])
    maintenance = item.maintenance if item.maintenance is not None else PARAMS["emergency"]["maintenance"]
    flux = lum.flux_lm * lum.efficiency * maintenance
    found = size_antipanic(item.length_m, item.width_m, item.height_m, flux, e_min.value, ratio.value, band, step, PARAMS["emergency"]["n_max"], PARAMS["emergency"]["spacing_ratio_max"])
    if not found:
        warnings.append(f"no grid of up to {PARAMS['emergency']['n_max']} luminaires gives {e_min.value} lux at least with a ratio of {ratio.value} at most: use a luminaire with more flux, or check the height and the criteria")
    lay = _layout(found, item.height_m, tags)
    routes = [_route(r, found["positions"], flux, item.height_m, step, e_min.value) for r in item.routes] if found else []
    return {"id": item.id, "name": item.name, "method": "antipanic grid", "luminaire": {"id": lum.id, "name": lum.name, "flux_lm": rnd(lum.flux_lm)},
            "criteria": {"min_lux": e_min.as_dict(), "max_over_min": ratio.as_dict()}, "layout": lay,
            "verification": {"min_lux": rnd(found["e_min"]), "average_lux": rnd(found["e_avg"]), "max_lux": rnd(found["e_max"]), "max_over_min": rnd(found["max_over_min"]), "complies": True}
            if found else {"complies": False},
            "routes": routes, "energy": {"installed_power_w": rnd(lum.power_w * lay["installed"]) if lum.power_w is not None else None}}
