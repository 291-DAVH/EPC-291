"""Room geometry: mounting height, room index, cavity ratios and effective reflectances.

Why these formulas: UPV lumen-method article (tables 1-3) for the room index,
UNAC chapter III 2 for the zonal cavity ratio. The effective cavity reflectance
is the standard IES (Gershun) formula; the UNAC text defers to annex tables that
were not supplied, so the formula stands in for them.
"""
from typing import Any, Dict, List

from epc_lighting.config import PARAMS, data
from epc_lighting.model import Estimate, LightingError, Room


def mounting_height(room: Room, system: Dict[str, Any], warnings: List[str]) -> Estimate:
    """Height h of the luminaire plane over the work plane."""
    available = room.height_m - room.work_plane_m
    if available <= 0:
        raise LightingError(
            f"room '{room.id}': work_plane_height_m ({room.work_plane_m}) must be lower than height_m ({room.height_m})"
        )
    if room.suspension_mode:
        return _auto_height(room, system, available)
    h = available - room.suspension_m
    if h <= 0:
        raise LightingError(
            f"room '{room.id}': suspension_m ({room.suspension_m}) leaves no height between the luminaires and the work plane; "
            f"it must be lower than {round(available, 3)} m (height_m - work_plane_height_m)"
        )
    reason = "luminaires as high as possible (UPV table 1)" if room.suspension_m == 0 else f"given suspension d' = {room.suspension_m} m"
    return Estimate(h, reason, 1.0)


def _auto_height(room: Room, system: Dict[str, Any], available: float) -> Estimate:
    group = system.get("suspension_group")
    rules = data("lighting_systems")["suspension_rules"]
    if group is None:
        usable = sorted(k for k, v in data("lighting_systems")["systems"].items() if v.get("suspension_group"))
        raise LightingError(
            f"room '{room.id}': suspension_mode '{room.suspension_mode}' is not defined for lighting_system '{room.system}' "
            f"(UPV table 2 covers {usable}); give suspension_m instead"
        )
    fraction = rules[group][room.suspension_mode]["h_fraction"]
    note = rules[group][room.suspension_mode]["note"]
    return Estimate(fraction * available, f"UPV table 2 ({group} lighting, {room.suspension_mode}): {note}", 0.8)


def room_index(formula: str, room: Room, h: float) -> float:
    """Room index k (UPV table 3). h is the luminaire plane height over the work plane."""
    a, b = room.width_m, room.length_m
    if formula == "direct":
        return a * b / (h * (a + b))
    plane_above_floor = room.work_plane_m + h
    return 3 * a * b / (2 * plane_above_floor * (a + b))


def cavity_ratio(depth_m: float, width_m: float, length_m: float) -> float:
    """Cavity ratio 5 * depth * (length + width) / (length * width) (UNAC 2)."""
    return PARAMS["cavity"]["rcr_factor"] * depth_m * (width_m + length_m) / (width_m * length_m)


def effective_reflectance(rho_base: float, rho_wall: float, width_m: float, length_m: float, depth_m: float) -> float:
    """Effective reflectance of a cavity as seen from its open face.

    A cavity of zero depth is its base; a deep one tends to zero.
    """
    if depth_m <= 0:
        return rho_base
    opening = width_m * length_m
    walls = 2 * (width_m + length_m) * depth_m
    surface = opening + walls
    average = (rho_base * opening + rho_wall * walls) / surface
    return average * opening / (surface - average * surface + average * opening)
