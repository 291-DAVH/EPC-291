"""Automatic design in two steps, so the person sees and can change the first before the second.

1. The runs (`propose_runs`): the trays and conduits for the loads placed in the drawing, as few and as straight as possible. A trunk is a long straight tray along a row (or a column) of loads, trunks hang
   from one straight spine that starts at the board, and each load is reached by a short straight conduit perpendicular to its trunk. No line has a bend: the only corners are the T junctions where a run
   leaves another. Both orientations (rows or columns) and every number of trunks are tried and the shortest layout is kept.
2. The wiring (`propose_wiring`): once the runs are in the drawing, a circuit for each room and family of load (the room is where the load lies; at most 15 lighting outlets per circuit), routed over the
   runs that are drawn, and checked with the engine: a circuit whose loads the runs do not reach is said.
Cables are not lines of their own: a circuit's cable follows the runs it is routed through.

Pure: a drawing document (and the rooms for the wiring) in, a proposal out; it changes nothing. Units are those of the view. The limits per circuit and the power per outlet are typical values in
`params.json` (`design`): the engineer confirms them against the standard of the project.
"""
import copy
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple

from epc_plan import core

Point = Tuple[float, float]
EPS = 1e-9
MAX_TRUNKS = 10


# ---------------------------------------------------------------- geometry
def inside(p: Point, poly: List[Point]) -> bool:
    """Whether a point lies in a polygon (ray casting; a point on the border counts as inside)."""
    x, y, n, hit = p[0], p[1], len(poly), False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if abs((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)) < 1e-7 and min(x1, x2) - 1e-7 <= x <= max(x1, x2) + 1e-7 and min(y1, y2) - 1e-7 <= y <= max(y1, y2) + 1e-7:
            return True
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def area(poly: List[Point]) -> float:
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def room_of(p: Point, rooms: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The room a point is in; the smallest when rooms are nested."""
    found = [r for r in rooms if len(r["points"]) >= 3 and inside(p, [tuple(q) for q in r["points"]])]
    return min(found, key=lambda r: area([tuple(q) for q in r["points"]])) if found else None


def chain(points: List[Point], start: Point) -> List[int]:
    """The order of the points that goes always to the nearest one not visited yet, starting from `start`."""
    left, here, order = list(range(len(points))), start, []
    while left:
        i = min(left, key=lambda k: (math.hypot(points[k][0] - here[0], points[k][1] - here[1]), k))
        order.append(i)
        left.remove(i)
        here = points[i]
    return order


def split_evenly(loads: List[Dict[str, Any]], maximum: int) -> List[List[Dict[str, Any]]]:
    """A room's loads in the fewest groups of at most `maximum`, balanced, cut along the longer side of their box so each group is compact."""
    if len(loads) <= maximum:
        return [loads]
    k = math.ceil(len(loads) / maximum)
    xs, ys = [l["x"] for l in loads], [l["y"] for l in loads]
    axis = "x" if max(xs) - min(xs) >= max(ys) - min(ys) else "y"
    ordered = sorted(loads, key=lambda l: (l[axis], l["id"]))
    size, extra = divmod(len(ordered), k)
    out, at = [], 0
    for i in range(k):
        n = size + (1 if i < extra else 0)
        out.append(ordered[at: at + n])
        at += n
    return out


# ---------------------------------------------------------------- data of the profile and the limits
def _families(profile: Dict[str, Any]) -> Dict[str, str]:
    """Kind of load -> family of circuit (lighting, general sockets...), as the profile says."""
    return {k["id"]: k["circuito"] for k in profile["nodos"] if k.get("carga") and k.get("circuito")}


def _next_tag(prefix: str, taken: set) -> str:
    n = 1
    while f"{prefix}-{n:02d}" in taken:
        n += 1
    tag = f"{prefix}-{n:02d}"
    taken.add(tag)
    return tag


def _limits(options: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """The families with the limits in force: the defaults of `params.json` over which the caller may put its own (`max_outlets`, `va_per_outlet` by family)."""
    base = params["design"]["families"]
    return {f: {**v, **{k: x for k, x in ((options.get("families") or {}).get(f) or {}).items() if k in ("max_outlets", "va_per_outlet") and isinstance(x, (int, float)) and x > 0}} for f, v in base.items()}


def _own_va(node: Dict[str, Any]) -> Optional[float]:
    """The power a load says of itself (a luminaire placed by the lighting calculation carries `attrs.lighting.power_w`); None when it says nothing, and then the family's typical value is used."""
    w = ((node.get("attrs") or {}).get("lighting") or {}).get("power_w")
    return float(w) if isinstance(w, (int, float)) and not isinstance(w, bool) and w > 0 else None


def _loads(document: Dict[str, Any], families: Dict[str, str], board: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """The loads of the drawing; when the board has a board of Engineering behind it, only the loads fed from that board (or from none yet)."""
    mine = (board or {}).get("board", "")
    return [{"id": n["id"], "x": n["x"], "y": n["y"], "kind": n["kind"], "family": families[n["kind"]], "va": _own_va(n)} for n in document.get("nodes", [])
            if n.get("kind") in families and (not mine or n.get("board", mine) == mine)]


def _board(document: Dict[str, Any], profile: Dict[str, Any], wanted: Optional[str]) -> Optional[Dict[str, Any]]:
    kinds = {k["id"]: k for k in profile["nodos"]}
    boards = [n for n in document.get("nodes", []) if kinds.get(n.get("kind"), {}).get("simbolo_2d") == "tablero" and (not wanted or n["id"] == wanted)]
    return boards[0] if boards else None


# ---------------------------------------------------------------- step 1: the runs
def _costs(ordered: List[Tuple[float, float]]) -> Dict[Tuple[int, int], float]:
    """What one trunk costs for each run of consecutive loads (ordered by y): the stubs from the trunk, at their median y, to each load plus the trunk, as long as the loads are wide."""
    n = len(ordered)
    ys = [p[1] for p in ordered]
    pre = [0.0]
    for y in ys:
        pre.append(pre[-1] + y)
    cost: Dict[Tuple[int, int], float] = {}
    for i in range(n):
        lo = hi = ordered[i][0]
        for j in range(i, n):
            lo, hi = min(lo, ordered[j][0]), max(hi, ordered[j][0])
            m = (i + j) // 2
            cost[(i, j)] = ys[m] * (m - i + 1) - (pre[m + 1] - pre[i]) + (pre[j + 1] - pre[m + 1]) - ys[m] * (j - m) + (hi - lo)
    return cost


def partitions(pts: List[Tuple[float, float]], most: int = MAX_TRUNKS) -> Dict[int, List[List[Tuple[float, float]]]]:
    """For every number of trunks k, the best way to cut the loads, ordered by y, into k consecutive groups (least total of stubs and trunks, by dynamic programming)."""
    ordered = sorted(pts, key=lambda p: (p[1], p[0]))
    n = len(ordered)
    cost = _costs(ordered)
    best: Dict[Tuple[int, int], Tuple[float, int]] = {}
    out: Dict[int, List[List[Tuple[float, float]]]] = {}
    for k in range(1, min(most, n) + 1):
        for j in range(k - 1, n):
            best[(k, j)] = (cost[(0, j)], 0) if k == 1 else min((best[(k - 1, i - 1)][0] + cost[(i, j)], i) for i in range(k - 1, j + 1))
        cuts, j = [], n - 1
        for kk in range(k, 0, -1):
            i = best[(kk, j)][1]
            cuts.append(ordered[i: j + 1])
            j = i - 1
        out[k] = cuts[::-1]
    return out


def _layout(groups: List[List[Tuple[float, float]]], board: Point, spine_x: float) -> Dict[str, Any]:
    """The lines of one way of cutting the loads: a horizontal trunk per group at the median y of its loads reaching the spine, the spine, the feeder from the board and a vertical stub per load."""
    trunks, stubs = [], []
    ys = []
    for g in groups:
        y = statistics.median(p[1] for p in g)
        ys.append(y)
        lo, hi = min(min(p[0] for p in g), spine_x), max(max(p[0] for p in g), spine_x)
        if hi - lo > EPS:
            trunks.append([(lo, y), (hi, y)])
        stubs += [[(p[0], y), (p[0], p[1])] for p in g if abs(p[1] - y) > 1e-6]
    top, bottom = min(ys + [board[1]]), max(ys + [board[1]])
    if bottom - top > EPS:
        trunks.append([(spine_x, top), (spine_x, bottom)])
    if abs(board[0] - spine_x) > EPS:
        trunks.append([board, (spine_x, board[1])])
    return {"trunks": trunks, "stubs": stubs}


def _length(lines: List[List[Point]]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for ln in lines for a, b in zip(ln, ln[1:]))


def best_layout(pts: List[Tuple[float, float]], board: Point) -> Dict[str, Any]:
    """The shortest layout of rows (horizontal trunks) over every number of trunks and over the places the spine can be (through the board or through the middle of the loads)."""
    best: Optional[Dict[str, Any]] = None
    for groups in partitions(pts).values():
        for sx in sorted({board[0], statistics.median(p[0] for p in pts)}):
            lay = _layout(groups, board, sx)
            lay["length"] = _length(lay["trunks"]) + _length(lay["stubs"])
            if best is None or lay["length"] < best["length"] - 1e-9:
                best = lay
    assert best is not None
    return best


def _runs(lay: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The lines of a layout with their role: a trunk is a tray (BN) and a stub a conduit (CN) to a single load."""
    return [{"kind": "BN", "points": [list(p) for p in ln], "role": "trunk"} for ln in lay["trunks"]] + [{"kind": "CN", "points": [list(p) for p in ln], "role": "stub"} for ln in lay["stubs"]]


def _transpose(lines: List[List[Point]]) -> List[List[Point]]:
    return [[(p[1], p[0]) for p in ln] for ln in lines]


def _stats(orientation: str, lines: List[Dict[str, Any]], document: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    scale = (document.get("plan") or {}).get("scale")
    k = core.metres_per_unit(scale, params) if scale else None
    unit = k if k else 1.0
    trunks = [ln["points"] for ln in lines if ln["role"] == "trunk"]
    stubs = [ln["points"] for ln in lines if ln["role"] == "stub"]
    return {"orientation": orientation, "trunks": len(trunks), "stubs": len(stubs), "bends": 0, "trunk_length": round(_length(trunks) * unit, 2), "stub_length": round(_length(stubs) * unit, 2), "in_metres": bool(k)}


def propose_runs(document: Dict[str, Any], options: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The trays and conduits for the loads of the drawing: straight trunks hanging from one spine that starts at the board, and a short straight conduit to each load. Both orientations are tried
    (horizontal trunks, or vertical ones) and the shorter wins. Returns {orientation, lines, stats, warnings}; a line is {kind, points, role} with role trunk (tray) or stub (conduit)."""
    params, options = params or core.PARAMS, options or {}
    profile = core.load_profile(document.get("discipline", "electrica_BT"))
    families = _families(profile)
    board = _board(document, profile, options.get("board"))
    loads = _loads(document, families, board)
    if board is None:
        return {"orientation": "", "lines": [], "stats": {}, "warnings": ["no board (tablero) in the drawing: place one to start the runs from it"]}
    if not loads:
        return {"orientation": "", "lines": [], "stats": {}, "warnings": ["there are no loads in the drawing: place the luminaires or sockets first"]}
    pts, b = [(l["x"], l["y"]) for l in loads], (board["x"], board["y"])
    rows = best_layout(pts, b)
    cols = best_layout([(y, x) for x, y in pts], (b[1], b[0]))
    cols = {**cols, "trunks": _transpose(cols["trunks"]), "stubs": _transpose(cols["stubs"])}
    orientation, lay = ("horizontal", rows) if rows["length"] <= cols["length"] + 1e-9 else ("vertical", cols)
    lines = _runs(lay)
    stats = _stats(orientation, lines, document, params)
    return {"orientation": orientation, "lines": lines, "stats": stats, "warnings": []}


# ---------------------------------------------------------------- step 2: the wiring over the runs that are drawn
class _Wiring:
    """One wiring being proposed: the board, the loads by room, the tags taken and what has been proposed."""

    def __init__(self, document: Dict[str, Any], rooms: List[Dict[str, Any]], options: Dict[str, Any], params: Dict[str, Any]):
        profile = core.load_profile(document.get("discipline", "electrica_BT"))
        self.document, self.rooms, self.params = document, rooms, params
        self.families = _families(profile)
        self.limits = _limits(options, params)
        self.board = _board(document, profile, options.get("board"))
        self.taken = set(options.get("taken") or [])
        self.circuits: List[Dict[str, Any]] = []
        self.assignments: Dict[str, str] = {}
        self.unassigned: List[str] = []
        self.warnings: List[str] = []

    def loads_by_room(self) -> Dict[str, List[Dict[str, Any]]]:
        by_room: Dict[str, List[Dict[str, Any]]] = {}
        for l in _loads(self.document, self.families, self.board):
            r = room_of((l["x"], l["y"]), self.rooms)
            by_room.setdefault(r["id"], []).append(l) if r else self.unassigned.append(l["id"])
        if self.unassigned:
            self.warnings.append(f"{len(self.unassigned)} load(s) are outside every room and get no circuit: {', '.join(self.unassigned[:8])}{' ...' if len(self.unassigned) > 8 else ''}")
        return by_room

    def distance_to_board(self, loads: List[Dict[str, Any]]) -> float:
        return math.hypot(*(sum(l[a] for l in loads) / len(loads) - self.board[a] for a in ("x", "y")))

    def room_circuits(self, room: Dict[str, Any], loads: List[Dict[str, Any]]) -> None:
        for family in sorted({l["family"] for l in loads}):
            for group in split_evenly([l for l in loads if l["family"] == family], int(self.limits[family]["max_outlets"])):
                self._circuit(room, family, group)

    def _circuit(self, room: Dict[str, Any], family: str, group: List[Dict[str, Any]]) -> None:
        lim = self.limits[family]
        tag = _next_tag(lim["prefix"], self.taken)
        pts = [(l["x"], l["y"]) for l in group]
        order = [group[i]["id"] for i in chain(pts, (self.board["x"], self.board["y"]))]
        self.assignments.update({i: tag for i in order})
        self.circuits.append({"tag": tag, "family": family, "room": room["id"], "room_name": room.get("name", ""), "loads": order, "outlets": len(order), "from": self.board["id"], "to": order[-1], "via": [],
                              "ternas": 1, "va": self._power(group, lim), "va_per_outlet": lim["va_per_outlet"], "description": f"{lim['label']['es']} {room.get('name', '')} ({len(order)})".strip()})

    @staticmethod
    def _power(group: List[Dict[str, Any]], lim: Dict[str, Any]) -> float:
        """The power of a circuit: what each load says of itself, and the family's typical value for the ones that say nothing."""
        return round(sum(l["va"] if l.get("va") is not None else float(lim["va_per_outlet"]) for l in group), 1)

    def verify(self) -> Dict[str, Any]:
        """Route what was proposed over the runs that are drawn, with the engine itself: for each circuit whether every load is reached and how far."""
        doc = copy.deepcopy(self.document)
        for n in doc["nodes"]:
            if n["id"] in self.assignments:
                n["circuit"] = self.assignments[n["id"]]
        doc["circuits"] = [{"tag": c["tag"], "from": c["from"], "to": c["to"], "via": [], "ternas": 1} for c in self.circuits]
        try:
            done = core.process(doc)
        except core.PlanError as e:
            self.warnings.append(f"the proposal could not be checked: {e}")
            return {}
        routes = {t: {"found": r["found"], "length_m": r["length_m"], "max_distance_m": r.get("max_distance_m", 0.0), "unreached": r.get("unreached", [])} for t, r in done["circuits"].items()}
        for t, r in routes.items():
            if not r["found"]:
                self.warnings.append(f"circuit {t}: the runs do not reach {', '.join(r['unreached'][:6]) or 'all its loads'}: draw a run to them or apply the runs first")
        return routes

    def result(self, routes: Dict[str, Any]) -> Dict[str, Any]:
        return {"board": self.board["id"] if self.board else "", "circuits": self.circuits, "assignments": self.assignments, "unassigned": self.unassigned, "warnings": self.warnings, "limits": self.limits, "routes": routes}


def propose_wiring(document: Dict[str, Any], rooms: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The circuits for the loads of the drawing, by room and family (at most `max_outlets` each), routed over the runs already drawn. `options`: `taken` (tags already used in the board), `board` (id of the
    origin node), `families` (limits that replace the defaults). Returns {board, circuits, assignments, unassigned, warnings, limits, routes}."""
    work = _Wiring(document, rooms, options or {}, params or core.PARAMS)
    if work.board is None:
        work.warnings.append("no board (tablero) in the drawing: place one to start the runs from it")
        return work.result({})
    if not document.get("lines"):
        work.warnings.append("there are no runs in the drawing: generate and apply the runs first")
        return work.result({})
    by_room = work.loads_by_room()
    by_id = {r["id"]: r for r in rooms}
    for rid in sorted(by_room, key=lambda r: work.distance_to_board(by_room[r])):
        work.room_circuits(by_id[rid], by_room[rid])
    return work.result(work.verify() if work.circuits else {})
