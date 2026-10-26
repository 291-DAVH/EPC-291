"""The work of the module as pure functions: the same input gives the same output; nothing here reads the network, the environment or the backend.

A drawing arrives in the coordinates of the view (units of the screen, y down). `process` turns it into real metres from the origin the person set,
joins the lines into a graph, gives every element its tag, works out lengths, the schedule of what was drawn, the real route of each circuit and, when
the rules allow it, the invert levels of a network from its outlet.
"""
import copy
import json
import math
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
PARAMS = json.loads((HERE / "params.json").read_text(encoding="utf-8"))
SYMBOLS = json.loads((HERE / "symbols.json").read_text(encoding="utf-8"))["symbols"]
_RULES_PLACES = (HERE / "knowledge" / "rules.json", HERE.parents[1] / "knowledge" / "rules.json")


from epc_plan import routing   # noqa: E402


class PlanError(ValueError):
    """The drawing cannot be processed: the message says what to fix."""


# ---------------------------------------------------------------- data files
def load_profile(profile_id: str) -> Dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_]+", profile_id or ""):
        raise PlanError(f"discipline {profile_id!r} is not valid")
    path = HERE / "profiles" / f"{profile_id}.json"
    if not path.is_file():
        raise PlanError(f"unknown discipline {profile_id!r}: profiles are {', '.join(profiles())}")
    return json.loads(path.read_text(encoding="utf-8"))


def profiles() -> List[str]:
    return sorted(p.stem for p in (HERE / "profiles").glob("*.json"))


def load_rules() -> List[Dict[str, Any]]:
    for place in _RULES_PLACES:
        if place.is_file():
            return json.loads(place.read_text(encoding="utf-8")).get("rules", [])
    return []


# ---------------------------------------------------------------- level, scale, origin
def parse_level(level: str, params: Dict[str, Any] = PARAMS) -> int:
    """`L0` is the ground level, `L1`, `L2`... go up, `L-1`, `L-2`... go down."""
    if not isinstance(level, str) or not re.fullmatch(params["levels"]["pattern"], level):
        raise PlanError(f"level {level!r} is not valid: use L0 for the ground level, L1, L2... upwards and L-1, L-2... downwards")
    return int(level[1:])


def metres_per_unit(scale: Dict[str, Any], params: Dict[str, Any] = PARAMS) -> float:
    """Real metres of one unit of the view, from two points the person marked and the real distance between them."""
    try:
        (x1, y1), (x2, y2) = scale["p1"], scale["p2"]
        real = float(scale["distance_m"])
    except (KeyError, TypeError, ValueError):
        raise PlanError("the scale needs two points (p1, p2) and the real distance between them (distance_m)")
    drawn = math.hypot(x2 - x1, y2 - y1)
    if drawn < params["geometry"]["min_calibration_units"]:
        raise PlanError("the two calibration points are the same point")
    if real < params["geometry"]["min_scale_distance_m"]:
        raise PlanError("the real distance of the scale must be greater than zero")
    return real / drawn


def to_world(point, origin, k: float) -> Tuple[float, float]:
    """View units (y down) to metres from the origin with y up, as in CAD."""
    return ((point[0] - origin[0]) * k, -(point[1] - origin[1]) * k)


# ---------------------------------------------------------------- geometry helpers
def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _project(p, a, b) -> Tuple[Tuple[float, float], float, float]:
    """Closest point of segment ab to p: (point, fraction along ab 0..1, distance)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
    q = (a[0] + t * dx, a[1] + t * dy)
    return q, t, _dist(p, q)


def _polyline_length(points) -> float:
    return sum(_dist(points[i], points[i + 1]) for i in range(len(points) - 1))


def _locate(points, p) -> Tuple[float, float]:
    """(arc length from the start of the polyline to the closest point to p, distance to the polyline)."""
    best = (0.0, float("inf"))
    run = 0.0
    for i in range(len(points) - 1):
        q, t, d = _project(p, points[i], points[i + 1])
        if d < best[1]:
            best = (run + t * _dist(points[i], points[i + 1]), d)
        run += _dist(points[i], points[i + 1])
    return best


def _slice(points, s0: float, s1: float) -> List[Tuple[float, float]]:
    """The part of the polyline between the arc lengths s0 and s1, with its end points exactly at them."""
    out: List[Tuple[float, float]] = []
    run = 0.0
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        seg = _dist(a, b)
        lo, hi = run, run + seg
        if hi >= s0 and lo <= s1 and seg > 0:
            t0 = max(0.0, (s0 - lo) / seg)
            t1 = min(1.0, (s1 - lo) / seg)
            p0 = (a[0] + t0 * (b[0] - a[0]), a[1] + t0 * (b[1] - a[1]))
            p1 = (a[0] + t1 * (b[0] - a[0]), a[1] + t1 * (b[1] - a[1]))
            if not out or _dist(out[-1], p0) > 1e-9:
                out.append(p0)
            if _dist(out[-1], p1) > 1e-9:
                out.append(p1)
        run = hi
    return out if len(out) >= 2 else [points[0], points[-1]]


def _crossing(a1, a2, b1, b2) -> Optional[Tuple[float, float]]:
    """Point where two segments cross strictly inside both, or None."""
    d = (a2[0] - a1[0]) * (b2[1] - b1[1]) - (a2[1] - a1[1]) * (b2[0] - b1[0])
    if abs(d) < 1e-12:
        return None
    t = ((b1[0] - a1[0]) * (b2[1] - b1[1]) - (b1[1] - a1[1]) * (b2[0] - b1[0])) / d
    u = ((b1[0] - a1[0]) * (a2[1] - a1[1]) - (b1[1] - a1[1]) * (a2[0] - a1[0])) / d
    if 1e-9 < t < 1 - 1e-9 and 1e-9 < u < 1 - 1e-9:
        return (a1[0] + t * (a2[0] - a1[0]), a1[1] + t * (a2[1] - a1[1]))
    return None


# ---------------------------------------------------------------- tags
def _tag(prefix: str, n: int, params: Dict[str, Any]) -> str:
    return f"{prefix}-{n:0{params['tags']['digits']}d}"


class _Tagger:
    """Correlative tags per prefix. A tag the person already gave is kept; the others take the next free number."""

    def __init__(self, params, warnings):
        self.params, self.warnings, self.used, self.next = params, warnings, set(), {}

    def reserve(self, tag: str, what: str) -> bool:
        if tag in self.used:
            self.warnings.append(f"duplicated tag {tag} ({what}): the later one is given a new tag")
            return False
        self.used.add(tag)
        return True

    def give(self, prefix: str) -> str:
        n = self.next.get(prefix, 0)
        while True:
            n += 1
            tag = _tag(prefix, n, self.params)
            if tag not in self.used:
                self.next[prefix] = n
                self.used.add(tag)
                return tag


# ---------------------------------------------------------------- the graph
def _kinds(profile) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return {k["id"]: k for k in profile["tramos"]}, {k["id"]: k for k in profile["nodos"]}


def _check_document(doc: Dict[str, Any], params) -> None:
    if not isinstance(doc, dict) or doc.get("schema_version") != "1.0":
        raise PlanError("the drawing must be an object with schema_version 1.0")
    lim = params["limits"]
    if len(doc.get("lines", [])) > lim["max_lines"] or len(doc.get("nodes", [])) > lim["max_nodes"]:
        raise PlanError(f"the drawing is too big: up to {lim['max_lines']} lines and {lim['max_nodes']} nodes")
    for ln in doc.get("lines", []):
        pts = ln.get("points", [])
        if len(pts) < 2:
            raise PlanError(f"line {ln.get('id', '?')} needs at least two points")
        if len(pts) > lim["max_points_per_line"]:
            raise PlanError(f"line {ln.get('id', '?')} has too many points (up to {lim['max_points_per_line']})")


class _Graph:
    """The nodes of the drawing (placed ones first) and the tolerance within which a point counts as being at a node."""

    def __init__(self, nodes: List[Dict[str, Any]], tol: float):
        self.tol = tol
        self.nodes: List[Dict[str, Any]] = [{"id": n["id"], "kind": n.get("kind"), "x": n["x"], "y": n["y"], "placed": True, "attrs": n.get("attrs", {}), "tag": n.get("tag")} for n in nodes]

    def near(self, p) -> Optional[Dict[str, Any]]:
        best = None
        for g in self.nodes:
            d = _dist(p, (g["x"], g["y"]))
            if d <= self.tol and (best is None or d < best[0]):
                best = (d, g)
        return best[1] if best else None

    def add(self, p, kind: str) -> Dict[str, Any]:
        g = {"id": f"auto:{kind}{sum(1 for x in self.nodes if x['kind'] == kind) + 1}", "kind": kind, "x": p[0], "y": p[1], "placed": False, "attrs": {}, "tag": None}
        self.nodes.append(g)
        return g


def _on_another_line(lines, own, end, tol) -> Optional[Tuple[float, float]]:
    """The point of another line the end lies on (a T), or None."""
    for other in lines:
        if other is own:
            continue
        s, d = _locate(other["points"], end)
        if d <= tol:
            return _point_at(other["points"], s)
    return None


def _join_line_ends(graph: _Graph, lines, warnings: List[str]) -> None:
    """Every line end connects to a node, to another line (a junction is made there) or stays free (and is reported)."""
    for ln in lines:
        for end in (ln["points"][0], ln["points"][-1]):
            if graph.near(end):
                continue
            joined = _on_another_line(lines, ln, end, graph.tol)
            if joined is not None:
                graph.add(joined, "J")
            else:
                graph.add(end, "E")
                warnings.append(f"line {ln['id']} has a free end at ({end[0]:.2f}, {end[1]:.2f}) m")


def _cuts(graph: _Graph, pts) -> List[Tuple[float, Dict[str, Any]]]:
    """The nodes that lie on a polyline, in order along it (a node is listed once in a row)."""
    found = []
    for g in graph.nodes:
        s, d = _locate(pts, (g["x"], g["y"]))
        if d <= graph.tol:
            found.append((s, g))
    found.sort(key=lambda c: (c[0], c[1]["id"]))
    merged: List[Tuple[float, Dict[str, Any]]] = []
    for s, g in found:
        if not (merged and merged[-1][1] is g):
            merged.append((s, g))
    return merged


def _stretches_of(ln, cuts) -> List[Dict[str, Any]]:
    out = []
    for (s0, g0), (s1, g1) in zip(cuts, cuts[1:]):
        if g0 is g1 or s1 - s0 < 1e-9:
            continue
        geom = _slice(ln["points"], s0, s1)
        out.append({"line": ln["id"], "kind": ln["kind"], "from": g0["id"], "to": g1["id"], "points": geom, "length_m": _polyline_length(geom), "attrs": ln.get("attrs", {}), "circuit": ln.get("circuit")})
    return out


def _cut_lines(graph: _Graph, lines, warnings: List[str]) -> List[Dict[str, Any]]:
    """Every line is cut where a node lies on it; each piece between two nodes is a stretch."""
    stretches: List[Dict[str, Any]] = []
    for ln in lines:
        cuts = _cuts(graph, ln["points"])
        if len(cuts) < 2:
            warnings.append(f"line {ln['id']} does not reach two nodes")
            continue
        stretches += _stretches_of(ln, cuts)
        if _polyline_length(ln["points"]) <= 0:
            warnings.append(f"line {ln['id']} has no length")
    return stretches


def _crossings_between(la, lb):
    for a in range(len(la["points"]) - 1):
        for b in range(len(lb["points"]) - 1):
            p = _crossing(la["points"][a], la["points"][a + 1], lb["points"][b], lb["points"][b + 1])
            if p:
                yield p


def _report_crossings(graph: _Graph, lines, warnings: List[str]) -> None:
    """Two lines that only cross are not connected: the person has to place a node, and a warning says so."""
    for i, la in enumerate(lines):
        for lb in lines[i + 1:]:
            for p in _crossings_between(la, lb):
                if not graph.near(p):
                    warnings.append(f"lines {la['id']} and {lb['id']} cross at ({p[0]:.2f}, {p[1]:.2f}) m without a node: they are not connected")


def build_graph(nodes: List[Dict[str, Any]], lines: List[Dict[str, Any]], tol: float) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str]]:
    """Join placed nodes and drawn lines into a graph, all in metres.

    A line end that lies on another line (a *T*) or on a placed node connects there; a placed node lying on a line splits it. Two lines that only cross are
    NOT connected: the person must place a node. Returns (graph nodes, stretches, warnings)."""
    warnings: List[str] = []
    graph = _Graph(nodes, tol)
    _join_line_ends(graph, lines, warnings)
    stretches = _cut_lines(graph, lines, warnings)
    _report_crossings(graph, lines, warnings)
    return graph.nodes, stretches, warnings


def _point_at(points, s: float) -> Tuple[float, float]:
    run = 0.0
    for i in range(len(points) - 1):
        seg = _dist(points[i], points[i + 1])
        if run + seg >= s - 1e-12 and seg > 0:
            t = (s - run) / seg
            return (points[i][0] + t * (points[i + 1][0] - points[i][0]), points[i][1] + t * (points[i + 1][1] - points[i][1]))
        run += seg
    return points[-1]


# ---------------------------------------------------------------- flow and invert levels
def _walk_from(outlet: str, stretches, ids) -> Tuple[Dict[str, Dict[str, Any]], set]:
    """Breadth-first from the outlet: the distance of every node to it and the stretch it was reached by (that stretch drains toward the outlet)."""
    adj: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {i: [] for i in ids}
    for s in stretches:
        adj[s["from"]].append((s["to"], s))
        adj[s["to"]].append((s["from"], s))
    info: Dict[str, Dict[str, Any]] = {outlet: {"distance_m": 0.0, "stretch": None}}
    queue, reached = [outlet], set()
    while queue:
        cur = queue.pop(0)
        for nxt, st in sorted(adj[cur], key=lambda e: (e[0], e[1]["line"])):
            if nxt not in info:
                info[nxt] = {"distance_m": info[cur]["distance_m"] + st["length_m"], "stretch": st}
                st["flows_to"], st["flows_from"] = cur, nxt
                reached.add(id(st))
                queue.append(nxt)
    return info, reached


def orient_from_outlet(gnodes, stretches, outlet: str, warnings: List[str]) -> Dict[str, Dict[str, Any]]:
    """Walk the network from its outlet: every stretch gets the node it drains to and the node it comes from, and every node its distance to the outlet."""
    ids = {g["id"] for g in gnodes}
    if outlet not in ids:
        raise PlanError(f"the outlet {outlet!r} is not a node of the drawing")
    info, reached = _walk_from(outlet, stretches, ids)
    for st in stretches:
        if id(st) not in reached and st["from"] in info and st["to"] in info:
            warnings.append(f"stretch {st['line']} ({st['from']}-{st['to']}) closes a loop: a network with a single outlet has none")
    for i in sorted(ids - set(info)):
        warnings.append(f"node {i} is not connected to the outlet {outlet}")
    return info


def _slope_table(rules: List[Dict[str, Any]], profile_id: str, warnings: List[str]) -> Optional[Tuple[Dict[str, Any], Dict[int, float]]]:
    """The rule that gives the minimum slope for the discipline and its usable rows; None (with a warning) when there is none: nothing is invented."""
    rule = next((r for r in rules if r.get("topic") == "min_slope" and r.get("applies_to") == profile_id), None)
    if rule is None:
        warnings.append("no minimum-slope rule for this discipline: invert levels are not calculated")
        return None
    table = {row["diameter_mm"]: row["slope_pct"] for row in rule["table"] if row.get("slope_pct") is not None}
    if not table:
        warnings.append(f"the rule {rule['id']} has no slope values yet: invert levels are not calculated")
        return None
    if rule.get("status", "pending") != "approved":
        warnings.append(f"the rule {rule['id']} is {rule.get('status', 'pending')}: the invert levels are provisional")
    return rule, table


def _slope_for(stretch, table: Dict[int, float]) -> Optional[float]:
    """The slope for the diameter of a stretch: its own row, else the next bigger diameter that has one."""
    diameter = (stretch.get("attrs") or {}).get("diameter_mm")
    if diameter in table:
        return table[diameter]
    bigger = [d for d in sorted(table) if diameter is not None and d >= diameter]
    return table[bigger[0]] if bigger else None


def derive_inverts(gnodes, stretches, info, outlet: str, outlet_invert_m: float, profile_id: str, rules: List[Dict[str, Any]], warnings: List[str]) -> Optional[Dict[str, Any]]:
    """Invert level of every node: the outlet's, rising upstream by the slope the rule gives for the diameter of the stretch. Without a usable rule nothing is invented."""
    found = _slope_table(rules, profile_id, warnings)
    if found is None:
        return None
    rule, table = found
    levels = {outlet: outlet_invert_m}
    for node_id in sorted(info, key=lambda i: (info[i]["distance_m"], i)):
        st = info[node_id]["stretch"]
        if st is None:
            continue
        slope = _slope_for(st, table)
        if slope is None:
            warnings.append(f"stretch {st['line']} has no diameter with a slope rule: node {node_id} gets no invert level")
            continue
        st["slope_pct"] = slope
        if st["flows_to"] in levels:
            levels[node_id] = levels[st["flows_to"]] + slope / 100.0 * st["length_m"]
    status = rule.get("status", "pending")
    return {"rule": rule["id"], "status": status, "validated": status == "approved", "invert_m": {k: round(v, 4) for k, v in sorted(levels.items())}}


# ---------------------------------------------------------------- the whole job
def _read_nodes(doc, node_kinds, profile_id: str, origin, k: float) -> List[Dict[str, Any]]:
    nodes = []
    for n in doc.get("nodes", []):
        if n.get("kind") not in node_kinds:
            raise PlanError(f"node {n.get('id', '?')}: kind {n.get('kind')!r} does not exist in the discipline {profile_id}")
        x, y = to_world((n["x"], n["y"]), origin, k)
        nodes.append({"id": n["id"], "kind": n["kind"], "x": x, "y": y, "attrs": n.get("attrs", {}), "tag": n.get("tag")})
    return nodes


def _read_lines(doc, line_kinds, profile_id: str, origin, k: float) -> List[Dict[str, Any]]:
    lines = []
    for ln in doc.get("lines", []):
        if ln.get("kind") not in line_kinds:
            raise PlanError(f"line {ln.get('id', '?')}: kind {ln.get('kind')!r} does not exist in the discipline {profile_id}")
        lines.append({"id": ln["id"], "kind": ln["kind"], "points": [to_world(p, origin, k) for p in ln["points"]], "attrs": ln.get("attrs", {}), "tag": ln.get("tag"), "circuit": ln.get("circuit")})
    return lines


def _read_circuits(doc) -> List[Dict[str, Any]]:
    """The circuits to route: a tag of the board, an origin node, a destination node, optional nodes to pass through and the number of parallel cables (ternas)."""
    return [{"tag": c.get("tag", ""), "from": c.get("from", ""), "to": c.get("to", ""), "via": list(c.get("via", [])), "ternas": c.get("ternas", 1)} for c in doc.get("circuits", [])]


def _check_unique_ids(nodes, lines) -> None:
    ids = [x["id"] for x in nodes] + [x["id"] for x in lines]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        raise PlanError(f"the id {dup!r} is used twice: ids must be unique")


def _reserve_node_tags(gnodes, tagger) -> None:
    for x in gnodes:
        if x["placed"] and x["tag"] and not tagger.reserve(x["tag"], f"node {x['id']}"):
            x["tag"] = None


def _give_node_tags(gnodes, node_kinds, tagger, params) -> None:
    for x in gnodes:
        if not x["tag"]:
            prefix = node_kinds[x["kind"]]["prefijo_tag"] if x["placed"] else params["tags"]["junction_prefix" if x["kind"] == "J" else "end_prefix"]
            x["tag"] = tagger.give(prefix)


def _tag_stretches(stretches, line_tag, separator: str) -> None:
    """A line cut into several stretches gives them `<line tag><separator>1`, `...2`; a line with one stretch keeps its tag."""
    count: Dict[str, int] = {}
    for s in stretches:
        s["line_tag"] = line_tag[s["line"]]
        count[s["line"]] = count.get(s["line"], 0) + 1
    seen: Dict[str, int] = {}
    for s in stretches:
        seen[s["line"]] = seen.get(s["line"], 0) + 1
        s["tag"] = s["line_tag"] if count[s["line"]] == 1 else f"{s['line_tag']}{separator}{seen[s['line']]}"
        s["length_m"] = round(s["length_m"], 4)


def _assign_tags(gnodes, lines, stretches, node_kinds, line_kinds, params, warnings) -> Dict[str, str]:
    """Tags of nodes, lines and stretches. Returns the tag of every line. Tags the person wrote are reserved first so the correlative never takes one."""
    tagger = _Tagger(params, warnings)
    _reserve_node_tags(gnodes, tagger)
    for ln in lines:
        if ln["tag"] and not tagger.reserve(ln["tag"], f"line {ln['id']}"):
            ln["tag"] = None
    _give_node_tags(gnodes, node_kinds, tagger, params)
    line_tag = {ln["id"]: ln["tag"] or tagger.give(line_kinds[ln["kind"]]["prefijo_tag"]) for ln in lines}
    _tag_stretches(stretches, line_tag, params["tags"]["stretch_separator"])
    return line_tag


def _network(doc, gnodes, stretches, profile_id: str, rules, warnings) -> Optional[Dict[str, Any]]:
    """Orientation toward the outlet and invert levels, when the drawing names an outlet."""
    outlet = doc.get("outlet")
    if not outlet:
        return None
    info = orient_from_outlet(gnodes, stretches, outlet, warnings)
    flow = None
    if doc.get("outlet_invert_m") is not None:
        flow = derive_inverts(gnodes, stretches, info, outlet, float(doc["outlet_invert_m"]), profile_id, rules, warnings)
    else:
        warnings.append("the outlet has no invert level: levels are not calculated")
    for x in gnodes:
        x["distance_to_outlet_m"] = round(info[x["id"]]["distance_m"], 4) if x["id"] in info else None
    return flow


def _node_json(x) -> Dict[str, Any]:
    out = {"id": x["id"], "tag": x["tag"], "kind": x["kind"], "placed": x["placed"], "x_m": round(x["x"], 4), "y_m": round(x["y"], 4), "attrs": x["attrs"]}
    if "distance_to_outlet_m" in x:
        out["distance_to_outlet_m"] = x["distance_to_outlet_m"]
    return out


def _stretch_json(s) -> Dict[str, Any]:
    out = {"tag": s["tag"], "line": s["line"], "line_tag": s["line_tag"], "kind": s["kind"], "from": s["from"], "to": s["to"], "length_m": s["length_m"],
           "points_m": [[round(p[0], 4), round(p[1], 4)] for p in s["points"]], "attrs": s["attrs"], "circuit": s["circuit"]}
    if "flows_to" in s:
        out.update(flows_to=s["flows_to"], flows_from=s["flows_from"])
    if "slope_pct" in s:
        out["slope_pct"] = s["slope_pct"]
    if "carries" in s:
        out.update(carries=s["carries"], cables=sum(c["ternas"] for c in s["carries"]))
    return out


def process(document: Dict[str, Any], params: Dict[str, Any] = PARAMS, rules: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Takes the drawing document (schema/input.schema.json) and returns the result document (schema/output.schema.json). Never changes its input."""
    doc = copy.deepcopy(document)
    _check_document(doc, params)
    rules = load_rules() if rules is None else rules
    plan = doc.get("plan") or {}
    level = plan.get("level", params["levels"]["ground"])
    level_number = parse_level(level, params)
    k = metres_per_unit(plan.get("scale") or {}, params)
    origin = plan.get("origin", [0.0, 0.0])
    profile = load_profile(doc.get("discipline", ""))
    line_kinds, node_kinds = _kinds(profile)
    nodes = _read_nodes(doc, node_kinds, profile["id"], origin, k)
    lines = _read_lines(doc, line_kinds, profile["id"], origin, k)
    _check_unique_ids(nodes, lines)

    gnodes, stretches, warnings = build_graph(nodes, lines, params["geometry"]["snap_tolerance_m"])
    line_tag = _assign_tags(gnodes, lines, stretches, node_kinds, line_kinds, params, warnings)
    routes = routing.route_circuits(gnodes, stretches, _read_circuits(doc), {k for k, v in line_kinds.items() if v.get("un_solo_circuito")}, warnings)
    flow = _network(doc, gnodes, stretches, profile["id"], rules, warnings)
    return {
        "schema_version": "1.0", "plan": {"id": plan.get("id", ""), "level": level, "level_number": level_number, "metres_per_unit": k, "origin": list(origin)},
        "discipline": profile["id"], "nodes": [_node_json(x) for x in gnodes], "stretches": [_stretch_json(s) for s in stretches],
        "schedule": _schedule(gnodes, stretches, lines, line_tag, line_kinds, node_kinds), "circuits": routes, "network": flow, "rules_used": [flow["rule"]] if flow else [], "warnings": warnings,
    }


def _kind_totals(stretches, line_kinds) -> Dict[str, Dict[str, Any]]:
    out = {}
    for kid in line_kinds:
        sel = [s for s in stretches if s["kind"] == kid]
        out[kid] = {"lines": len({s["line"] for s in sel}), "stretches": len(sel), "length_m": round(sum(s["length_m"] for s in sel), 4)}
    return out


def _circuit_routes(stretches) -> Dict[str, Dict[str, Any]]:
    """The real route of every circuit a line references: its stretches and the total length."""
    routes: Dict[str, Dict[str, Any]] = {}
    for s in stretches:
        if s.get("circuit"):
            r = routes.setdefault(s["circuit"], {"stretches": [], "length_m": 0.0})
            r["stretches"].append(s["tag"])
            r["length_m"] = round(r["length_m"] + s["length_m"], 4)
    return dict(sorted(routes.items()))


def _containers(stretches) -> List[Dict[str, Any]]:
    """What each stretch that carries routed circuits holds: the circuits and how many cables (the sum of their ternas)."""
    return [{"tag": s["tag"], "kind": s["kind"], "circuits": [c["circuit"] for c in s["carries"]], "cables": sum(c["ternas"] for c in s["carries"])} for s in stretches if s.get("carries")]


def _schedule(gnodes, stretches, lines, line_tag, line_kinds, node_kinds) -> Dict[str, Any]:
    nodes = {kid: sum(1 for g in gnodes if g["placed"] and g["kind"] == kid) for kid in node_kinds}
    per_line = {line_tag[ln["id"]]: round(sum(s["length_m"] for s in stretches if s["line"] == ln["id"]), 4) for ln in lines}
    return {"lines": _kind_totals(stretches, line_kinds), "nodes": nodes, "circuit_routes": _circuit_routes(stretches), "length_by_line_m": dict(sorted(per_line.items())),
            "containers": _containers(stretches), "total_length_m": round(sum(s["length_m"] for s in stretches), 4)}
