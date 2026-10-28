"""Lumen (utilisation factor) method: Phi_T = E_m * S / (C_u * C_m).

UPV lumen-method article, equation 1; UNAC chapter III 1. It gives the average
illuminance of a general, uniform installation with an error near +-5 %.
"""
from epc_lighting import cu, geometry
from epc_lighting.methods import register
from epc_lighting.model import Context, FluxPlan, Luminaire, Room, rnd


@register("lumen")
def required_flux(room: Room, lum: Luminaire, ctx: Context) -> FluxPlan:
    h = ctx.mounting.value
    formula = ctx.system["index_formula"]
    k = geometry.room_index(formula, room, h)
    refl = tuple(e.value for e in room.reflectances)
    estimate = cu.resolve(room, lum, {"k": k, "rcr": 5.0 / k}, refl, ctx.warnings)
    flux = ctx.target.value * room.area_m2 / (estimate.value * ctx.maintenance.value)
    return FluxPlan(flux, estimate, {"room_index_k": rnd(k), "index_formula": formula})
