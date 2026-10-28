"""The size of each conduit and tray, from the cables that go through it.

A container carries the cables of the circuits routed over it (see `core._containers`); once the cables are sized (the section of each circuit comes from the calculation of its board), the smallest
commercial size whose free section holds them within the fill limit is the one to draw. Typical values (in params.json, `sizing`): the engineer confirms them against the catalogue of the project.
"""
import math
from typing import Any, Dict, List, Optional

from epc_plan import occupancy


def cable_mm(section_mm2: Optional[float], cfg: Dict[str, Any], default: float) -> float:
    """The outside diameter of a cable: the one of the nearest section in the table at or above (the largest when it exceeds the table), the default when the section is unknown."""
    if not section_mm2 or section_mm2 <= 0:
        return default
    table = sorted((float(k), float(v)) for k, v in cfg["cable_mm_by_section"].items())
    for s, d in table:
        if s >= section_mm2:
            return d
    return table[-1][1]


def _area(d: float) -> float:
    return math.pi * d * d / 4


def _is_tray(kind: str, kinds: Dict[str, Dict[str, Any]]) -> bool:
    return "ancho_mm" in (kinds.get(kind, {}).get("atributos") or [])


def _candidates(tray: bool, cfg: Dict[str, Any]) -> List[Dict[str, float]]:
    if tray:
        return [{"ancho_mm": float(w), "alto_mm": float(h)} for w, h in cfg["tray_mm"]]
    return [{"diametro_mm": float(d)} for d in cfg["conduit_mm"]]


def _used_pct(cables: List[float], size: Dict[str, float]) -> float:
    return sum(_area(d) for d in cables) / occupancy.section_mm2(size) * 100


def size_container(container: Dict[str, Any], sections: Dict[str, Optional[float]], terna_cables: Dict[str, int], tray: bool, cfg: Dict[str, Any], occ: Dict[str, Any]) -> Dict[str, Any]:
    """The smallest size that holds the cables of a container within its limit: {size, used_pct, limit_pct, cable_mm: [..], fits}. When even the largest does not hold them, `fits` is False and the
    largest is returned."""
    cables = [cable_mm(sections.get(c), cfg, float(occ["default_cable_mm"])) for c in container["circuits"] for _ in range(terna_cables.get(c, 1))]
    options = _candidates(tray, cfg)
    limit = occupancy.limit_pct(options[0], len(cables), occ)
    for size in options:
        used = _used_pct(cables, size)
        if used <= limit:
            return {"size": size, "used_pct": round(used, 1), "limit_pct": limit, "cable_mm": cables, "fits": True}
    return {"size": options[-1], "used_pct": round(_used_pct(cables, options[-1]), 1), "limit_pct": limit, "cable_mm": cables, "fits": False}


def size_containers(containers: List[Dict[str, Any]], sections: Dict[str, Optional[float]], ternas: Dict[str, int], line_kinds: Dict[str, Dict[str, Any]], params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """One entry per container: its line, kind, circuits, cables, the size it has now (the fill reported by the plan, if it had a size) and the size that fits."""
    cfg, occ = params["sizing"], params["occupancy"]
    out = []
    for c in containers:
        tray = _is_tray(c["kind"], line_kinds)
        found = size_container(c, sections, ternas, tray, cfg, occ)
        out.append({"line": c.get("line", ""), "tag": c["tag"], "kind": c["kind"], "circuits": c["circuits"], "cables": c["cables"], "now": c.get("fill"), **found})
    return out
