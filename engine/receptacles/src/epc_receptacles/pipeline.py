"""The calculation, in a fixed order: read the document, count the outlets each room needs, place them (or take the ones drawn), check the mounting height and give the load."""
import math
from typing import Any, Dict, List, Optional, Union

from epc_receptacles import layout
from epc_receptacles.config import PARAMS, data
from epc_receptacles.document import parse
from epc_receptacles.model import Options, Result


def _required(room: Dict[str, Any], rule: Dict[str, Any]) -> tuple:
    """(outlets needed, the reason in words) for a room: the person's count, or what the use asks for its area or its perimeter."""
    area, perimeter = room["length_m"] * room["width_m"], 2 * (room["length_m"] + room["width_m"])
    if room["count"] is not None:
        return room["count"], "the number was chosen by the person"
    basis = rule["basis"]
    if basis == "area":
        wanted, why = math.ceil(area / rule["per_m2"]), f"one outlet per {rule['per_m2']:g} m² of {area:.1f} m²"
    elif basis == "perimeter":
        wanted, why = math.ceil(perimeter / rule["per_m"]), f"one outlet per {rule['per_m']:g} m of a perimeter of {perimeter:.1f} m"
    else:
        wanted, why = 0, "a fixed number for this use"
    return max(wanted, rule["min"]), f"{why}, at least {rule['min']}"


def _outlet(room: Dict[str, Any], rule: Dict[str, Any], outlets: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The outlet of the room: the one it names, or the first of the document that suits its family."""
    if room["receptacle"]:
        return outlets[room["receptacle"]]
    want = "special" if rule["family"] == "TUE" else "general"
    return next((o for o in outlets.values() if o["kind"] == want), None)


def _height(room: Dict[str, Any], outlet: Optional[Dict[str, Any]]) -> float:
    if room["height_m"] is not None:
        return room["height_m"]
    return (outlet or {}).get("height_m") or PARAMS["default_mount_height_m"]


def _checks(room: Dict[str, Any], rule: Dict[str, Any], z: float, norm: str, installed: int, required: int) -> List[Dict[str, Any]]:
    """What the room is checked against: the mounting height (by section of the norm and in wet rooms) and, with drawn outlets, that there are enough."""
    found = []
    limits = data("uses")["mounting"][norm]
    low, high = limits["min_m"], limits["max_m"]
    ok = z >= low and (high is None or z <= high)
    span = f"at least {low:g} m" if high is None else f"between {low:g} and {high:g} m"
    found.append({"id": "mounting_height", "ok": ok, "message": f"mounting height {z:g} m ({'complies' if ok else 'does not comply'}: {span}, AEA 90364-7-{norm}; typical value to verify)"})
    wet = rule.get("wet", False) if room["wet"] is None else bool(room["wet"])
    if wet:
        floor = data("uses")["mounting"]["wet_min_m"]
        found.append({"id": "wet_room_height", "ok": z >= floor, "message": f"room cleaned by washing or with water nearby: the box goes at least {floor:g} m up; check the IP rating"})
    if room["positions"]:
        found.append({"id": "enough_outlets", "ok": installed >= required, "message": f"{installed} outlets drawn, {required} needed"})
    return found


def _room(room: Dict[str, Any], doc: Dict[str, Any], options: Options) -> Dict[str, Any]:
    rule = data("uses")["uses"][room["use"]]
    required, why = _required(room, rule)
    outlet = _outlet(room, rule, doc["receptacles"])
    z = _height(room, outlet)
    drawn = bool(room["positions"])
    points = room["positions"] if drawn else layout.positions(room["length_m"], room["width_m"], required, z)
    installed = len(points)
    family = "TUE" if outlet and outlet["kind"] == "special" else rule["family"]
    each = outlet["power_va"] if outlet else 0.0
    cap = data("uses")["circuits"][family]["max_outlets"]
    return {"id": room["id"], "name": room["name"], "use": room["use"], "basis": rule["basis"], "area_m2": round(room["length_m"] * room["width_m"], 3), "perimeter_m": round(2 * (room["length_m"] + room["width_m"]), 3),
            "receptacle": outlet["id"] if outlet else "", "family": family, "required": required, "installed": installed, "power_va_each": each, "load_va": round(installed * each, 2),
            "circuits_min": math.ceil(installed / cap) if installed else 0, "layout": {"mode": "drawn" if drawn else "proposed", "positions": points},
            "checks": _checks(room, rule, z, room["norm"] or options.norm, installed, required),
            "estimate": {"reason": why, "confidence": rule["confidence"], "source": rule["source"]}}


def _warnings(rooms: List[Dict[str, Any]]) -> List[str]:
    found = []
    for r in rooms:
        found += [f"room '{r['name']}': {c['message']}" for c in r["checks"] if not c["ok"]]
        if not r["receptacle"]:
            found.append(f"room '{r['name']}': no outlet in the document fits its family ({r['family']}): the load is not counted")
    return found


def run(source: Union[Dict[str, Any], str, bytes], options: Optional[Options] = None) -> Result:
    """How many outlets each room needs, where they go and what they load; every estimate says why and how sure it is."""
    options = options or Options()
    doc = parse(source)
    rooms = [_room(r, doc, options) for r in doc["rooms"]]
    return Result(rooms=rooms, warnings=_warnings(rooms))
