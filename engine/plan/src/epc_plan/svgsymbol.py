"""A symbol of the plan drawn as an SVG: the primitives the editor and the DXF use, read from the file.

The SVG is the source: whoever redraws the symbol edits the file. Coordinates are those of the unit symbol (a viewBox of -0.5 -0.5 1 1: the symbol fills [-0.5, 0.5]) and the shapes understood are
rect and circle centred on the origin, line, polyline and polygon. Anything else is ignored.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

NS = "{http://www.w3.org/2000/svg}"


def _points(text: str) -> List[List[float]]:
    nums = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]
    return [[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)]


def _segments(points: List[List[float]], closed: bool) -> List[Dict[str, Any]]:
    pairs = list(zip(points, points[1:] + ([points[0]] if closed and points else [])))
    return [{"t": "line", "a": a, "b": b} for a, b in pairs if a != b]


def _shape(el: ET.Element) -> List[Dict[str, Any]]:
    tag = el.tag.replace(NS, "")
    if tag == "rect":
        return [{"t": "rect", "w": float(el.get("width", 0)), "h": float(el.get("height", 0))}]
    if tag == "circle":
        return [{"t": "circle", "r": float(el.get("r", 0))}]
    if tag == "line":
        return [{"t": "line", "a": [float(el.get("x1", 0)), float(el.get("y1", 0))], "b": [float(el.get("x2", 0)), float(el.get("y2", 0))]}]
    if tag in ("polyline", "polygon"):
        return _segments(_points(el.get("points", "")), tag == "polygon")
    return []


def prims(path: Path) -> List[Dict[str, Any]]:
    """The primitives of the symbol in an SVG file, in drawing order."""
    return [p for el in ET.parse(path).getroot().iter() for p in _shape(el)]
