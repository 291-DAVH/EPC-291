"""Schedule: validation and critical-path computation (CPM on durations, finish-to-start dependencies)."""
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.errors import Invalid
from epc.core.fsutil import today
from epc.modules.schedule import repository
from epc.modules.schedule.models import ScheduleIn
from epc.modules.wbs import public as wbs


def _date(s: str) -> Optional[dt.date]:
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def _duration(a: dict) -> int:
    return 0 if a["milestone"] else (_date(a["end"]) - _date(a["start"])).days + 1


def _order(acts: Dict[str, dict]) -> Optional[List[str]]:
    """Topological order, None when the dependencies contain a cycle."""
    indeg = {i: len(a["depends_on"]) for i, a in acts.items()}
    succ: Dict[str, List[str]] = {i: [] for i in acts}
    for i, a in acts.items():
        for p in a["depends_on"]:
            succ[p].append(i)
    ready = sorted(i for i, n in indeg.items() if n == 0)
    out: List[str] = []
    while ready:
        i = ready.pop(0)
        out.append(i)
        for s in succ[i]:
            indeg[s] -= 1
            if indeg[s] == 0:
                ready.append(s)
    return out if len(out) == len(acts) else None


def validate(d: Path, acts: List[dict]) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    ids = [a["id"] for a in acts]
    for a in acts:
        i = a["id"]
        if not i.strip() or ids.count(i) > 1:
            errors[f"id:{i}"] = "required and unique"
        if not a["name"].strip():
            errors[f"name:{i}"] = "required"
        s, e = _date(a["start"]), _date(a["end"])
        if not s or not e:
            errors[f"dates:{i}"] = "use ISO dates (YYYY-MM-DD)"
        elif e < s:
            errors[f"dates:{i}"] = "end before start"
        elif a["milestone"] and e != s:
            errors[f"dates:{i}"] = "a milestone has start = end"
        if not 0 <= a["progress"] <= 100:
            errors[f"progress:{i}"] = "must be between 0 and 100"
        for p in a["depends_on"]:
            if p not in ids or p == i:
                errors[f"depends_on:{i}"] = f"unknown or self predecessor {p}"
        if a["wbs_id"] and not wbs.has_node(d, a["wbs_id"]):
            errors[f"wbs_id:{i}"] = f"WBS node {a['wbs_id']} does not exist"
    if not errors and _order({a["id"]: a for a in acts}) is None:
        errors["depends_on"] = "dependencies contain a cycle"
    return errors


def view(d: Path) -> dict:
    acts = {a["id"]: a for a in repository.load(d)}
    if not acts:
        return {"activities": [], "start": None, "end": None, "span_days": 0, "critical_path": [], "counts": {"activities": 0, "late": 0, "conflicts": 0}}
    order = _order(acts) or list(acts)
    dur = {i: _duration(a) for i, a in acts.items()}
    es: Dict[str, int] = {}
    ef: Dict[str, int] = {}
    for i in order:
        es[i] = max((ef[p] for p in acts[i]["depends_on"]), default=0)
        ef[i] = es[i] + dur[i]
    length = max(ef.values())
    lf: Dict[str, int] = {}
    for i in reversed(order):
        succ = [lf_s - dur[s] for s, lf_s in lf.items() if i in acts[s]["depends_on"]]
        lf[i] = min(succ, default=length)
    now = today()
    out = []
    for i in sorted(acts, key=lambda k: (acts[k]["start"], k)):
        a = acts[i]
        slack = lf[i] - dur[i] - es[i]
        conflict = any(_date(acts[p]["end"]) >= _date(a["start"]) and not (a["milestone"] and _date(acts[p]["end"]) == _date(a["start"]))
                       for p in a["depends_on"])
        out.append({**a, "duration_days": dur[i], "slack_days": slack, "critical": slack == 0, "conflict": conflict,
                    "late": _date(a["end"]) < now and a["progress"] < 100})
    starts, ends = min(a["start"] for a in out), max(a["end"] for a in out)
    return {"activities": out, "start": starts, "end": ends, "span_days": (_date(ends) - _date(starts)).days + 1,
            "critical_path": [i for i in sorted(order, key=lambda k: es[k]) if lf[i] - dur[i] - es[i] == 0],
            "counts": {"activities": len(out), "late": sum(1 for a in out if a["late"]), "conflicts": sum(1 for a in out if a["conflict"])}}


def replace(d: Path, body: ScheduleIn) -> dict:
    acts = [a.model_dump() for a in body.activities]
    errors = validate(d, acts)
    if errors:
        raise Invalid(errors)
    repository.save(d, acts)
    return view(d)
