"""The route of each circuit over the drawn network, from its origin to its destination.

The person does not draw one cable per circuit: they say which circuit (a tag of the board) goes from which node to which, and the program finds the way through the
stretches (the shortest one) and records, on every stretch, which circuits it carries. A kind of stretch that takes a single circuit (a conduit) is blocked for the others:
a circuit cannot be routed through a conduit another circuit already uses; a tray takes as many as come.
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


def _route_one(adj, c, usable) -> Optional[List[int]]:
    path: List[int] = []
    stops = _legs(c)
    for a, b in zip(stops, stops[1:]):
        leg = [] if a == b else _shortest(adj, a, b, usable)
        if leg is None:
            return None
        path += leg
    return path


def _problem(circuit: Dict[str, Any], ids: Set[str], seen: Set[str]) -> Optional[str]:
    if not circuit.get("tag"):
        return "a circuit has no tag: choose one of the board's circuits"
    if circuit["tag"] in seen:
        return f"circuit {circuit['tag']} is defined twice: the second definition is ignored"
    missing = [n for n in _legs(circuit) if n not in ids]
    if missing:
        return f"circuit {circuit['tag']}: the node {missing[0]} no longer exists"
    if circuit["from"] == circuit["to"]:
        return f"circuit {circuit['tag']}: the origin and the destination are the same node"
    return None


def route_circuits(gnodes, stretches, circuits: List[Dict[str, Any]], single_kinds: Set[str], warnings: List[str]) -> Dict[str, Dict[str, Any]]:
    """Route every circuit in the order given. Records on each stretch the circuits it carries (`carries`) and returns the route of each circuit by tag."""
    ids = {g["id"] for g in gnodes}
    tag_of = {g["id"]: g["tag"] for g in gnodes}
    adj = _adjacency(stretches)
    taken: Dict[int, Set[str]] = {i: ({s["circuit"]} if s.get("circuit") else set()) for i, s in enumerate(stretches)}
    routes: Dict[str, Dict[str, Any]] = {}
    for c in circuits:
        problem = _problem(c, ids, set(routes))
        if problem:
            warnings.append(problem)
            continue
        tag = c["tag"]
        free = lambda si: not (stretches[si]["kind"] in single_kinds and taken[si] - {tag})           # noqa: E731 - a conduit used by another circuit is blocked
        path = _route_one(adj, c, free)
        ternas = max(1, int(c.get("ternas") or 1))
        if path is None:
            reachable = _route_one(adj, c, lambda si: True) is not None
            warnings.append(f"circuit {tag}: " + ("every way from {} to {} goes through a conduit that another circuit already uses".format(tag_of[c["from"]], tag_of[c["to"]]) if reachable
                                                     else f"there is no way from {tag_of[c['from']]} to {tag_of[c['to']]} over the drawn stretches"))
            routes[tag] = {"found": False, "from": c["from"], "to": c["to"], "ternas": ternas, "stretches": [], "lines": [], "length_m": 0.0, "cable_length_m": 0.0}
            continue
        for si in path:
            taken[si].add(tag)
            stretches[si].setdefault("carries", []).append({"circuit": tag, "ternas": ternas})
        length = round(sum(stretches[si]["length_m"] for si in path), 4)
        routes[tag] = {"found": True, "from": c["from"], "to": c["to"], "ternas": ternas, "stretches": [stretches[si]["tag"] for si in path],
                       "lines": list(dict.fromkeys(stretches[si]["line"] for si in path)), "length_m": length, "cable_length_m": round(length * ternas, 4)}
    return routes
