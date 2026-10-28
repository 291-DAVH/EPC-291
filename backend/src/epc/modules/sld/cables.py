"""The cables of the circuits of the boards, sized from the data of each board (the plan's lengths included): what the plan editor needs to size its conduits and trays."""
from pathlib import Path
from typing import Dict, List, Tuple

from epc.core.errors import DomainError
from epc.modules.sld import jobs, repository, results


def _rows(d: Path, bid: str) -> Tuple[Dict[str, dict], List[str]]:
    """Calculate one board (no diagrams) and read what it gave: {tag: {section_mm2, in_a, ib_a, du_pct, complies, board}} and the reasons it could not be done."""
    try:
        jobs.generate(d, wait=True, diagrams="none", bid=bid)
    except DomainError as e:
        return {}, [f"{bid}: {e}"]
    rows = results.calculation(d, bid)["rows"]
    return {r["tag"]: {"section_mm2": r.get("S"), "in_a": r.get("In"), "ib_a": r.get("Ib"), "du_pct": r.get("dU"), "complies": r.get("cumple"), "board": bid} for r in rows}, []


def size(d: Path, board_id: str = "") -> Tuple[Dict[str, dict], List[str]]:
    """Every circuit of the board named (or of all the boards) with its cable, and the warnings of the boards that could not be calculated."""
    found: Dict[str, dict] = {}
    notes: List[str] = []
    for bid in ([board_id] if board_id else repository.board_ids(d)):
        rows, why = _rows(d, bid)
        found.update(rows)
        notes += why
    return found, notes
