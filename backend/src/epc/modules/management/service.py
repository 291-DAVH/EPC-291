"""Project management views: portfolio, project summary and progress reports.

This module composes data from other modules through their public interfaces only. WBS/EDT, project backlog,
schedule, risks and change control will grow here.
"""
import datetime as dt
from pathlib import Path
from typing import Tuple

from epc.core.fsutil import is_inside, safe_file, today
from epc.core.errors import NotFound
from epc.modules.deliverables import public as deliverables
from epc.modules.intake import public as intake
from epc.modules.management import repository
from epc.modules.projects import public as projects
from epc.modules.requirements import public as requirements

HEALTH_ORDER = {"delayed": 0, "at_risk": 1, "on_track": 2}


def summary(d: Path) -> dict:
    meta, st = projects.read_meta(d), projects.read_status(d)
    return {
        "id": projects.project_id(d), "name": meta.get("project_name") or meta.get("project_code") or d.name,
        "client": meta.get("client", d.parent.name), "code": meta.get("project_code", d.name), "disciplines": meta.get("disciplines", []),
        "methodology": meta.get("methodology"), "state": st.get("state", "active"), "phase": st.get("phase") or meta.get("phase"),
        "progress": st.get("progress_pct", 0), "health": st.get("health", "on_track"), "manager": st.get("manager", ""),
        "location": st.get("location", ""), "start": st.get("start"), "due": st.get("due"), "next_milestone": st.get("next_milestone"),
        "updated": st.get("updated"), "created": meta.get("created"),
        "deliverables": deliverables.counts(d), "inputs": intake.input_counts(d),
    }


def portfolio() -> dict:
    dirs = projects.list_project_dirs()
    ps = [summary(d) for d in dirs]
    by_id = {projects.project_id(d): d for d in dirs}
    active = [p for p in ps if p["state"] == "active"]
    soon = (today() + dt.timedelta(days=14)).isoformat()
    due_soon = sum(deliverables.due_soon(by_id[p["id"]], soon) for p in active)
    kpis = {
        "total": len(ps), "active": len(active), "closed": len(ps) - len(active),
        "on_track": sum(1 for p in active if p["health"] == "on_track"), "at_risk": sum(1 for p in active if p["health"] == "at_risk"),
        "delayed": sum(1 for p in active if p["health"] == "delayed"),
        "deliverables_delivered": sum(p["deliverables"]["delivered"] for p in ps), "deliverables_total": sum(p["deliverables"]["total"] for p in ps),
        "deliverables_due_soon": due_soon, "inputs_open": sum(p["inputs"]["open"] for p in active),
    }
    ps.sort(key=lambda p: (p["state"] != "active", HEALTH_ORDER.get(p["health"], 3), p["due"] or "9999"))
    return {"kpis": kpis, "projects": ps, "today": today().isoformat()}


def detail(d: Path) -> dict:
    s = summary(d)
    s["milestones"] = projects.read_status(d).get("milestones", [])
    s["requirements_count"] = requirements.count(d)
    return s


def reports(d: Path) -> list:
    base = d / "deliverables"
    items = [{**x, "downloadable": bool(x.get("file") and is_inside(base, x["file"]))} for x in repository.reports_index(d)]
    return sorted(items, key=lambda x: x.get("date", ""), reverse=True)


def report_file(d: Path, report_id: str) -> Tuple[Path, str]:
    item = next((x for x in repository.reports_index(d) if x.get("id") == report_id), None)
    if not item or not item.get("file"):
        raise NotFound("file not found")
    return safe_file(d / "deliverables", item["file"]), f"{report_id}.pdf"
