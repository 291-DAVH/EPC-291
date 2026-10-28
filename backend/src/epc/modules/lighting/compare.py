"""Comparing the luminaires of the catalogue for one room, and choosing one for the rooms that have a target but no luminaire.

Each luminaire is calculated for the room alone, exactly as the panel would calculate it (so the figures are the ones the person would get by choosing it), without the point-by-point grid, which is slow
and not needed to rank. The best one is the one that complies with the least installed power, then with the fewest luminaires.
"""
from pathlib import Path
from typing import List, Optional, Tuple

from epc.core.errors import Invalid
from epc.modules.lighting import service
from epc.modules.lighting.models import CalcIn, CompareIn, RoomParams

EMERGENCY_GROUP = "emergency"                      # the luminaires of this group light the way out, not the room: they are not candidates for it
MAX_CANDIDATES = 60                                  # the catalogue is small; a runaway one is not calculated whole


def _kind_of(params: RoomParams) -> str:
    return "exterior" if params.exterior else "interior"


def _single(body: CalcIn, room_id: str, params: RoomParams) -> CalcIn:
    """The request that calculates only this room, with the parameters given."""
    room = next(r for r in body.sheet.rooms if r.id == room_id)
    options = body.options.model_copy(update={"compute_points": False, "map": False, "use_drawn": False, "auto_luminaire": False})
    return body.model_copy(update={"sheet": body.sheet.model_copy(update={"rooms": [room], "nodes": []}), "rooms": {room_id: params}, "options": options})


def _worst_spacing(layout: dict) -> str:
    states = [a.get("status") for a in layout.get("spacing_check", {}).values() if a.get("checked")]
    return "exceeds" if "exceeds" in states else "within_tolerance" if "within_tolerance" in states else "ok" if states else "n/a"


def _row(lid: str, entry: dict, lang: str, out: dict) -> Optional[dict]:
    """One luminaire's figures for the room, or None when the room could not be calculated with it."""
    result = out["result"]
    item = next(iter((result["rooms"] if result else []) + (result["areas"] if result else [])), None)
    if item is None:
        return None
    v, energy = item["verification"], item.get("energy") or {}
    installed = item["layout"]["installed"] if "layout" in item else item["flux"]["luminaires_required"]
    return {"luminaire": lid, "name": service.label(entry, lang) or lid, "installed": installed, "power_w": energy.get("installed_power_w"), "density_w_m2": energy.get("power_density_w_m2"),
            "average_lux": v["average_lux"], "target_lux": v["target_lux"], "complies": v["complies"], "spacing": _worst_spacing(item.get("layout", {})),
            "favorite": bool(entry.get("favorite")), "illustrative": bool(entry.get("illustrative"))}


def _rank(row: dict) -> Tuple:
    return (not row["complies"], row["power_w"] is None, row["power_w"] or 0.0, row["installed"], row["luminaire"])


def rows_for(project_dir: Path, body: CalcIn, room_id: str) -> List[dict]:
    """Every luminaire of the right kind calculated for the room, best first."""
    params = body.rooms.get(room_id)
    if params is None:
        raise Invalid({"room": "this room has no parameters: choose an activity or a target first"})
    luminaires = service.effective(project_dir)
    ids = [lid for lid, e in luminaires.items() if e.get("kind", "interior") == _kind_of(params) and e.get("group") != EMERGENCY_GROUP][:MAX_CANDIDATES]
    rows = []
    for lid in ids:
        row = _row(lid, luminaires[lid], body.lang, service.calc(project_dir, _single(body, room_id, params.model_copy(update={"luminaire": lid}))))
        if row:
            rows.append(row)
    return sorted(rows, key=_rank)


def compare(project_dir: Path, body: CompareIn) -> dict:
    """The luminaires of the catalogue for one room: `{room, options (best first), best}`."""
    if not any(r.id == body.room for r in body.sheet.rooms):
        raise Invalid({"room": "this room is not on the sheet"})
    params = body.rooms.get(body.room)
    problem = service._target_problem(params) if params else "no parameters"
    if problem:
        raise Invalid({"room": problem})
    rows = rows_for(project_dir, body, body.room)
    return {"room": body.room, "options": rows, "best": next((r["luminaire"] for r in rows if r["complies"]), None)}


def apply_auto(project_dir: Path, body: CalcIn) -> Tuple[CalcIn, List[str]]:
    """The request with a luminaire chosen for each room that has a target but none: the best one that complies. Notes say what was chosen, or why nothing could be."""
    rooms, notes = dict(body.rooms), []
    for room in body.sheet.rooms:
        params = rooms.get(room.id)
        if params is None or params.luminaire or service._target_problem(params):
            continue
        rows = rows_for(project_dir, body, room.id)
        best = next((r for r in rows if r["complies"]), None)
        if best is None:
            notes.append(f"room '{room.name or room.id}': no luminaire of the catalogue reaches its target, so none was chosen")
            continue
        rooms[room.id] = params.model_copy(update={"luminaire": best["luminaire"]})
        notes.append(f"room '{room.name or room.id}': the luminaire '{best['name']}' was chosen ({best['installed']} luminaires, {best['power_w']} W)")
    return body.model_copy(update={"rooms": rooms}), notes
