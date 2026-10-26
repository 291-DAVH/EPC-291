"""Public interface of the sld module."""
from pathlib import Path
from typing import List

from epc.modules.sld import lengths, repository

__all__ = ["circuits", "set_plan_lengths"]


def circuits(d: Path) -> List[dict]:
    """The circuits of every board of the project (tag, description, board): what other modules may reference, never create."""
    out: List[dict] = []
    for bid in repository.board_ids(d):
        data = repository.load_input(d, bid) or {}
        name = (data.get("board") or {}).get("name", "")
        out += [{"tag": c["tag"], "description": c.get("description", ""), "board": name, "board_id": bid} for c in data.get("circuits", []) if c.get("tag")]
    return out


def set_plan_lengths(provider) -> None:
    """The plan editor tells this module how to read what the drawings measured for each circuit (see `lengths`)."""
    lengths.set_plan_lengths(provider)
