"""Coefficient of utilisation: how it is read from a manufacturer table, or given.

The tables come from the luminaire maker, indexed by room index k (or by cavity
ratio RCR = 5 / k) and by the reflectances of ceiling, walls and floor. The
lookup interpolates linearly along the axis and, between reflectance columns,
by inverse-distance weighting. It never extrapolates: outside the table it
keeps the nearest row and says so.
"""
import math
from bisect import bisect_right
from typing import Dict, List, Sequence, Tuple

from epc_lighting.config import PARAMS
from epc_lighting.tables import generic_table
from epc_lighting.model import CuTable, Estimate, Luminaire, Room

Reflectances = Tuple[float, float, float]


def _interp(xs: Sequence[float], ys: Sequence[float], x: float) -> float:
    if len(xs) == 1 or x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    i = bisect_right(xs, x) - 1
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[i] + t * (ys[i + 1] - ys[i])


def _column_values(table: CuTable, axis_value: float) -> List[float]:
    columns = range(len(table.columns))
    return [_interp(table.axis_values, [row[j] for row in table.values], axis_value) for j in columns]


def _distance2(a: Reflectances, b: Reflectances) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _on_node(table: CuTable, axis_value: float) -> bool:
    return any(abs(axis_value - v) < 1e-9 for v in table.axis_values)


def lookup(table: CuTable, axis_value: float, reflectances: Reflectances) -> Tuple[float, str]:
    """(cu, kind) with kind one of table_exact, table_interpolated_axis,
    table_interpolated_reflectance, table_out_of_range."""
    lo, hi = table.axis_values[0], table.axis_values[-1]
    out_of_range = axis_value < lo - 1e-9 or axis_value > hi + 1e-9
    per_column = _column_values(table, axis_value)
    tolerance = PARAMS["cu"]["exact_match_tolerance"]
    distances = [math.sqrt(_distance2(col, reflectances)) for col in table.columns]
    nearest = min(range(len(distances)), key=lambda j: distances[j])
    if distances[nearest] <= tolerance:
        value, kind = per_column[nearest], ("table_exact" if _on_node(table, axis_value) else "table_interpolated_axis")
    else:
        value, kind = _idw(table, per_column, reflectances), "table_interpolated_reflectance"
    return value, ("table_out_of_range" if out_of_range else kind)


def _idw(table: CuTable, per_column: Sequence[float], reflectances: Reflectances) -> float:
    power = PARAMS["cu"]["idw_power"]
    weights = [1.0 / (_distance2(col, reflectances) ** (power / 2)) for col in table.columns]
    return sum(w * v for w, v in zip(weights, per_column)) / sum(weights)


def _describe(kind: str, axis: str, axis_value: float, refl: Reflectances) -> str:
    where = f"{axis} = {axis_value:.3f}, ceiling/walls/floor = {refl[0]:.3f}/{refl[1]:.3f}/{refl[2]:.3f}"
    phrases = {
        "table_exact": "read directly from the table",
        "table_interpolated_axis": f"interpolated along {axis} in the table",
        "table_interpolated_reflectance": "interpolated between reflectance columns of the table (inverse-distance weighting)",
        "table_out_of_range": f"{axis} is outside the table: the nearest row is kept, nothing is extrapolated",
    }
    return f"{phrases[kind]} ({where})"


def resolve(room: Room, lum: Luminaire, axes: Dict[str, float], refl: Reflectances, warnings: List[str]) -> Estimate:
    """The CU for this room: room override, luminaire value, luminaire table, then the generic table."""
    confidence = PARAMS["cu"]["confidence"]
    if room.cu is not None:
        estimate = Estimate(room.cu, "given in the room (project or manufacturer value)", confidence["given"])
    elif lum.cu is not None:
        estimate = Estimate(lum.cu, f"given with luminaire '{lum.id}'", confidence["given"])
    elif lum.cu_table is not None:
        estimate = _from_table(lum.cu_table, axes, refl, confidence)
    else:
        estimate = _from_generic(lum, axes, refl, confidence, warnings)
    if estimate.value > PARAMS["cu"]["warn_above"]:
        warnings.append(
            f"CU = {round(estimate.value, 3)} is above 1: the table is normalised to something other than lamp flux "
            f"(some manufacturers do); confirm it with the manufacturer's data"
        )
    return estimate


def _from_table(table: CuTable, axes: Dict[str, float], refl: Reflectances, confidence: Dict[str, float]) -> Estimate:
    value, kind = lookup(table, axes[table.axis], refl)
    return Estimate(value, _describe(kind, table.axis, axes[table.axis], refl), confidence[kind])


def _from_generic(lum: Luminaire, axes: Dict[str, float], refl: Reflectances, confidence: Dict[str, float], warnings: List[str]) -> Estimate:
    table = generic_table()
    value, kind = lookup(table, axes["k"], refl)
    warnings.append(
        f"luminaire '{lum.id}' has no cu or cu_table: an illustrative table from the UPV article was used; "
        f"give the manufacturer's CU table for a reliable result"
    )
    reason = "generic illustrative table, " + _describe(kind, "k", axes["k"], refl)
    return Estimate(value, reason, confidence["generic_table"])
