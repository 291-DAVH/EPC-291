"""Clash detection between footprints of different disciplines. Pure: footprints and rules in, clashes out; the same input gives the same output.

Two elements of different disciplines clash when
  hard         their bodies occupy the same space (the 3D gap between them is zero or negative);
  clearance    they do not touch but are closer than the separation the rules ask for those two kinds;
  maintenance  one of them sits in the free space an equipment asks for around itself (`clear_m`).
Elements of the same discipline never clash here: coordinating inside a discipline is that discipline's own work.
"""
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from epc_plan import core

HERE = Path(__file__).resolve().parent
Point = Tuple[float, float]
RANK = {"hard": 3, "maintenance": 2, "clearance": 1}


def default_rules() -> List[Dict[str, Any]]:
    return json.loads((HERE / "clash_rules.json").read_text(encoding="utf-8"))["rules"]


def rule_key(r: Dict[str, Any]) -> str:
    return "|".join([r.get("a", "*"), r.get("b", "*"), ",".join(sorted(r.get("kinds_a", []))), ",".join(sorted(r.get("kinds_b", [])))])


def merge_rules(*layers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rule lists in order of authority (the engine's, the company's, the project's): a later rule replaces an earlier one with the same pair of disciplines and kinds,
    and `{"disabled": true}` removes it."""
    merged: Dict[str, Dict[str, Any]] = {}
    for layer in layers:
        for r in layer or []:
            if r.get("disabled"):
                merged.pop(rule_key(r), None)
            else:
                merged[rule_key(r)] = r
    return list(merged.values())


# ---------------------------------------------------------------- geometry
def _cross(o: Point, a: Point, b: Point) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def _seg_closest(a0: Point, a1: Point, b0: Point, b1: Point) -> Tuple[float, Point, Point]:
    """Distance between two segments and the closest point of each (zero distance, same point, where they cross)."""
    d1, d2 = _cross(a0, a1, b0), _cross(a0, a1, b1)
    d3, d4 = _cross(b0, b1, a0), _cross(b0, b1, a1)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)) and d1 != 0 and d2 != 0 and d3 != 0 and d4 != 0:
        t = d3 / (d3 - d4)
        p = (a0[0] + t * (a1[0] - a0[0]), a0[1] + t * (a1[1] - a0[1]))
        return 0.0, p, p
    best: Optional[Tuple[float, Point, Point]] = None
    for p, seg, flip in ((a0, (b0, b1), False), (a1, (b0, b1), False), (b0, (a0, a1), True), (b1, (a0, a1), True)):
        q, _, d = core._project(p, seg[0], seg[1])
        cand = (d, q, p) if flip else (d, p, q)
        if best is None or cand[0] < best[0]:
            best = cand
    return best  # type: ignore[return-value]


def _segments(item: Dict[str, Any]) -> List[Tuple[Point, Point]]:
    pts = [tuple(p) for p in item["points"]]
    return [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)] if len(pts) > 1 else [(pts[0], pts[0])]


def plan_gap(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[float, Point]:
    """Horizontal gap between the bodies (negative when they overlap in plan) and the point halfway between the closest points."""
    best: Optional[Tuple[float, Point, Point]] = None
    for sa in _segments(a):
        for sb in _segments(b):
            cand = _seg_closest(sa[0], sa[1], sb[0], sb[1])
            if best is None or cand[0] < best[0]:
                best = cand
    assert best is not None
    d, pa, pb = best
    return d - (a["width_m"] + b["width_m"]) / 2, ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)


def height_gap(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    """Vertical gap between the bodies (negative when their heights overlap)."""
    return max(a["z0"], b["z0"]) - min(a["z1"], b["z1"])


def gap_3d(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[float, float, float, Point]:
    h, at = plan_gap(a, b)
    v = height_gap(a, b)
    if h <= 0 and v <= 0:
        return max(h, v), h, v, at                              # inside each other: how deep, the larger (less negative) of the two overlaps
    return math.hypot(max(h, 0.0), max(v, 0.0)), h, v, at


# ---------------------------------------------------------------- rules
def _score(rule: Dict[str, Any], a: Dict[str, Any], b: Dict[str, Any]) -> Optional[int]:
    """How specifically a rule names this pair (None when it does not apply); the most specific wins."""
    best: Optional[int] = None
    for x, y in ((a, b), (b, a)):
        if rule.get("a", "*") not in ("*", x["discipline"]) or rule.get("b", "*") not in ("*", y["discipline"]):
            continue
        if rule.get("kinds_a") and x["kind"] not in rule["kinds_a"]:
            continue
        if rule.get("kinds_b") and y["kind"] not in rule["kinds_b"]:
            continue
        s = (rule.get("a", "*") != "*") + (rule.get("b", "*") != "*") + bool(rule.get("kinds_a")) + bool(rule.get("kinds_b"))
        best = s if best is None else max(best, s)
    return best


def rule_for(rules: List[Dict[str, Any]], a: Dict[str, Any], b: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    scored = [(s, r.get("clearance_m", 0.0), r) for r in rules for s in [_score(r, a, b)] if s is not None]
    return max(scored, key=lambda t: (t[0], t[1]))[2] if scored else None


# ---------------------------------------------------------------- detection
def _pair_id(a: Dict[str, Any], b: Dict[str, Any]) -> str:
    keys = sorted([f"{a['sheet']}:{a['id']}", f"{b['sheet']}:{b['id']}"])
    return hashlib.sha1("|".join(keys).encode()).hexdigest()[:10]


def _classify(a: Dict[str, Any], b: Dict[str, Any], rule: Optional[Dict[str, Any]]) -> Optional[Tuple[str, float, Point, float]]:
    """(type, gap, point, asked clearance) for a pair, or None when it is fine or the rules say to ignore it."""
    if rule and rule.get("ignore"):
        return None
    gap, h, v, at = gap_3d(a, b)
    if gap <= 0:
        return "hard", gap, at, 0.0
    asked = float((rule or {}).get("clearance_m", 0.0))
    if v <= 0:                                                  # same heights: the free space of an equipment, around it in plan
        free = max(a["clear_m"], b["clear_m"])
        if free > 0 and h < free:
            return "maintenance", h, at, free
    if asked > 0 and gap < asked:
        return "clearance", gap, at, asked
    return None


def _bounds(item: Dict[str, Any]) -> Tuple[float, float, float, float]:
    xs, ys = [p[0] for p in item["points"]], [p[1] for p in item["points"]]
    r = item["width_m"] / 2
    return min(xs) - r, max(xs) + r, min(ys) - r, max(ys) + r


def _candidates(items: List[Dict[str, Any]], margin: float):
    """Pairs of different disciplines whose boxes (grown by `margin`) meet: a sweep along x, so thousands of elements are not compared all against all."""
    boxes = sorted(((_bounds(it), it) for it in items), key=lambda t: t[0][0])
    for i, (bi, a) in enumerate(boxes):
        for bj, b in boxes[i + 1:]:
            if bj[0] - bi[1] > margin:
                break
            if a["discipline"] == b["discipline"] or bj[2] - bi[3] > margin or bi[2] - bj[3] > margin or height_gap(a, b) > margin:
                continue
            yield a, b


def detect(items: List[Dict[str, Any]], rules: Optional[List[Dict[str, Any]]] = None, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Every clash between footprints of different disciplines, worst first. One entry per pair of elements, with the id that stays the same while the pair does."""
    params = params or core.PARAMS
    rules = default_rules() if rules is None else rules
    if len(items) > params["coordination"]["max_items"]:
        raise core.PlanError(f"too many elements to compare ({len(items)}): the limit is {params['coordination']['max_items']}")
    margin = max([r.get("clearance_m", 0.0) for r in rules] + [0.0]) + 2 * max([it["clear_m"] for it in items] + [0.0]) + 0.01
    found: List[Dict[str, Any]] = []
    for a, b in _candidates(items, margin):
        res = _classify(a, b, rule_for(rules, a, b))
        if res is None:
            continue
        kind, gap, at, asked = res
        found.append({"id": _pair_id(a, b), "type": kind, "severity": "error" if kind == "hard" else "warning", "gap_m": round(gap, 3), "clearance_m": round(asked, 3),
                      "point_m": [round(at[0], 3), round(at[1], 3)], "level": a["level"], "level_number": a["level_number"], "a": _ref(a), "b": _ref(b)})
    found.sort(key=lambda c: (-RANK[c["type"]], c["gap_m"], c["id"]))
    return found


def _ref(it: Dict[str, Any]) -> Dict[str, Any]:
    return {k: it[k] for k in ("sheet", "discipline", "level", "id", "tag", "kind", "shape")}
