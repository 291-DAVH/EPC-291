"""Zonal cavity method (UNAC chapter III 2).

The room is three cavities: ceiling (above the luminaire plane), room (luminaire
plane to work plane) and floor (below the work plane). The cavity ratio
RCR = 5 h (l + w) / (l w) replaces the room index (RCR = 5 / k), and the ceiling
and floor cavities are folded into effective reflectances before the CU is read.
"""
from epc_lighting import cu, geometry
from epc_lighting.methods import register
from epc_lighting.model import Context, FluxPlan, Luminaire, Room, rnd


@register("zonal")
def required_flux(room: Room, lum: Luminaire, ctx: Context) -> FluxPlan:
    h = ctx.mounting.value
    w, length = room.width_m, room.length_m
    ceiling, walls, floor = (e.value for e in room.reflectances)
    ceiling_depth = room.height_m - room.work_plane_m - h
    rcr = geometry.cavity_ratio(h, w, length)
    ccr = geometry.cavity_ratio(ceiling_depth, w, length)
    fcr = geometry.cavity_ratio(room.work_plane_m, w, length)
    rho_cc = geometry.effective_reflectance(ceiling, walls, w, length, ceiling_depth)
    rho_fc = geometry.effective_reflectance(floor, walls, w, length, room.work_plane_m)
    estimate = cu.resolve(room, lum, {"k": 5.0 / rcr, "rcr": rcr}, (rho_cc, walls, rho_fc), ctx.warnings)
    flux = ctx.target.value * room.area_m2 / (estimate.value * ctx.maintenance.value)
    geometry_out = {
        "room_cavity_ratio": rnd(rcr),
        "ceiling_cavity_ratio": rnd(ccr),
        "floor_cavity_ratio": rnd(fcr),
        "effective_ceiling_reflectance": rnd(rho_cc),
        "effective_floor_reflectance": rnd(rho_fc),
    }
    return FluxPlan(flux, estimate, geometry_out)
