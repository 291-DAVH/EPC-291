"""Plenums (vertical shafts) of the building: where one starts, how far it goes and the node that stands for it on the plan of every level it crosses.

A plenum is defined once (a code, a place in metres from the origin of the plan, the height it adds, the level it starts on and how many levels it reaches up and down: all of them or a number). The drawing
of each level in range gets its node `PL` with the same code, at the same place; a level added later that falls in range gets it too. The definitions are kept apart from the drawings, in `plenums.json`
next to the sheets, and the drawings only hold their nodes.
"""
import math
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from epc.core.errors import Invalid
from epc.core.fsutil import read_json, write_json
from epc.modules.layout import repository

FILE = "plenums.json"
CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,19}$")
LEVEL = re.compile(r"^L(-?\d{1,2})$")
MAX_REACH = 50


def _file(d: Path) -> Path:
    return repository.base(d) / FILE


def load(d: Path) -> List[dict]:
    return (read_json(_file(d), {}) or {}).get("plenums", [])


def _store(d: Path, items: List[dict]) -> None:
    _file(d).parent.mkdir(parents=True, exist_ok=True)
    write_json(_file(d), {"schema_version": "1.0", "plenums": items})


def number(level: str) -> int:
    """`L-1` is -1, `L2` is 2."""
    return int(LEVEL.match(level).group(1))


def covers(p: dict, base: str) -> bool:
    """Whether a plenum crosses a level: its own, and the ones up to `up` above and `down` below (None: all of them)."""
    here, start = number(base), number(p["level"])
    if here == start:
        return True
    reach = p.get("up") if here > start else p.get("down")
    return reach is None or abs(here - start) <= reach


def _reach(value, name: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_REACH:
        raise Invalid({name: f"all the levels (empty) or a number from 0 to {MAX_REACH}"})
    return value


def _check(body: dict, vertical_kind: Callable[[str], Optional[str]]) -> dict:
    errors: Dict[str, str] = {}
    code = str(body.get("code", "")).strip()
    if not CODE.match(code):
        errors["code"] = "letters, digits, - and _, up to 20"
    if not LEVEL.match(str(body.get("level", ""))):
        errors["level"] = "a level of the building: L-1, L0, L1..."
    kind = vertical_kind(str(body.get("discipline", "")))
    if kind is None:
        errors["discipline"] = "this discipline has no kind of vertical shaft"
    for key in ("x_m", "y_m"):
        if isinstance(body.get(key), bool) or not isinstance(body.get(key), (int, float)) or not math.isfinite(body[key]):
            errors[key] = "a number of metres from the origin of the plan"
    height = body.get("altura_m", 3.0)
    if isinstance(height, bool) or not isinstance(height, (int, float)) or not 0 < height <= 30:
        errors["altura_m"] = "the height the shaft adds, above 0 and up to 30 m"
    if errors:
        raise Invalid(errors)
    return {"code": code, "discipline": body["discipline"], "kind": kind, "level": body["level"], "x_m": round(float(body["x_m"]), 3), "y_m": round(float(body["y_m"]), 3), "altura_m": float(height),
            "up": _reach(body.get("up"), "up"), "down": _reach(body.get("down"), "down")}


def _metres_per_unit(scale: Optional[dict]) -> Optional[float]:
    try:
        run = math.hypot(scale["p2"][0] - scale["p1"][0], scale["p2"][1] - scale["p1"][1])
        return float(scale["distance_m"]) / run if run > 0 else None
    except (TypeError, KeyError, IndexError, ValueError):
        return None


def _has(data: dict, p: dict) -> bool:
    return any(n.get("kind") == p["kind"] and (n.get("attrs") or {}).get("pleno") == p["code"] for n in data.get("nodes", []))


def _node(data: dict, p: dict, k: float) -> dict:
    ox, oy = (data.get("origin") or [0.0, 0.0])[:2]
    taken = {n["id"] for n in data.get("nodes", [])} | {ln["id"] for ln in data.get("lines", [])}
    nid, i = f"pl_{p['code']}", 2
    while nid in taken:
        nid, i = f"pl_{p['code']}_{i}", i + 1
    return {"id": nid, "kind": p["kind"], "x": round(ox + p["x_m"] / k, 3), "y": round(oy - p["y_m"] / k, 3), "tag": "", "board": "", "circuit": "", "attrs": {"pleno": p["code"], "altura_m": p["altura_m"]}}


def _into(d: Path, p: dict, base: str, blank: Callable[[], dict]) -> int:
    """The node of a plenum in the sheet of its discipline on a level (the sheet is made when it does not exist): 1 when it was added, 0 when it was there or the plan has no scale yet."""
    key = f"{base}@{p['discipline']}"
    k = _metres_per_unit(repository.architecture_scale(d, key))
    if k is None:
        return 0
    data = repository.load_drawing(d, key) or {**blank(), "discipline": p["discipline"]}
    if _has(data, p):
        return 0
    data = {**data, "nodes": [*data.get("nodes", []), _node(data, p, k)]}
    repository.save_drawing(d, key, data)
    return 1


def sync(d: Path, blank: Callable[[], dict]) -> int:
    """Every plenum in the drawing of every level it crosses (the ones that exist now); how many nodes were added."""
    bases = sorted({repository.split(lv)[0] for lv in repository.levels(d) if LEVEL.match(repository.split(lv)[0])}, key=number)
    return sum(_into(d, p, base, blank) for p in load(d) for base in bases if covers(p, base))


def define(d: Path, body: dict, vertical_kind: Callable[[str], Optional[str]], blank: Callable[[], dict]) -> dict:
    """Define (or redefine, by its code) a plenum and put it in the drawings it crosses."""
    p = _check(body, vertical_kind)
    _store(d, [x for x in load(d) if not (x["code"] == p["code"] and x["discipline"] == p["discipline"])] + [p])
    return {"plenums": load(d), "added": sync(d, blank)}


def remove(d: Path, code: str, discipline: str) -> List[dict]:
    """Forget a plenum. Its nodes stay in the drawings (they are drawing: the person deletes them if they want)."""
    left = [x for x in load(d) if not (x["code"] == code and x["discipline"] == discipline)]
    _store(d, left)
    return left
