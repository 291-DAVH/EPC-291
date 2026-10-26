"""Where the length of each circuit comes from: the drawn plan or the data of the board.

A circuit says which one it wants (`length_source`: auto, plan or data). The plan is read through a provider that the layout module registers (the plan editor
depends on this module, not the other way round). With `auto` the plan is used when it measured the circuit completely, and the data otherwise. What the plan gives is
the length of the moment method: for one load (board - load) the distance to it, for several loads the length that, with the whole current, drops the same as the
sum of current x distance of each load."""

import copy
from pathlib import Path
from typing import Callable, Dict, Optional

SOURCES = ("auto", "plan", "data")

PlanLengths = Callable[[Path], Dict[str, dict]]
_PLAN: Optional[PlanLengths] = None


def set_plan_lengths(provider: Optional[PlanLengths]) -> None:
    global _PLAN
    _PLAN = provider


def plan_lengths(d: Path) -> Dict[str, dict]:
    return _PLAN(d) if _PLAN else {}


def choose(c: dict, plan: Optional[dict]) -> dict:
    """What is used for one circuit and why: the source, both lengths (None when not available) and whether it is measured by moments."""
    want = c.get("length_source") or "auto"
    data_m = float(c.get("length_m") or 0)
    usable = bool(plan and plan.get("usable"))
    plan_m = plan.get("moment_length_m") if plan else None
    reason = ""
    if c.get("route"):
        used, reason = "data", "route"                                    # a real route (tramos) is data and owns the length
    elif want == "data":
        used = "data"
    elif usable:
        used = "plan"
    else:
        used, reason = "data", (plan or {}).get("reason") or "not_drawn"
    return {"setting": want, "used": used, "data_m": data_m, "plan_m": plan_m, "plan_max_m": (plan or {}).get("max_distance_m"), "plan_total_m": (plan or {}).get("length_m"),
            "levels": (plan or {}).get("levels", []), "moments": used == "plan" and (plan or {}).get("loads_n", 0) >= 2, "reason": reason,
            "fallback": want == "plan" and used == "data" and reason not in ("route",)}


def info(d: Path, circuits: list) -> Dict[str, dict]:
    plan = plan_lengths(d)
    return {c["tag"]: choose(c, plan.get(c["tag"])) for c in circuits if c.get("tag")}


def apply(d: Path, data: dict) -> dict:
    """The board data with the length each circuit uses (the plan's replaces the data's). The data stored is not touched."""
    out = copy.deepcopy(data)
    chosen = info(d, out.get("circuits", []))
    for c in out.get("circuits", []):
        i = chosen.get(c.get("tag"))
        if i and i["used"] == "plan":
            c["length_m"] = round(i["plan_m"], 3)
            if i["moments"]:
                c["moments"] = True
    return out
