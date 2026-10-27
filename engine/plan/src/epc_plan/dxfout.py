"""The DXF deliverable, written from the result of `core.process` with ezdxf (MIT). It is never converted from the SVG of the screen: both come from the same model.

Real units: metres or millimetres, as the discipline says. One layer per kind of element, one block per symbol used, real text for the tags.
"""
import math
from pathlib import Path
from typing import Any, Dict, List

import ezdxf
from epc_dxf import deliverable

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


def _define_block(doc, sid: str, size: float, scale: float, height: float) -> str:
    """The block of a symbol (one per symbol used), with an attribute that holds the tag. Returns its name."""
    name = f"SYM_{sid.upper()}"
    if name in doc.blocks:
        return name
    blk = doc.blocks.new(name=name)
    for p in _symbol_prims(sid, size, scale):
        if p["t"] == "poly":
            blk.add_lwpolyline(p["pts"], close=True)
        elif p["t"] == "line":
            blk.add_line(p["a"], p["b"])
        else:
            blk.add_circle((0, 0), p["r"])
    blk.add_attdef("TAG", (size * scale * 0.6, size * scale * 0.6), height=height)
    return name


def _turn(n: Dict[str, Any]) -> Dict[str, float]:
    """The turn of a symbol (`rot_deg` on the node, clockwise on the screen) as the rotation of its block, counter-clockwise as CAD counts it."""
    rot = (n.get("attrs") or {}).get("rot_deg")
    return {"rotation": -float(rot)} if isinstance(rot, (int, float)) and not isinstance(rot, bool) and rot else {}


def _add_nodes(doc, msp, result, node_kinds, cfg, scale: float, height: float, layer) -> int:
    """Placed nodes as block insertions with their tag, junctions as small circles. Returns how many entities were added."""
    count = 0
    for n in result["nodes"]:
        at = (n["x_m"] * scale, n["y_m"] * scale)
        if n["placed"]:
            kind = node_kinds[n["kind"]]
            block = _define_block(doc, kind["simbolo_2d"], cfg["node_symbol_size_m"], scale, height)
            msp.add_blockref(block, at, dxfattribs={"layer": layer(kind["capa_dxf"]), **_turn(n)}).add_auto_attribs({"TAG": n["tag"]})
            count += 1
        elif n["kind"] == "J":
            msp.add_circle(at, 0.05 * scale, dxfattribs={"layer": layer(cfg["junction_layer"])})
            count += 1
    return count


def _label_position(pts):
    """Middle of a polyline (by vertex count) and the angle of its ends, turned so the text is never upside down."""
    half = len(pts) // 2
    mid = pts[half] if len(pts) % 2 else ((pts[half - 1][0] + pts[half][0]) / 2, (pts[half - 1][1] + pts[half][1]) / 2)
    a, b = pts[0], pts[-1]
    angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    return mid, angle + 180 if (angle > 90 or angle < -90) else angle


def _label(s) -> str:
    """The tag of a stretch, followed by the circuits it carries when it carries any."""
    return s["tag"] + (" [" + ",".join(c["circuit"] for c in s["carries"]) + "]" if s.get("carries") else "")


def _add_stretches(msp, result, line_kinds, cfg, scale: float, height: float, layer) -> int:
    for s in result["stretches"]:
        pts = [(x * scale, y * scale) for x, y in s["points_m"]]
        msp.add_lwpolyline(pts, dxfattribs={"layer": layer(line_kinds[s["kind"]]["capa_dxf"])})
        mid, angle = _label_position(pts)
        msp.add_text(_label(s), height=height, rotation=angle, dxfattribs={"layer": layer(cfg["tag_layer"])}).set_placement(mid, align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
    return 2 * len(result["stretches"])


def write_dxf(result: Dict[str, Any], path: Path, version: str = "", params: Dict[str, Any] = core.PARAMS, layers_file=None) -> List[str]:
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
    layer = lambda base: "plan." + base                          # noqa: E731 - the draft names a layer by its ROLE; the deliverable service gives it its name and look (the catalog the MASTER edits)
    for base in sorted({k["capa_dxf"] for k in list(line_kinds.values()) + list(node_kinds.values())} | {cfg["tag_layer"], cfg["junction_layer"]}):
        doc.layers.add(layer(base))
    height = cfg["text_height_m"] * scale
    expected = _add_nodes(doc, msp, result, node_kinds, cfg, scale, height, layer) + _add_stretches(msp, result, line_kinds, cfg, scale, height, layer)

    path.parent.mkdir(parents=True, exist_ok=True)
    warnings = [f"DXF audit: {e.message}" for e in doc.audit().errors]
    deliverable.finish_draft(doc, path, layers_file)
    back = len(ezdxf.readfile(str(path)).modelspace())
    if back != expected:
        warnings.append(f"DXF read back has {back} entities, expected {expected}")
    return warnings
