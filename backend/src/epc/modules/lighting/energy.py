"""What the installed power of a calculation means for the person: whether a room stays under the power density they allow, and what a year of use costs.

The engine reports the installed power, W/m² and kWh/year. It has no limit and no tariff: both are the person's (the limit may come from a standard, the tariff from the bill), so they are optional and nothing is
compared or priced without them.
"""
from typing import Any, Dict, Optional

from epc.modules.lighting.models import CalcOptions


def _check(energy: Optional[dict], options: CalcOptions) -> Optional[Dict[str, Any]]:
    if not energy:
        return None
    density, kwh = energy.get("power_density_w_m2"), energy.get("annual_energy_kwh")
    limit = options.power_limit_w_m2
    return {"power_w": energy.get("installed_power_w"), "density_w_m2": density, "limit_w_m2": limit,
            "complies": None if limit is None or density is None else density <= limit + 1e-9,
            "annual_kwh": kwh, "annual_cost": round(kwh * options.kwh_price, 2) if kwh is not None and options.kwh_price is not None else None}


def energy_checks(result: dict, options: CalcOptions) -> Dict[str, dict]:
    """By room or area id: its installed power, power density against the limit (None when there is no limit) and the yearly energy and cost (None when the hours or the tariff are missing)."""
    found = {x["id"]: _check(x.get("energy"), options) for x in result["rooms"] + result["areas"]}
    return {i: c for i, c in found.items() if c}
