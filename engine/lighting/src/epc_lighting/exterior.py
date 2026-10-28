"""Floodlight method for exterior areas: N = E_m * S / (Phi * CBU * f_m).

UNAC chapter III 5. CBU, the coefficient of beam utilisation, is the share of the
beam lumens that reach the area; it comes from the isocandela curves of the
floodlight and the aiming points, which this engine does not compute. When the
document gives none, the middle of the usual range is assumed, with low confidence.
"""
import math
from typing import Any, Dict, Iterator, List

from epc_lighting import energy, factors
from epc_lighting.config import PARAMS
from epc_lighting.model import Area, Estimate, Luminaire, rnd


def _beam_utilisation(area: Area, warnings: List[str]) -> Estimate:
    if area.beam_utilisation is not None:
        estimate = Estimate(area.beam_utilisation, "given in the document", 1.0)
    else:
        value = PARAMS["defaults"]["area_beam_utilisation"]
        estimate = Estimate(value, "assumed: no isocandela data given (usual range 0.6-0.9, UNAC chapter III 5)", 0.4)
    low, high = PARAMS["beam_utilisation_range"]
    if estimate.value < low:
        warnings.append(f"CBU {estimate.value} is below {low}: under {int(low * 100)}% of the beam reaches the area, a narrower beam or other aiming may be more economical")
    if estimate.value > high:
        warnings.append(f"CBU {estimate.value} is above {high}: the beam is probably too narrow and the light too concentrated")
    return estimate


def calculate(area: Area, lum: Luminaire, tags: Iterator[int], warnings: List[str]) -> Dict[str, Any]:
    target, extras = factors.resolve_target(area, warnings)
    fm = factors.exterior_maintenance(area.enclosure, area.maintenance)
    cbu = _beam_utilisation(area, warnings)
    beam_lm = lum.flux_lm * lum.efficiency
    exact = target.value * area.area_m2 / (beam_lm * cbu.value * fm.value)
    n = max(1, math.ceil(exact - PARAMS["ceil_epsilon"]))
    achieved = n * beam_lm * cbu.value * fm.value / area.area_m2
    tag_list = [f"LU-{next(tags):03d}" for _ in range(n)]
    return {
        "id": area.id,
        "name": area.name,
        "method": "floodlight",
        "area_m2": rnd(area.area_m2),
        "target": {**target.as_dict(), **extras},
        "luminaire": _luminaire(lum),
        "factors": {"beam_utilisation": cbu.as_dict(), "maintenance": fm.as_dict()},
        "flux": {"luminaires_exact": rnd(exact), "luminaires_required": n, "beam_flux_per_luminaire_lm": rnd(beam_lm)},
        "tags": tag_list,
        "verification": {
            "average_lux": rnd(achieved),
            "target_lux": rnd(target.value),
            "complies": achieved >= target.value - 1e-9,
            "margin_pct": rnd((achieved / target.value - 1) * 100),
        },
        "energy": energy.summarise(lum, n, area.area_m2, achieved, area.operating_hours),
    }


def _luminaire(lum: Luminaire) -> Dict[str, Any]:
    return {"id": lum.id, "name": lum.name, "lamps": lum.lamps, "lamp_flux_lm": rnd(lum.lamp_flux_lm), "flux_lm": rnd(lum.flux_lm)}
