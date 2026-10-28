"""Parses the two table-like inputs of a luminaire: the CU table and the photometry.

Kept apart from document.py so cu.py can read the generic table without
importing the document parser.
"""
import math
from functools import lru_cache
from typing import Any, Sequence

from epc_lighting.config import data
from epc_lighting.model import CuTable, LightingError, Photometry


def _fail(path: str, message: str) -> None:
    raise LightingError(f"{path}: {message}")


def _bounds(value: float, path: str, minimum: float | None, maximum: float | None, positive: bool) -> None:
    if positive and value <= 0:
        _fail(path, f"must be greater than 0, got {value}")
    if minimum is not None and value < minimum:
        _fail(path, f"must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        _fail(path, f"must be at most {maximum}, got {value}")


def number(value: Any, path: str, minimum: float | None = None, maximum: float | None = None, positive: bool = False) -> float:
    """A finite number within limits, or an error that says what to correct."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(path, f"must be a number, got {value!r}")
    if not math.isfinite(value):
        _fail(path, "must be a finite number")
    _bounds(value, path, minimum, maximum, positive)
    return float(value)


def _increasing(values: Sequence[float], path: str) -> None:
    if any(b <= a for a, b in zip(values, values[1:])):
        _fail(path, "values must be strictly increasing")


def _list(raw: Any, path: str, minimum_len: int = 1) -> list:
    if not isinstance(raw, list) or len(raw) < minimum_len:
        _fail(path, f"must be a list with at least {minimum_len} item(s)")
    return raw


def parse_cu_table(raw: Any, path: str) -> CuTable:
    if not isinstance(raw, dict):
        _fail(path, "must be an object with axis, axis_values, reflectances and values")
    axis = raw.get("axis", "k")
    if axis not in ("k", "rcr"):
        _fail(f"{path}.axis", f"'{axis}' is not valid: choose 'k' (room index) or 'rcr' (cavity ratio)")
    axis_values = tuple(number(v, f"{path}.axis_values[{i}]", minimum=0) for i, v in enumerate(_list(raw.get("axis_values"), f"{path}.axis_values")))
    _increasing(axis_values, f"{path}.axis_values")
    columns = _columns(raw.get("reflectances"), f"{path}.reflectances")
    scale = _scale(raw.get("unit", "fraction"), f"{path}.unit")
    rows = _list(raw.get("values"), f"{path}.values")
    if len(rows) != len(axis_values):
        _fail(f"{path}.values", f"needs one row per axis value ({len(axis_values)}), got {len(rows)}")
    values = tuple(_row(r, len(columns), scale, f"{path}.values[{i}]") for i, r in enumerate(rows))
    return CuTable(axis, axis_values, columns, values)


def _scale(unit: Any, path: str) -> float:
    if unit not in ("fraction", "percent"):
        _fail(path, f"'{unit}' is not valid: choose 'fraction' or 'percent'")
    return 0.01 if unit == "percent" else 1.0


def _columns(raw: Any, path: str):
    columns = []
    for i, col in enumerate(_list(raw, path)):
        triple = _list(col, f"{path}[{i}]", 3)
        if len(triple) != 3:
            _fail(f"{path}[{i}]", "must be [ceiling, walls, floor]")
        columns.append(tuple(number(v, f"{path}[{i}][{j}]", minimum=0, maximum=1) for j, v in enumerate(triple)))
    return tuple(columns)


def _row(raw: Any, width: int, scale: float, path: str):
    row = _list(raw, path)
    if len(row) != width:
        _fail(path, f"needs one value per reflectance column ({width}), got {len(row)}")
    return tuple(number(v, f"{path}[{j}]", minimum=0) * scale for j, v in enumerate(row))


def parse_photometry(raw: Any, path: str) -> Photometry:
    if not isinstance(raw, dict):
        _fail(path, "must be an object with gamma_deg and intensity_cd_per_klm (and c_deg for asymmetric luminaires)")
    gamma = tuple(number(v, f"{path}.gamma_deg[{i}]", minimum=0, maximum=180) for i, v in enumerate(_list(raw.get("gamma_deg"), f"{path}.gamma_deg")))
    _increasing(gamma, f"{path}.gamma_deg")
    intensity = raw.get("intensity_cd_per_klm")
    if "c_deg" not in raw:
        return Photometry(gamma, (0.0,), (_intensity_row(intensity, len(gamma), f"{path}.intensity_cd_per_klm"),))
    c_deg = tuple(number(v, f"{path}.c_deg[{i}]", minimum=0, maximum=359.999) for i, v in enumerate(_list(raw["c_deg"], f"{path}.c_deg")))
    _increasing(c_deg, f"{path}.c_deg")
    rows = _list(intensity, f"{path}.intensity_cd_per_klm")
    if len(rows) != len(c_deg):
        _fail(f"{path}.intensity_cd_per_klm", f"needs one row per C plane ({len(c_deg)}), got {len(rows)}")
    return Photometry(gamma, c_deg, tuple(_intensity_row(r, len(gamma), f"{path}.intensity_cd_per_klm[{i}]") for i, r in enumerate(rows)))


def _intensity_row(raw: Any, width: int, path: str):
    row = _list(raw, path)
    if len(row) != width:
        _fail(path, f"needs one value per gamma angle ({width}), got {len(row)}")
    return tuple(number(v, f"{path}[{j}]", minimum=0) for j, v in enumerate(row))


@lru_cache(maxsize=None)
def generic_table() -> CuTable:
    """The illustrative CU table shipped in data/cu_generic.json."""
    return parse_cu_table(data("cu_generic")["cu_table"], "data/cu_generic.json cu_table")

