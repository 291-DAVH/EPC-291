"""The floor each plan of a sheet is. Plans say it in their title ("PLANTA BAJA", "PLANTA ALTA", "PLANTA 2", "SUBSUELO"): the patterns are data (`levels` in params.json). A plan with no title that says a floor
is only numbered in reading order; that is a guess and the result says so (`source`)."""
import math
import re
from typing import List, Optional, Tuple

from epc_arch.config import PARAMS
from epc_arch.model import Level, Text

_RULES = [(re.compile(r["re"], re.I), r["index"]) for r in PARAMS["levels"]]
Box = Tuple[float, float, float, float]


def _distance(t: Text, box: Box) -> float:
    return math.hypot(max(box[0] - t.at[0], 0.0, t.at[0] - box[2]), max(box[1] - t.at[1], 0.0, t.at[1] - box[3]))


def _floor(value: str) -> Optional[Tuple[int, str, Optional[int]]]:
    """(0 for a title, 1 for a bare abbreviation, the title without its bubble number, the floor index) when the text names a floor ("PLANTA BAJA" is worth more than a bare "PB")."""
    title = re.sub(r"^\d+\s+(?=\D)", "", value).strip()                  # the number of the view's bubble comes first
    for n, (rx, index) in enumerate(_RULES):
        m = rx.match(title)                                                 # a title starts with the floor: "PB-01" (a room) or "terraza" (its name) are not titles
        if m:
            return int(len(title) <= 2), title, int(re.sub(r"\s+", "", m.group(1))) if index == "$1" else index
    return None


def named(texts: List[Text], box: Box) -> Optional[Level]:
    """The floor that the closest title around a view says (a full title before a bare abbreviation), or None when no text near it names one."""
    found = [(f[0], _distance(t, box), f) for t in texts for f in [_floor(t.value)] if f]
    if not found:
        return None
    _, _, (_, title, idx) = min(found, key=lambda x: (x[0], x[1]))
    return Level(title, idx, "text")


def assign(boxes: List[Box], texts: List[List[Text]]) -> List[Level]:
    """A level for each view, in the order given: from its title, else its place in reading order."""
    return [named(t, b) or Level(f"plan {i + 1}", None, "order") for i, (b, t) in enumerate(zip(boxes, texts))]


def order(levels: List[Level]) -> List[int]:
    """The indices of the plans from the lowest floor to the highest; plans with no floor keep their reading order after those that have one."""
    return sorted(range(len(levels)), key=lambda i: (levels[i].index is None, levels[i].index if levels[i].index is not None else 0, i))
