"""Public interface of the sld module."""
from pathlib import Path
from typing import List

from epc.modules.sld import lengths, repository

__all__ = ["circuits", "boards", "set_plan_lengths", "add_circuits", "size_cables"]


def circuits(d: Path) -> List[dict]:
    """The circuits of every board of the project (tag, description, board): what other modules may reference, never create."""
    out: List[dict] = []
    for bid in repository.board_ids(d):
        data = repository.load_input(d, bid) or {}
        name = (data.get("board") or {}).get("name", "")
        out += [{"tag": c["tag"], "description": c.get("description", ""), "board": name, "board_id": bid} for c in data.get("circuits", []) if c.get("tag")]
    return out


def boards(d: Path) -> List[dict]:
    """The boards of the project (id, name and where each is: its level and its place): what the plan editor offers when a board symbol or a load is placed, and what decides where the plenum is asked for."""
    from epc.modules.sld import boards as _boards
    return [{"id": b["id"], "name": b["name"], "level": b["level"], "location": b["location"]} for b in _boards.boards(d)]


def set_plan_lengths(provider) -> None:
    """The plan editor tells this module how to read what the drawings measured for each circuit (see `lengths`)."""
    lengths.set_plan_lengths(provider)


def add_circuits(d: Path, specs: List[dict], board_id: str = "") -> dict:
    """Add circuits to a board of the project (the first one when none is named); see `boards.add_circuits`."""
    from epc.modules.sld import boards
    return boards.add_circuits(d, specs, board_id)


def size_cables(d: Path, board_id: str = ""):
    """Calculate the board (or all of them) and give the cable of each circuit: ({tag: {section_mm2, in_a, ib_a, du_pct, complies, board}}, warnings)."""
    from epc.modules.sld import cables
    return cables.size(d, board_id)
