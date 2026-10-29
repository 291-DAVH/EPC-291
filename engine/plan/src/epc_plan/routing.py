"""The route of each circuit over the drawn network, from its origin to its destination.

The person does not draw one cable per circuit: they say which circuit (a tag of the board) goes from which node to which, and the program finds the way through the
stretches (the shortest one) and records, on every stretch, which circuits it carries. A kind of stretch that takes a single circuit (a conduit) is blocked for the others:
a circuit cannot be routed through a conduit another circuit already uses; a tray takes as many as come.

A circuit may go up or down through plenums (vertical shafts): each plenum its route passes adds its own height (`altura_m`) to the length, once per circuit however many loads
use it, so a route through several plenums adds the height of each.
"""
import heapq
from typing import Any, Dict, List, Optional, Set, Tuple


def _adjacency(stretches) -> Dict[str, List[Tuple[str, int, float]]]:
    adj: Dict[str, List[Tuple[str, int, float]]] = {}
    for i, s in enumerate(stretches):
        adj.setdefault(s["from"], []).append((s["to"], i, s["length_m"]))
        adj.setdefault(s["to"], []).append((s["from"], i, s["length_m"]))
    return adj


def _shortest(adj, a: str, b: str, usable) -> Optional[List[int]]:
    """Stretch indexes of the shortest way from node a to node b using only the stretches `usable` allows; None when there is none."""
    best: Dict[str, float] = {a: 0.0}
    came: Dict[str, Tuple[str, int]] = {}
    queue: List[Tuple[float, str]] = [(0.0, a)]
    while queue:
        d, cur = heapq.heappop(queue)
        if cur == b:
            break
        if d > best.get(cur, float("inf")):
            continue
        for nxt, si, length in sorted(adj.get(cur, []), key=lambda e: (e[0], e[1])):
            if not usable(si):
                continue
            nd = d + length
            if nd < best.get(nxt, float("inf")) - 1e-12:
                best[nxt] = nd
                came[nxt] = (cur, si)
                heapq.heappush(queue, (nd, nxt))
    if b not in best:
        return None
    path: List[int] = []
    cur = b
    while cur != a:
        cur, si = came[cur][0], came[cur][1]
        path.append(si)
    return path[::-1]


def _legs(c: Dict[str, Any]) -> List[str]:
    return [c["from"], *c.get("via", []), c["to"]]


def _walk(adj, stops: List[str], usable) -> Optional[List[int]]:
    """The stretches of the way that goes through the stops in order; None when one leg has no way."""
    path: List[int] = []
    for a, b in zip(stops, stops[1:]):
        leg = [] if a == b else _shortest(adj, a, b, usable)
        if leg is None:
            return None
        path += leg
    return path


def _targets(c: Dict[str, Any], loads: Dict[str, List[str]]) -> List[List[str]]:
    """The ways to find for a circuit: one to its destination node (through the nodes it must pass), and one to each of its loads (luminaires, sockets, HVAC...)."""
    ways = [_legs(c)] if c.get("to") else []
    return ways + [[c["from"], n] for n in loads.get(c["tag"], [])]


def _node_problem(circuit: Dict[str, Any], ids: Set[str], ways: List[List[str]]) -> Optional[str]:
    tag = circuit["tag"]
    if not circuit.get("from") or circuit["from"] not in ids:
        return f"circuit {tag}: the origin node is not chosen or no longer exists"
    if not ways:
        return f"circuit {tag}: it has no destination node and no loads assigned"
    missing = [n for way in ways for n in way if n not in ids]
    if missing:
        return f"circuit {tag}: the node {missing[0]} no longer exists"
    if circuit.get("to") == circuit["from"]:
        return f"circuit {tag}: the origin and the destination are the same node"
    return None


def _problem(circuit: Dict[str, Any], ids: Set[str], seen: Set[str], ways: List[List[str]]) -> Optional[str]:
    if not circuit.get("tag"):
        return "a circuit has no tag: choose one of the board's circuits"
    if circuit["tag"] in seen:
        return f"circuit {circuit['tag']} is defined twice: the second definition is ignored"
    return _node_problem(circuit, ids, ways)


def _visited(start: str, path: List[int], stretches) -> List[str]:
    """The nodes a way goes through, in order, from its start."""
    seen, cur = [start], start
    for si in path:
        s = stretches[si]
        cur = s["to"] if s["from"] == cur else s["from"]
        seen.append(cur)
    return seen


def _plenums_on(start: str, path: List[int], stretches, risers: Dict[str, float]) -> List[str]:
    """The plenums a way goes through (each once, however many times it touches it)."""
    return [n for n in dict.fromkeys(_visited(start, path, stretches)) if n in risers]


def _tree(adj, ways: List[List[str]], free, stretches, risers: Dict[str, float]) -> Tuple[List[int], Dict[str, float], List[str], List[str]]:
    """The stretches that reach every target (the shared trunk counted once), the length of the way to each (with the height of the plenums it goes through),
    the targets with no way and the plenums the circuit goes through."""
    used: List[int] = []
    reach: Dict[str, float] = {}
    lost: List[str] = []
    through: List[str] = []
    for way in ways:
        path = _walk(adj, way, free)
        if path is None:
            lost.append(way[-1])
            continue
        mine = _plenums_on(way[0], path, stretches, risers)
        used += [si for si in path if si not in used]
        through += [n for n in mine if n not in through]
        reach[way[-1]] = round(sum(stretches[si]["length_m"] for si in path) + sum(risers[n] for n in mine), 4)
    return used, reach, lost, through


def _no_way(tag: str, tag_of, ways, adj) -> str:
    """Why a circuit has loads or a destination it cannot reach: nothing connects them, or the only ways go through a conduit another circuit uses."""
    apart = [w for w in ways if _walk(adj, w, lambda si: True) is None]
    if apart:
        return f"circuit {tag}: there is no way from {tag_of[apart[0][0]]} to {', '.join(tag_of[w[-1]] for w in apart)} over the drawn stretches"
    return f"circuit {tag}: every way to its loads goes through a conduit that another circuit already uses"


def _record(tag: str, ternas: int, used: List[int], stretches, rise: float = 0.0) -> Dict[str, Any]:
    for si in used:
        stretches[si].setdefault("carries", []).append({"circuit": tag, "ternas": ternas})
    length = round(sum(stretches[si]["length_m"] for si in used) + rise, 4)
    return {"stretches": [stretches[si]["tag"] for si in used], "lines": list(dict.fromkeys(stretches[si]["line"] for si in used)), "length_m": length, "cable_length_m": round(length * ternas, 4)}


def _loads_by_circuit(gnodes, load_kinds: Set[str]) -> Dict[str, List[str]]:
    loads: Dict[str, List[str]] = {}
    for g in sorted(gnodes, key=lambda g: g["tag"] or ""):
        if g.get("circuit") and g["kind"] in load_kinds:
            loads.setdefault(g["circuit"], []).append(g["id"])
    return loads


_POWER_W = {"potencia_w": 1.0, "potencia_va": 1.0, "potencia_kw": 1000.0}


def _weight(g) -> Optional[float]:
    """The power of a load in W (from its attributes), or None when it has none."""
    for key, k in _POWER_W.items():
        try:
            v = float((g.get("attrs") or {}).get(key))
        except (TypeError, ValueError):
            continue
        if v > 0:
            return v * k
    return None


def _measured(c: Dict[str, Any], mine: List[str]) -> List[str]:
    """What the circuit is measured to: its loads, or its destination when it has no load assigned."""
    return mine or ([c["to"]] if c.get("to") else [])


def _moments(mine: List[str], reach: Dict[str, float], tag_of, gnode_of) -> Dict[str, Any]:
    """The moment method over the loads of a circuit: each load weighs its power (equal when some load has none), its distance is the way from the origin.
    `moment_length_m` is the length that, with the whole current, gives the same drop as the sum of current x distance of the loads."""
    placed = [n for n in mine if n in reach]
    if not placed:
        return {"loads_detail": [], "max_distance_m": 0.0, "moment_length_m": 0.0}
    power = [_weight(gnode_of[n]) for n in placed]
    known = all(power)
    w = power if known else [1.0] * len(placed)
    d = [reach[n] for n in placed]
    return {"loads_detail": [{"tag": tag_of[n], "distance_m": round(x, 4), "power_w": wi if known else None} for n, x, wi in zip(placed, d, w)],
            "max_distance_m": round(max(d), 4), "moment_length_m": round(sum(wi * x for wi, x in zip(w, d)) / sum(w), 4)}


def _route_one(c, ways, adj, stretches, taken, single_kinds, tag_of, gnode_of, loads, warnings, risers: Dict[str, float]) -> Dict[str, Any]:
    """The route of one circuit: the stretches that reach all its targets (marked as taken by it), the lengths and what could not be reached."""
    tag, ternas = c["tag"], max(1, int(c.get("ternas") or 1))
    free = lambda si: not (stretches[si]["kind"] in single_kinds and taken[si] - {tag})           # noqa: E731 - a conduit used by another circuit is blocked
    used, reach, lost, through = _tree(adj, ways, free, stretches, risers)
    for si in used:
        taken[si].add(tag)
    if lost:
        warnings.append(_no_way(tag, tag_of, ways, adj))
    mine = loads.get(tag, [])
    rise = sum(risers[n] for n in through)
    return {"found": not lost, "from": c["from"], "to": c.get("to", ""), "ternas": ternas, "loads": len(mine), "unreached": [tag_of[n] for n in lost],
            "distance_to_load_m": {tag_of[n]: d for n, d in reach.items() if n in mine}, **_moments(_measured(c, mine), reach, tag_of, gnode_of),
            "destination_distance_m": reach.get(c.get("to", "")), "plenums": [tag_of[n] for n in through], "rise_m": round(rise, 4), **_record(tag, ternas, used, stretches, rise)}


def _risers(gnodes, vertical_kinds: Set[str], warnings: List[str]) -> Dict[str, float]:
    """The height of each plenum (node of a vertical kind) by node id; one with no usable height counts as zero and is reported."""
    out: Dict[str, float] = {}
    for g in gnodes:
        if g["kind"] not in vertical_kinds or not g["placed"]:
            continue
        try:
            h = float((g.get("attrs") or {}).get("altura_m"))
        except (TypeError, ValueError):
            h = -1.0
        if h < 0:
            warnings.append(f"plenum {g['tag']} has no height (altura_m): it adds nothing to the cables that go through it")
            h = 0.0
        out[g["id"]] = h
    return out


def route_circuits(gnodes, stretches, circuits: List[Dict[str, Any]], single_kinds: Set[str], load_kinds: Set[str], warnings: List[str], vertical_kinds: Optional[Set[str]] = None) -> Dict[str, Dict[str, Any]]:
    """Route every circuit in the order given: from its origin to its destination node and to each load assigned to it. Records on each stretch the circuits it carries
    (`carries`) and returns the route of each circuit by tag. A route through plenums (`vertical_kinds`) adds the height of each."""
    risers = _risers(gnodes, vertical_kinds or set(), warnings)
    ids = {g["id"] for g in gnodes}
    tag_of = {g["id"]: g["tag"] for g in gnodes}
    gnode_of = {g["id"]: g for g in gnodes}
    loads = _loads_by_circuit(gnodes, load_kinds)
    adj = _adjacency(stretches)
    taken: Dict[int, Set[str]] = {i: ({s["circuit"]} if s.get("circuit") else set()) for i, s in enumerate(stretches)}
    routes: Dict[str, Dict[str, Any]] = {}
    for c in circuits:
        ways = _targets(c, loads)
        problem = _problem(c, ids, set(routes), ways)
        if problem:
            warnings.append(problem)
            continue
        routes[c["tag"]] = _route_one(c, ways, adj, stretches, taken, single_kinds, tag_of, gnode_of, loads, warnings, risers)
    return routes
