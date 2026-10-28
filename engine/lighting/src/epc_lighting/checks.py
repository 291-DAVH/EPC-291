"""Checks that compare figures already calculated: the glare rating of a room and the agreement between the flux method and the direct point-by-point average.

Ported from `epc_aea90364.lighting` (CAL-001). The engine does not calculate UGR (it needs the luminance of the luminaires and the position of the observer): it compares a value the caller
brings from photometric software with the limit of the activity, and says so when there is none.
"""
import math
from typing import Any, Dict, Optional

from epc_lighting.config import PARAMS
from epc_lighting.model import LightingError, rnd

_TOL = 1e-9


def ugr(calculated: Optional[float], limit: Optional[float]) -> Dict[str, Any]:
    """The UGR of a room against its limit: `not_verifiable` when the value or the limit is missing, otherwise `meets` or `does_not_meet`."""
    if calculated is None or limit is None:
        return {"result": "not_verifiable", "complies": None, "limit": limit, "calculated": calculated,
                "reason": "UGR needs the photometry of the luminaires and an external calculation: give 'ugr_calculated' to compare it with the limit of the activity"}
    if isinstance(calculated, bool) or not math.isfinite(calculated) or calculated < 0:
        raise LightingError(f"ugr_calculated must be a finite number from 0 up, got {calculated!r}")
    ok = calculated <= limit
    return {"result": "meets" if ok else "does_not_meet", "complies": ok, "limit": limit, "calculated": calculated}


def direct_check(target_lux: float, flux_average_lux: float, direct_average_lux: float) -> Dict[str, Any]:
    """The flux method sizes the room and the direct point-by-point average (without reflections, so a lower bound) checks it: it complies when the flux average reaches the target and the direct
    average reaches `direct_factor` of it. The factor is a typical value to confirm with the project standard."""
    factor = PARAMS["conformity"]["direct_factor"]
    limit = factor * target_lux
    flux_ok = flux_average_lux >= target_lux - _TOL
    direct_ok = direct_average_lux >= limit - _TOL
    return {"complies": flux_ok and direct_ok, "flux_ok": flux_ok, "direct_ok": direct_ok, "direct_factor": rnd(factor), "direct_min_acceptable_lux": rnd(limit)}
