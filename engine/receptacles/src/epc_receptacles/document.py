"""Reads and checks the document the engine is given: the outlets in use and the rooms (rectangles, in metres)."""
import json
from typing import Any, Dict, List, Union

from epc_receptacles.config import PARAMS, data
from epc_receptacles.model import NORMS, ReceptaclesError

MAX_SIDE_M = 1000.0


def load(source: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """The document as a dict: it may come as a dict, a JSON string or JSON bytes."""
    if isinstance(source, (str, bytes, bytearray)):
        try:
            source = json.loads(source)
        except ValueError as exc:
            raise ReceptaclesError(f"the document is not valid JSON: {exc}")
    if not isinstance(source, dict):
        raise ReceptaclesError("the document must be a JSON object with `receptacles` and `rooms`")
    return source


def _number(where: str, value: Any, low: float, high: float, optional: bool = False) -> Any:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low < value <= high:
        raise ReceptaclesError(f"{where}: a number above {low} and up to {high}")
    return float(value)


def _outlet(entry: Any, index: int) -> Dict[str, Any]:
    where = f"receptacles[{index}]"
    if not isinstance(entry, dict) or not str(entry.get("id", "")).strip():
        raise ReceptaclesError(f"{where}: each outlet needs an `id`")
    kind = entry.get("kind", "general")
    if kind not in ("general", "special"):
        raise ReceptaclesError(f"{where}.kind: `general` or `special`")
    out = dict(entry)
    out["kind"] = kind
    out["power_va"] = _number(f"{where}.power_va", entry.get("power_va", 100), -1, 100000)
    out["height_m"] = _number(f"{where}.height_m", entry.get("height_m"), -1, 5, optional=True)
    return out


def _positions(where: str, value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > PARAMS["max_outlets_per_room"]:
        raise ReceptaclesError(f"{where}.positions: a list of up to {PARAMS['max_outlets_per_room']} points")
    for i, p in enumerate(value):
        if not isinstance(p, dict) or any(isinstance(p.get(k), bool) or not isinstance(p.get(k), (int, float)) for k in ("x_m", "y_m")):
            raise ReceptaclesError(f"{where}.positions[{i}]: needs `x_m` and `y_m` in metres")
    return value


def _room(entry: Any, index: int, outlets: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    where = f"rooms[{index}]"
    if not isinstance(entry, dict) or not str(entry.get("id", "")).strip():
        raise ReceptaclesError(f"{where}: each room needs an `id`")
    use = entry.get("use") or "general"
    if use not in data("uses")["uses"]:
        raise ReceptaclesError(f"{where}.use: '{use}' is not a known use ({', '.join(data('uses')['uses'])})")
    outlet = entry.get("receptacle") or ""
    if outlet and outlet not in outlets:
        raise ReceptaclesError(f"{where}.receptacle: '{outlet}' is not among the outlets of the document")
    norm = entry.get("norm") or None
    if norm is not None and norm not in NORMS:
        raise ReceptaclesError(f"{where}.norm: one of {', '.join(NORMS)}")
    count = entry.get("count")
    if count is not None and (isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= PARAMS["max_outlets_per_room"]):
        raise ReceptaclesError(f"{where}.count: a whole number from 0 to {PARAMS['max_outlets_per_room']}")
    return {**entry, "id": str(entry["id"]), "name": str(entry.get("name") or entry["id"]), "use": use, "receptacle": outlet, "norm": norm, "count": count,
            "length_m": _number(f"{where}.length_m", entry.get("length_m"), 0, MAX_SIDE_M), "width_m": _number(f"{where}.width_m", entry.get("width_m"), 0, MAX_SIDE_M),
            "height_m": _number(f"{where}.height_m", entry.get("height_m"), -1, 5, optional=True), "positions": _positions(where, entry.get("positions")), "wet": entry.get("wet")}


def parse(source: Union[Dict[str, Any], str, bytes]) -> Dict[str, Any]:
    """The document checked and ready: `{"receptacles": {id: outlet}, "rooms": [room]}`. Every problem says what to correct."""
    doc = load(source)
    raw = doc.get("receptacles", [])
    if not isinstance(raw, list):
        raise ReceptaclesError("`receptacles` must be a list")
    outlets = {}
    for i, entry in enumerate(raw):
        o = _outlet(entry, i)
        if o["id"] in outlets:
            raise ReceptaclesError(f"receptacles[{i}]: the id '{o['id']}' is repeated")
        outlets[o["id"]] = o
    rooms_raw = doc.get("rooms", [])
    if not isinstance(rooms_raw, list) or len(rooms_raw) > PARAMS["max_rooms"]:
        raise ReceptaclesError(f"`rooms` must be a list of up to {PARAMS['max_rooms']} rooms")
    rooms, seen = [], set()
    for i, entry in enumerate(rooms_raw):
        room = _room(entry, i, outlets)
        if room["id"] in seen:
            raise ReceptaclesError(f"rooms[{i}]: the id '{room['id']}' is repeated")
        seen.add(room["id"])
        rooms.append(room)
    return {"receptacles": outlets, "rooms": rooms}
