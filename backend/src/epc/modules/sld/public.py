"""Public interface of the sld module."""
from pathlib import Path
from typing import List

from epc.modules.sld import lengths, repository

__all__ = ["circuits", "boards", "set_plan_lengths", "add_circuits"]


def circuits(d: Path) -> List[dict]:
    """The circuits of every board of the project (tag, description, board): what other modules may reference, never create."""
    out: List[dict] = []
    for bid in repository.board_ids(d):
        data = repository.load_input(d, bid) or {}
        name = (data.get("board") or {}).get("name", "")
        out += [{"tag": c["tag"], "description": c.get("description", ""), "board": name, "board_id": bid} for c in data.get("circuits", []) if c.get("tag")]
    return out


def boards(d: Path) -> List[dict]:
    """The boards of the project (id and name): what the plan editor offers when a board symbol or a load is placed."""
    from epc.modules.sld import boards as _boards
    return [{"id": b["id"], "name": b["name"]} for b in _boards.boards(d)]


def set_plan_lengths(provider) -> None:
    """The plan editor tells this module how to read what the drawings measured for each circuit (see `lengths`)."""
    lengths.set_plan_lengths(provider)


def add_circuits(d: Path, specs: List[dict], board_id: str = "") -> dict:
    """Add circuits to a board of the project (the first one when none is named); see `boards.add_circuits`."""
    from epc.modules.sld import boards
    return boards.add_circuits(d, specs, board_id)
