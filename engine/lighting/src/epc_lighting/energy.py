"""Installed power and energy (UNAC chapter III 7: kWh = kW x hours)."""
from typing import Any, Dict, Optional

from epc_lighting.model import Luminaire, rnd


def summarise(lum: Luminaire, installed: int, area_m2: float, average_lux: float, hours_per_year: Optional[float]) -> Optional[Dict[str, Any]]:
    """None when the luminaire declares no power: there is nothing honest to report."""
    if lum.power_w is None:
        return None
    power_w = installed * lum.power_w
    out: Dict[str, Any] = {
        "installed_power_w": rnd(power_w),
        "power_density_w_m2": rnd(power_w / area_m2),
        "power_density_w_m2_per_100lx": rnd(power_w / area_m2 / (average_lux / 100.0)) if average_lux > 0 else None,
        "annual_energy_kwh": None,
    }
    if hours_per_year is not None:
        out["annual_energy_kwh"] = rnd(power_w / 1000.0 * hours_per_year)
    return out
