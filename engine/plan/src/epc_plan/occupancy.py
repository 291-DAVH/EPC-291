"""How full a tray or a conduit is: the cross-section of the cables it carries against the free section it offers, and the share the rules allow.

Typical values (in params.json, `occupancy`): the engineer confirms them against the standard of the project. The diameter of a cable is the one written on the line
(`diametro_cable_mm`) or the default; the size of the container is read from its attributes: a tray has `ancho_mm` and `alto_mm`, a conduit `diametro_mm` (internal).
"""
import math
from typing import Any, Dict, Optional


def _number(value: Any) -> Optional[float]:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0 else None


def section_mm2(attrs: Dict[str, Any]) -> Optional[float]:
    w, h, d = _number(attrs.get("ancho_mm")), _number(attrs.get("alto_mm")), _number(attrs.get("diametro_mm"))
    if w and h:
        return w * h
    return math.pi * d * d / 4 if d else None


def limit_pct(attrs: Dict[str, Any], cables: int, cfg: Dict[str, Any]) -> float:
    if _number(attrs.get("ancho_mm")) and _number(attrs.get("alto_mm")):
        return float(cfg["tray_pct"])
    return float(cfg["conduit_pct"]["1" if cables <= 1 else "2" if cables == 2 else "many"])


def fill(attrs: Dict[str, Any], cables: int, cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """{"used_pct", "limit_pct", "status"} (ok, near or over) or None when the container has no size written on it."""
    area = section_mm2(attrs or {})
    if not area or cables <= 0:
        return None
    d = _number((attrs or {}).get("diametro_cable_mm")) or float(cfg["default_cable_mm"])
    used = cables * math.pi * d * d / 4 / area * 100
    limit = limit_pct(attrs, cables, cfg)
    return {"used_pct": round(used, 1), "limit_pct": limit, "cable_mm": d, "status": "over" if used > limit else "near" if used > limit * 0.85 else "ok"}
