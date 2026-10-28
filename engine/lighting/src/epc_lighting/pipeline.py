"""The work end to end, always in the same order. Each step is a function of its own.

  1. read and validate the document
  2. per room: resolve target and factors -> flux method -> luminaire count
     -> distribution -> verification -> point-by-point -> energy
  3. per exterior area: floodlight method
"""
import math
from typing import Any, Dict, Iterator, List, Tuple

from epc_lighting import checks, emergency, energy, exterior, factors, geometry, layout, methods, photometry, pointcalc
from epc_lighting.config import PARAMS, data
from epc_lighting.document import load_document, parse_project
from epc_lighting.model import Context, Luminaire, Options, Result, Room, rnd


def run(document: Any, options: Options = Options()) -> Result:
    """Calculate every room and area of a lighting document (dict, JSON str or bytes)."""
    project = parse_project(load_document(document))
    result = Result()
    tags = layout.new_tag_counter()
    for room in project.rooms:
        warnings: List[str] = []
        result.rooms.append(_room(room, project.luminaires[room.luminaire_id], options, tags, warnings))
        result.warnings.extend(f"room '{room.id}': {w}" for w in warnings)
    for area in project.areas:
        warnings = []
        result.areas.append(exterior.calculate(area, project.luminaires[area.luminaire_id], tags, warnings))
        result.warnings.extend(f"area '{area.id}': {w}" for w in warnings)
    escape_tags = layout.new_tag_counter()
    for item in project.emergency:
        warnings = []
        result.emergency.append(emergency.calculate(item, project.luminaires[item.luminaire_id], escape_tags, warnings))
        result.warnings.extend(f"emergency '{item.id}': {w}" for w in warnings)
    if not (project.rooms or project.areas or project.emergency):
        result.warnings.append("the document has no rooms, areas or emergency rooms, so nothing was calculated: add at least one entry to 'rooms', 'areas' or 'emergency'")
    return result


def _context(room: Room, system: Dict[str, Any], warnings: List[str]) -> Tuple[Context, Dict[str, Any]]:
    target, extras = factors.resolve_target(room, warnings)
    ctx = Context(
        target=target,
        maintenance=factors.interior_maintenance(room.environment, room.maintenance),
        mounting=geometry.mounting_height(room, system, warnings),
        system=system,
        warnings=warnings,
    )
    return ctx, extras


def _required_count(flux_lm: float, lum: Luminaire) -> Dict[str, Any]:
    installed_flux = flux_lm / lum.efficiency
    exact = installed_flux / lum.flux_lm
    return {"exact": exact, "count": max(1, math.ceil(exact - PARAMS["ceil_epsilon"])), "installed_flux_lm": installed_flux}


def _verify(room: Room, lum: Luminaire, installed: int, cu_value: float, cm: float, target: float, warnings: List[str]) -> Dict[str, Any]:
    average = installed * lum.flux_lm * lum.efficiency * cu_value * cm / room.area_m2
    complies = average >= target - 1e-9
    if not complies:  # pragma: no cover  (the count is rounded up, so this guards against a future change)
        warnings.append(f"average illuminance {round(average, 1)} lux is below the target {round(target, 1)} lux: add luminaires or use a higher flux")
    return {
        "method": "average illuminance E_m = N * n * Phi_L * C_u * C_m / S",
        "average_lux": rnd(average),
        "target_lux": rnd(target),
        "complies": complies,
        "margin_pct": rnd((average / target - 1) * 100),
    }


def _points(room: Room, lum: Luminaire, lay: Dict[str, Any], h: float, cm: float, options: Options, warnings: List[str]) -> Dict[str, Any]:
    if not options.compute_points:
        return {"computed": False, "reason": "disabled by the options"}
    if lum.photometry is None:
        if room.points:
            warnings.append(f"points were requested but luminaire '{lum.id}' has no photometry: give 'photometry' to compute them")
        return {"computed": False, "reason": f"luminaire '{lum.id}' has no photometry (intensity table)"}
    sources = [
        pointcalc.Source(p["x_m"], p["y_m"], p["z_m"], lum.photometry, lum.flux_lm) for p in lay["positions"]
    ]
    step = room.point_step_m or options.point_step_m
    report, extra = pointcalc.calculate(sources, room.width_m, room.length_m, room.work_plane_m, step, cm, room.points, options.return_grid)
    warnings.extend(extra)
    report["photometry_output_ratio"] = _output_ratio(lum, warnings)
    return report


def _output_ratio(lum: Luminaire, warnings: List[str]) -> float:
    ratio = photometry.emitted_fraction(lum.photometry)
    limit = PARAMS["photometry_max_output_ratio"]
    if ratio > limit:
        warnings.append(
            f"the intensity table of luminaire '{lum.id}' emits {round(ratio * 100)}% of the lamp flux: a luminaire cannot emit more "
            f"than its lamps, so check that the values are cd per klm of lamp flux; the point results are not reliable"
        )
    return rnd(ratio)


def _luminaire_block(lum: Luminaire) -> Dict[str, Any]:
    return {
        "id": lum.id,
        "name": lum.name,
        "lamps": lum.lamps,
        "lamp_flux_lm": rnd(lum.lamp_flux_lm),
        "flux_lm": rnd(lum.flux_lm),
        "efficiency": rnd(lum.efficiency),
    }


def _room(room: Room, lum: Luminaire, options: Options, tags: Iterator[int], warnings: List[str]) -> Dict[str, Any]:
    system = data("lighting_systems")["systems"][room.system]
    ctx, extras = _context(room, system, warnings)
    plan = methods.get(room.method)(room, lum, ctx)
    need = _required_count(plan.required_flux_lm, lum)
    h = ctx.mounting.value
    lay = layout.plan(room, lum, need["count"], h, options, tags, warnings)
    verification = _verify(room, lum, lay["installed"], plan.cu.value, ctx.maintenance.value, ctx.target.value, warnings)
    points = _points(room, lum, lay, h, ctx.maintenance.value, options, warnings)
    if points.get("computed"):
        verification["direct_check"] = checks.direct_check(ctx.target.value, verification["average_lux"], points["avg_lux"])
    return {
        "id": room.id,
        "name": room.name,
        "method": room.method,
        "lighting_system": room.system,
        "geometry": {
            "area_m2": rnd(room.area_m2),
            "width_m": rnd(room.width_m),
            "length_m": rnd(room.length_m),
            "height_m": rnd(room.height_m),
            "work_plane_height_m": rnd(room.work_plane_m),
            "mounting_height_m": ctx.mounting.as_dict(),
            **plan.geometry,
        },
        "target": {**ctx.target.as_dict(), **extras},
        "reflectances": {
            "ceiling": room.reflectances[0].as_dict(),
            "walls": room.reflectances[1].as_dict(),
            "floor": room.reflectances[2].as_dict(),
        },
        "factors": {"cu": plan.cu.as_dict(), "maintenance": ctx.maintenance.as_dict()},
        "luminaire": _luminaire_block(lum),
        "flux": {
            "required_lm": rnd(plan.required_flux_lm),
            "required_installed_lm": rnd(need["installed_flux_lm"]),
            "luminaires_exact": rnd(need["exact"]),
            "luminaires_required": need["count"],
        },
        "layout": lay,
        "verification": verification,
        "ugr": checks.ugr(room.ugr_calculated, extras.get("ugr_l_max")),
        "points": points,
        "energy": energy.summarise(lum, lay["installed"], room.area_m2, verification["average_lux"], room.operating_hours),
    }
