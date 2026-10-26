"""The DXF deliverable, written from the result of `core.process` with ezdxf (MIT). It is never converted from the SVG of the screen: both come from the same model.

Real units: metres or millimetres, as the discipline says. One layer per kind of element, one block per symbol used, real text for the tags.
"""
import math
from pathlib import Path
from typing import Any, Dict, List

import ezdxf

from epc_plan import core

_UNITS = {"m": (6, 1.0), "mm": (4, 1000.0)}          # DXF $INSUNITS code and the factor from metres


def versions(params: Dict[str, Any] = core.PARAMS) -> List[str]:
    return list(params["dxf"]["versions"])


def _symbol_prims(symbol_id: str, size: float, scale: float) -> List[Dict[str, Any]]:
    out = []
    for p in core.SYMBOLS[symbol_id]["prims"]:
        if p["t"] == "rect":
            w, h = p["w"] * size * scale / 2, p["h"] * size * scale / 2
            out.append({"t": "poly", "pts": [(-w, -h), (w, -h), (w, h), (-w, h)]})
        elif p["t"] == "line":
            out.append({"t": "line", "a": tuple(c * size * scale for c in p["a"]), "b": tuple(c * size * scale for c in p["b"])})
        elif p["t"] == "circle":
            out.append({"t": "circle", "r": p["r"] * size * scale})
    return out


def write_dxf(result: Dict[str, Any], path: Path, version: str = "", params: Dict[str, Any] = core.PARAMS) -> List[str]:
    """Write the DXF of a result to `path`; returns the warnings (audit findings, read-back differences)."""
    cfg = params["dxf"]
    version = version or cfg["default_version"]
    if version not in cfg["versions"]:
        raise core.PlanError(f"DXF version {version!r} is not available: choose one of {', '.join(cfg['versions'])}")
    profile = core.load_profile(result["discipline"])
    line_kinds, node_kinds = core._kinds(profile)
    code, scale = _UNITS[profile.get("unidades_salida", cfg["default_units"])]
    doc = ezdxf.new(dxfversion=version, setup=True)
    doc.units = code
    msp = doc.modelspace()
    warnings: List[str] = []

    layers = {k["capa_dxf"] for k in list(line_kinds.values()) + list(node_kinds.values())} | {cfg["tag_layer"], cfg["junction_layer"]}
    for name in sorted(layers):
        doc.layers.add(name)
    height = cfg["text_height_m"] * scale
    size = cfg["node_symbol_size_m"]

    blocks = set()
    for n in result["nodes"]:
        if not n["placed"]:
            continue
        kind = node_kinds[n["kind"]]
        sid = kind["simbolo_2d"]
        if sid not in blocks:
            blocks.add(sid)
            blk = doc.blocks.new(name=f"SYM_{sid.upper()}")
            for p in _symbol_prims(sid, size, scale):
                if p["t"] == "poly":
                    blk.add_lwpolyline(p["pts"], close=True)
                elif p["t"] == "line":
                    blk.add_line(p["a"], p["b"])
                else:
                    blk.add_circle((0, 0), p["r"])
            blk.add_attdef("TAG", (size * scale * 0.6, size * scale * 0.6), height=height)
        ref = msp.add_blockref(f"SYM_{sid.upper()}", (n["x_m"] * scale, n["y_m"] * scale), dxfattribs={"layer": kind["capa_dxf"]})
        ref.add_auto_attribs({"TAG": n["tag"]})
    for n in result["nodes"]:
        if not n["placed"] and n["kind"] == "J":
            msp.add_circle((n["x_m"] * scale, n["y_m"] * scale), 0.05 * scale, dxfattribs={"layer": cfg["junction_layer"]})

    for s in result["stretches"]:
        pts = [(x * scale, y * scale) for x, y in s["points_m"]]
        msp.add_lwpolyline(pts, dxfattribs={"layer": line_kinds[s["kind"]]["capa_dxf"]})
        mid = pts[len(pts) // 2] if len(pts) % 2 else ((pts[len(pts) // 2 - 1][0] + pts[len(pts) // 2][0]) / 2, (pts[len(pts) // 2 - 1][1] + pts[len(pts) // 2][1]) / 2)
        a, b = pts[0], pts[-1]
        angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        if angle > 90 or angle < -90:
            angle += 180
        msp.add_text(s["tag"], height=height, rotation=angle, dxfattribs={"layer": cfg["tag_layer"]}).set_placement(mid, align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)

    path.parent.mkdir(parents=True, exist_ok=True)
    auditor = doc.audit()
    warnings += [f"DXF audit: {e.message}" for e in auditor.errors]
    doc.saveas(str(path))
    back = ezdxf.readfile(str(path))
    expected = len(result["stretches"]) + sum(1 for n in result["nodes"] if n["placed"]) + sum(1 for n in result["nodes"] if not n["placed"] and n["kind"] == "J") + len(result["stretches"])
    if len(back.modelspace()) != expected:
        warnings.append(f"DXF read back has {len(back.modelspace())} entities, expected {expected}")
    return warnings
