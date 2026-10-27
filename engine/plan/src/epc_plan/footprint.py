"""The footprint of a drawing: what each element occupies in real space, in metres, so that drawings of different disciplines can be compared without sharing anything else.

A footprint is the only thing a discipline gives to the others: where an element is (plan points), how wide it is, the heights it spans from the floor of the project
(level number x storey height + elevation) and the free space it asks for around it. Circuits, cables, lengths and every other calculation stay inside the discipline.
"""
from typing import Any, Dict, List, Optional

from epc_plan import core

_NUMBERS = ("z_m", "ancho_m", "alto_m", "libre_m", "altura_m")


def _number(value: Any) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def geometry_of(kind: Dict[str, Any], attrs: Dict[str, Any]) -> Dict[str, float]:
    """The size of an element: the defaults of its kind in the profile, overridden by what the person wrote on the element itself."""
    g: Dict[str, float] = {"z_m": 0.0, "ancho_m": 0.0, "alto_m": 0.0, "libre_m": 0.0}
    g.update({k: float(v) for k, v in (kind.get("geom") or {}).items()})
    for key in _NUMBERS:
        v = _number((attrs or {}).get(key))
        if v is not None:
            g[key] = v
    return g


def _span(g: Dict[str, float], floor: float, vertical: bool) -> List[float]:
    """Bottom and top elevation: a shaft rises `altura_m` (or its height) from `z_m`; everything else is centred on `z_m`."""
    if vertical:
        bottom = floor + g["z_m"]
        return [bottom, bottom + (g.get("altura_m") or g["alto_m"])]
    return [floor + g["z_m"] - g["alto_m"] / 2, floor + g["z_m"] + g["alto_m"] / 2]


def _tags(document: Dict[str, Any]) -> Dict[str, str]:
    """The tag the engine gave each node and line (TB-001, CA-003...) so a report names things as the drawing does; empty when the drawing cannot be processed."""
    try:
        done = core.process(document)
    except core.PlanError:
        return {}
    tags = {n["id"]: n["tag"] for n in done["nodes"] if n.get("placed", True)}
    for s in done["stretches"]:
        tags.setdefault(s["line"], s["line_tag"])
    return tags


def footprints(document: Dict[str, Any], sheet: str, story_height_m: Optional[float] = None, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Every node and line of one drawing as a footprint in metres. A drawing without scale occupies nothing that can be measured: it gives none."""
    params = params or core.PARAMS
    plan = document.get("plan") or {}
    if not plan.get("scale"):
        return []
    story = story_height_m if story_height_m is not None else params["coordination"]["story_height_m"]
    level = plan.get("level", params["levels"]["ground"])
    number = core.parse_level(level, params)
    k = core.metres_per_unit(plan["scale"], params)
    origin = plan.get("origin", [0.0, 0.0])
    profile = core.load_profile(document.get("discipline", ""))
    line_kinds, node_kinds = core._kinds(profile)
    tags = _tags(document)
    floor = number * story
    out: List[Dict[str, Any]] = []
    for shape, items, kinds in (("node", document.get("nodes", []), node_kinds), ("line", document.get("lines", []), line_kinds)):
        for el in items:
            kind = kinds.get(el.get("kind"))
            if kind is None:
                continue
            g = geometry_of(kind, el.get("attrs") or {})
            pts = [[x, y] for x, y in (core.to_world(p, origin, k) for p in ([[el["x"], el["y"]]] if shape == "node" else el["points"]))]
            z0, z1 = _span(g, floor, bool(kind.get("vertical")))
            out.append({"sheet": sheet, "discipline": profile["id"], "level": level, "level_number": number, "id": el["id"], "kind": kind["id"], "shape": shape,
                        "tag": tags.get(el["id"], el.get("tag") or el["id"]), "points": pts, "width_m": g["ancho_m"], "z0": round(z0, 4), "z1": round(z1, 4),
                        "clear_m": g["libre_m"], "origin": "drawing"})
    return out
