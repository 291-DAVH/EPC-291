"""The thresholds of the recognition (`params.json`) and what they mean for one plan: in metres when the units are known, else as fractions of the plan."""
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PARAMS: Dict[str, Any] = json.loads((Path(__file__).resolve().parent / "params.json").read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Scale:
    """Ranges in plan units for one plan: wall thickness, opening width, door radius."""
    wall_thickness: Tuple[float, float]
    opening_width: Tuple[float, float]
    door_radius: Tuple[float, float]
    known: bool


def scale_for(size: Tuple[float, float], units_per_metre: Optional[float], params: Dict[str, Any] = PARAMS) -> Scale:
    """With a scale the ranges are real sizes; without one they are guessed from the longest side and from the wall thickness once it is known (see `Calibration`)."""
    side = max(size) or 1.0
    if units_per_metre:
        m = params["metres"]
        return Scale(*(tuple(v * units_per_metre for v in m[k]) for k in ("wall_thickness", "opening_width", "door_radius")), known=True)     # type: ignore[arg-type]
    rel = params["relative"]
    lo, hi = rel["wall_thickness"]
    return Scale((lo * side, hi * side), (0.0, side), (0.0, side), known=False)


class Hints:
    """What the names of layers and blocks say (`MUROS`, `PUERTA-1`, `A$C12345$ventana`...): a clue, never a certainty."""

    def __init__(self, params: Dict[str, Any] = PARAMS):
        self._rx = {kind: re.compile("|".join(re.escape(w) for w in words), re.I) for kind, words in params["hints"].items()}

    def of(self, name: str) -> str:
        return next((kind for kind, rx in self._rx.items() if name and rx.search(name)), "")
