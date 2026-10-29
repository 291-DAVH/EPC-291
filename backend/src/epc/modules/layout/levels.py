"""A circuit drawn over several levels: how the length each sheet measured is put together.

The person draws such a circuit once on every sheet it touches, with the same tag. On the sheet of the board it goes from the board to the plenum it climbs through (its destination); on each
sheet above or below it goes from that plenum (its origin) to its loads, and on to the next plenum when the circuit keeps going. The engine measures each sheet on its own, with the height of
the plenums its way touches; here the parts are chained from the sheet of the board outward:

- a part that starts at a plenum begins where the part before it left: its distances are shifted by the way already made, and the height of its own entry plenum, which the part before already counted
  as its exit, is taken off once;
- the length of the circuit is what every sheet measured, without that repeated height;
- the moment length weighs every load of every sheet with its power (equal weights when one has none), by its distance from the board.

Anything that does not chain (no single sheet that starts at the board, two sheets at one level, a sheet that gives no distance to its plenum) is not measured: the board keeps its own length.
"""
from typing import Dict, List, NamedTuple, Optional

from epc.modules.layout import plenums, repository


class Part(NamedTuple):
    level: str                     # the sheet
    route: dict                    # what the engine derived for the circuit on it
    entry_rise: Optional[float]    # the height of the plenum it starts at; None when it starts at the board (or at anything that is not a plenum)


def _n(part: Part) -> int:
    return plenums.number(repository.split(part.level)[0])


def _origin(parts: List[Part]) -> Optional[Part]:
    roots = [p for p in parts if p.entry_rise is None]
    return roots[0] if len(roots) == 1 else None


def _before(p: Part, parts: List[Part], origin: Part) -> Optional[Part]:
    """The part the cable comes from to reach this one: the nearest one toward the board, on the same side of it."""
    o, n = _n(origin), _n(p)
    near = [q for q in parts if q is not p and (_n(q) - o) * (n - o) >= 0 and abs(_n(q) - o) < abs(n - o)]
    return max(near, key=lambda q: abs(_n(q) - o), default=None)


def _leaves_at(p: Part) -> Optional[float]:
    """How far from the board the cable leaves a part through its plenum (what the part measured to its destination, without the entry height the part before counted)."""
    d = p.route.get("destination_distance_m")
    return None if d is None else d - (p.entry_rise or 0.0)


def _offsets(parts: List[Part], origin: Part) -> Optional[Dict[int, float]]:
    """Where each part starts, in metres of cable from the board (by position in `parts`)."""
    at = {id(origin): 0.0}
    for p in sorted((q for q in parts if q is not origin), key=lambda q: abs(_n(q) - _n(origin))):
        before = _before(p, parts, origin)
        gone = None if before is None else _leaves_at(before)
        if gone is None:
            return None
        at[id(p)] = at[id(before)] + gone
    return at


def _loads(parts: List[Part], at: Dict[int, float]) -> List[tuple]:
    """(distance from the board, power or None) of every load of every part."""
    return [(x["distance_m"] - (p.entry_rise or 0.0) + at[id(p)], x.get("power_w")) for p in parts if p.route.get("loads", 0) > 0 for x in p.route.get("loads_detail", [])]


def _moment(loads: List[tuple]) -> float:
    known = all(w for _, w in loads)
    weights = [w if known else 1.0 for _, w in loads]
    return sum(w * d for w, (d, _) in zip(weights, loads)) / sum(weights)


def _whole(p: Part) -> bool:
    return bool(p.route.get("found")) and not p.route.get("unreached")


def _answer(levels: List[str], usable: bool, reason: str, loads: List[tuple], length: float) -> dict:
    return {"levels": levels, "usable": usable, "reason": reason, "loads_n": len(loads), "moment_length_m": round(_moment(loads), 4) if loads else 0.0,
            "max_distance_m": round(max(d for d, _ in loads), 4) if loads else 0.0, "length_m": round(length, 4)}


def combine(parts: List[Part]) -> dict:
    """What the sheets measured for one circuit, as one measure (the same fields as a circuit on one sheet; `usable` only when every part is whole and they chain)."""
    levels = [p.level for p in parts]
    origin = _origin(parts)
    at = _offsets(parts, origin) if origin else None
    if at is None:
        return _answer(levels, False, "levels", [], 0.0)
    loads = _loads(parts, at)
    length = sum(p.route.get("length_m", 0.0) - (p.entry_rise or 0.0) for p in parts)
    whole = all(_whole(p) for p in parts) and bool(loads)
    return _answer(levels, whole, "" if whole else "incomplete", loads, length)
