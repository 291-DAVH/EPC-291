"""Automatic design of circuits and runs for the loads placed in rooms.

The person places the loads (luminaires, sockets...) and marks the rooms; this module proposes
  - the circuits: each room is a circuit of each family of load it holds (lighting, general sockets...), split when a room holds more loads than a circuit may have (15 for lighting);
  - the trunk: tray lines from the board to the entrance of each room, sharing what they can;
  - the branches: one conduit per circuit from the entrance of its room through its loads, in the order of the shortest chain.
Cables are not lines of their own: a circuit's cable follows the conduits and trays it is routed through (the engine records on every stretch which circuits it carries).

Pure: a drawing document and the rooms in, a proposal out (circuits, assignments, lines); it changes nothing. Lines are straight horizontal and vertical stretches, in the units of the view.
The limits per circuit and the power per outlet are typical values in `params.json` (`design`): the engineer confirms them against the standard of the project.
"""
import math
from typing import Any, Dict, List, Optional, Tuple

from epc_plan import core

Point = Tuple[float, float]
EPS = 1e-9


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


def l_path(a: Point, b: Point, horizontal_first: bool) -> List[Point]:
    """A straight run from a to b with at most one elbow, horizontal first or vertical first."""
    if abs(a[0] - b[0]) < EPS or abs(a[1] - b[1]) < EPS:
        return [a, b]
    return [a, (b[0], a[1]), b] if horizontal_first else [a, (a[0], b[1]), b]


def _dedupe(points: List[Point]) -> List[Point]:
    out: List[Point] = []
    for p in points:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-6:
            out.append(p)
    return out


def nearest_on(segments: List[Tuple[Point, Point]], p: Point) -> Point:
    """The point of a set of segments closest to p."""
    best, gap = segments[0][0], float("inf")
    for a, b in segments:
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = dx * dx + dy * dy
        t = 0.0 if n == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n))
        q = (a[0] + t * dx, a[1] + t * dy)
        if math.hypot(p[0] - q[0], p[1] - q[1]) < gap:
            best, gap = q, math.hypot(p[0] - q[0], p[1] - q[1])
    return best


def entry_point(path: List[Point], poly: List[Point]) -> Tuple[List[Point], Point]:
    """Where a run toward a room first enters it: the run up to there and that point. A run that starts inside the room has no trunk to lay."""
    if inside(path[0], poly):
        return [path[0]], path[0]
    for a, b in zip(path, path[1:]):
        steps = 200
        for i in range(1, steps + 1):
            q = (a[0] + (b[0] - a[0]) * i / steps, a[1] + (b[1] - a[1]) * i / steps)
            if inside(q, poly):
                cut = path[: path.index(a) + 1] + [q]
                return _dedupe(cut), q
    return [path[0]], path[0]


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


# ---------------------------------------------------------------- the design
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


def _loads(document: Dict[str, Any], families: Dict[str, str]) -> List[Dict[str, Any]]:
    return [{"id": n["id"], "x": n["x"], "y": n["y"], "kind": n["kind"], "family": families[n["kind"]]} for n in document.get("nodes", []) if n.get("kind") in families]


def _trunk_to(trunk: List[Tuple[Point, Point]], target: Point, poly: List[Point]) -> Tuple[List[Point], Point]:
    """The tray run from the nearest point of what is laid to the entrance of a room (and that entrance), and records it in the trunk."""
    start = nearest_on(trunk, target)
    path = _dedupe(l_path(start, target, abs(target[0] - start[0]) >= abs(target[1] - start[1])))
    run, entrance = entry_point(path, poly)
    run = _dedupe(run)
    trunk.extend(zip(run, run[1:]))
    return run, entrance


def _branch(entrance: Point, group: List[Dict[str, Any]], horizontal_first: bool) -> Tuple[List[Point], List[str]]:
    """The conduit of one circuit: from the entrance of the room through its loads in the order of the shortest chain; and the loads in that order."""
    pts = [(l["x"], l["y"]) for l in group]
    order = chain(pts, entrance)
    path: List[Point] = [entrance]
    for i in order:
        path += l_path(path[-1], pts[i], horizontal_first)[1:]
    return _dedupe(path), [group[i]["id"] for i in order]


class _Design:
    """One proposal being made: the board, the rooms with their loads, the trunk laid so far, the tags taken and what has been proposed."""

    def __init__(self, document: Dict[str, Any], rooms: List[Dict[str, Any]], options: Dict[str, Any], params: Dict[str, Any]):
        profile = core.load_profile(document.get("discipline", "electrica_BT"))
        self.document, self.rooms = document, rooms
        self.kinds = {k["id"]: k for k in profile["nodos"]}
        self.families = _families(profile)
        self.limits = _limits(options, params)
        self.board = self._find_board(options.get("board"))
        self.taken = set(options.get("taken") or [])
        self.trunk: List[Tuple[Point, Point]] = [((self.board["x"], self.board["y"]),) * 2] if self.board else []
        self.circuits: List[Dict[str, Any]] = []
        self.lines: List[Dict[str, Any]] = []
        self.assignments: Dict[str, str] = {}
        self.unassigned: List[str] = []
        self.warnings: List[str] = []

    def _find_board(self, wanted: Optional[str]) -> Optional[Dict[str, Any]]:
        boards = [n for n in self.document.get("nodes", []) if self.kinds.get(n.get("kind"), {}).get("simbolo_2d") == "tablero" and (not wanted or n["id"] == wanted)]
        return boards[0] if boards else None

    def loads_by_room(self) -> Dict[str, List[Dict[str, Any]]]:
        by_room: Dict[str, List[Dict[str, Any]]] = {}
        for l in _loads(self.document, self.families):
            r = room_of((l["x"], l["y"]), self.rooms)
            by_room.setdefault(r["id"], []).append(l) if r else self.unassigned.append(l["id"])
        if self.unassigned:
            self.warnings.append(f"{len(self.unassigned)} load(s) are outside every room and get no circuit: {', '.join(self.unassigned[:8])}{' ...' if len(self.unassigned) > 8 else ''}")
        return by_room

    def distance_to_board(self, loads: List[Dict[str, Any]]) -> float:
        return math.hypot(*(sum(l[a] for l in loads) / len(loads) - self.board[a] for a in ("x", "y")))

    def _target(self, loads: List[Dict[str, Any]], poly: List[Point]) -> Point:
        """Where the trunk heads for in a room: the middle of its loads, or the load nearest to it when the middle falls outside the outline."""
        mid = (sum(l["x"] for l in loads) / len(loads), sum(l["y"] for l in loads) / len(loads))
        return mid if inside(mid, poly) else min(((l["x"], l["y"]) for l in loads), key=lambda q: math.hypot(q[0] - mid[0], q[1] - mid[1]))

    def lay_room(self, room: Dict[str, Any], loads: List[Dict[str, Any]]) -> None:
        poly = [tuple(q) for q in room["points"]]
        run, entrance = _trunk_to(self.trunk, self._target(loads, poly), poly)
        if len(run) >= 2:
            self.lines.append({"kind": "BN", "points": [list(p) for p in run], "role": "trunk", "room": room["id"]})
        for family in sorted({l["family"] for l in loads}):
            for group in split_evenly([l for l in loads if l["family"] == family], int(self.limits[family]["max_outlets"])):
                self._circuit(room, family, group, entrance)

    def _circuit(self, room: Dict[str, Any], family: str, group: List[Dict[str, Any]], entrance: Point) -> None:
        lim = self.limits[family]
        tag = _next_tag(lim["prefix"], self.taken)
        path, order = _branch(entrance, group, len(self.circuits) % 2 == 0)
        self.lines.append({"kind": "CN", "points": [list(p) for p in path], "circuit": tag, "role": "branch", "room": room["id"]})
        self.assignments.update({i: tag for i in order})
        self.circuits.append({"tag": tag, "family": family, "room": room["id"], "room_name": room.get("name", ""), "loads": order, "outlets": len(order), "from": self.board["id"], "to": order[-1], "via": [],
                              "ternas": 1, "va": round(len(order) * float(lim["va_per_outlet"]), 1), "va_per_outlet": lim["va_per_outlet"], "description": f"{lim['label']['es']} {room.get('name', '')} ({len(order)})".strip()})

    def result(self) -> Dict[str, Any]:
        return {"board": self.board["id"] if self.board else "", "circuits": self.circuits, "lines": self.lines, "assignments": self.assignments, "unassigned": self.unassigned, "warnings": self.warnings, "limits": self.limits}


def propose(document: Dict[str, Any], rooms: List[Dict[str, Any]], options: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """The circuits, trunk and branches for the loads of the drawing, by room. `options`: `taken` (tags already used in the board), `board` (id of the origin node; the first board of the drawing when empty),
    `families` (limits that replace the defaults). Returns {board, circuits, lines, assignments, unassigned, warnings, limits}."""
    work = _Design(document, rooms, options or {}, params or core.PARAMS)
    if work.board is None:
        work.warnings.append("no board (tablero) in the drawing: place one to start the runs from it")
        return work.result()
    by_room = work.loads_by_room()
    by_id = {r["id"]: r for r in rooms}
    for rid in sorted(by_room, key=lambda r: work.distance_to_board(by_room[r])):
        work.lay_room(by_id[rid], by_room[rid])
    return work.result()
