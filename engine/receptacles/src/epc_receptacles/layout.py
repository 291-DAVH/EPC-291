"""Where the outlets of a room go: spread evenly along its walls, away from the corners.

The room is a rectangle `length_m` along x and `width_m` along y, with its corner at (0, 0). The walls are walked in a fixed order (south, east, north, west) and each outlet sits on
its wall at the middle of an equal share of the perimeter; one that falls in a corner is moved along the wall until it is `corner_clearance_m` away.
"""
from typing import Dict, List

from epc_receptacles.config import PARAMS


def _wall_point(length: float, width: float, s: float) -> tuple:
    """(wall, offset along it, its length) of the point `s` metres along the perimeter, starting at the corner (0, 0) towards +x."""
    if s < length:
        return "south", s, length
    s -= length
    if s < width:
        return "east", s, width
    s -= width
    if s < length:
        return "north", s, length
    return "west", s - length, width


def _clear_of_corners(offset: float, wall_len: float, clearance: float) -> float:
    """The offset along a wall kept `clearance` away from both corners (the middle of a wall too short for that)."""
    if wall_len <= 2 * clearance:
        return wall_len / 2
    return min(max(offset, clearance), wall_len - clearance)


def _on_wall(wall: str, length: float, width: float, offset: float) -> tuple:
    """The place in metres of a point `offset` along a wall, walked in the order south, east, north, west."""
    if wall == "south":
        return offset, 0.0
    if wall == "east":
        return length, offset
    if wall == "north":
        return length - offset, width
    return 0.0, width - offset


def positions(length: float, width: float, count: int, height_m: float, prefix: str = "R") -> List[Dict]:
    """`count` outlets along the walls of a room, each with its tag, its place in metres, the mounting height and the wall it is on."""
    perimeter = 2 * (length + width)
    clearance = PARAMS["corner_clearance_m"]
    out = []
    for i in range(count):
        wall, offset, wall_len = _wall_point(length, width, (i + 0.5) * perimeter / count)
        x, y = _on_wall(wall, length, width, _clear_of_corners(offset, wall_len, clearance))
        out.append({"tag": f"{prefix}{i + 1}", "x_m": round(x, 4), "y_m": round(y, 4), "z_m": height_m, "wall": wall})
    return out
