"""The plan of a sheet as a figure of the report: the outline and name of each room, the illuminance of its cells when the study has them, and the luminaires (and emergency luminaires) where they are.

A figure is shapes in the units of the drawing (the exporter scales them to the page): see `epc_drawing.export.report_pdf`.
"""
import colorsys
from typing import Dict, List, Optional

MAX_CELLS = 8000                          # a map with more cells than this is left out of the page: the figure keeps its outlines and luminaires
MARGIN = 0.03                             # of the largest side of the plan, around it
ALPHA = 0.42                              # the map over the plan, as on the screen


def _hex(t: float) -> str:
    """The colour of a cell on the scale from blue (the lowest lux of the room) to red (the highest), on white as it is on the screen."""
    r, g, b = colorsys.hls_to_rgb((240 - 240 * t) / 360.0, 0.5, 0.8)
    blend = lambda c: round((c * ALPHA + (1 - ALPHA)) * 255)                       # noqa: E731
    return f"#{blend(r):02x}{blend(g):02x}{blend(b):02x}"


def _cells(m: dict) -> List[dict]:
    span = (m["max"] - m["min"]) or 1.0
    return [{"s": "rect", "x": m["x0"] + (n % m["nx"]) * m["dx"], "y": m["y0"] + (n // m["nx"]) * m["dy"], "w": m["dx"], "h": m["dy"], "fill": _hex((v - m["min"]) / span)}
            for n, v in enumerate(m["values"]) if v is not None]


def _bounds(rooms: List[dict]) -> List[float]:
    xs = [p[0] for r in rooms for p in r["points"]]
    ys = [p[1] for r in rooms for p in r["points"]]
    pad = MARGIN * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    return [min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad]


def _centre(points: List[List[float]]) -> List[float]:
    return [sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)]


def _marks(calc: dict, radius: float) -> List[dict]:
    """The luminaires (amber) and the emergency luminaires (red) as circles."""
    shapes: List[dict] = []
    for by, fill, stroke in ((calc.get("placements", {}), "#fbbf24", "#b45309"), (calc.get("emergency_placements", {}), "#f87171", "#b91c1c")):
        for marks in by.values():
            shapes += [{"s": "circle", "x": m["x"], "y": m["y"], "r": radius, "fill": fill, "stroke": stroke, "lw": 0.8} for m in marks]
    return shapes


def _names(rooms: List[dict], bounds: List[float]) -> List[dict]:
    size = max(5.0, min(9.0, 0.9 * (bounds[2] - bounds[0]) / 60.0))
    return [{"s": "text", "x": c[0], "y": c[1], "text": r.get("name") or r["id"], "size": size, "color": "#111827", "bold": True} for r in rooms for c in [_centre(r["points"])]]


def _caption(caption: str, scale_caption: str, maps: List[dict]) -> str:
    return f"{caption} · {scale_caption.format(low=min(m['min'] for m in maps), high=max(m['max'] for m in maps))}" if maps else caption


def sheet_figure(rooms: List[dict], calc: dict, caption: str, scale_caption: str) -> Optional[dict]:
    """The figure of a sheet, or None when it has no rooms. `rooms` are the outlines of the sheet (`id`, `name`, `points`); `calc` is a calculation with its placements and (when asked for) maps."""
    if not rooms:
        return None
    bounds = _bounds(rooms)
    maps: List[dict] = list(calc.get("maps", {}).values())
    drawn = maps if sum(len(m["values"]) for m in maps) <= MAX_CELLS else []
    shapes: List[dict] = [c for m in drawn for c in _cells(m)]
    shapes += [{"s": "poly", "points": r["points"], "fill": None, "stroke": "#374151", "lw": 1.0} for r in rooms]
    shapes += _marks(calc, max(bounds[2] - bounds[0], bounds[3] - bounds[1]) * 0.012) + _names(rooms, bounds)
    return {"type": "figure", "caption": _caption(caption, scale_caption, drawn), "bounds": bounds, "max_height": 330, "shapes": shapes}
