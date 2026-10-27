"""Clash detection over the project: the footprints of what each discipline drew (or last issued), the spaces reserved, the rules, and the state each clash was left in."""
from pathlib import Path
from typing import Dict, List, Optional

from epc.core import clock
from epc.core.errors import Invalid
from epc.modules.coordination import repository, rules
from epc.modules.identity import public as identity
from epc.modules.layout import public as layout

SOURCES = ("auto", "issued", "working")
SETTINGS = "settings.json"


def _plan():
    from epc_plan import clash, core, footprint
    return clash, core, footprint


def settings(d: Path) -> dict:
    _, core, _ = _plan()
    return {"story_height_m": core.PARAMS["coordination"]["story_height_m"], **(repository.read(d, SETTINGS, {}) or {})}


def save_settings(d: Path, story_height_m: float) -> dict:
    if not (0.5 <= story_height_m <= 20):
        raise Invalid({"story_height_m": "between 0.5 and 20 m"})
    repository.write(d, SETTINGS, {"story_height_m": story_height_m})
    return settings(d)


def working_items(d: Path) -> Dict[str, List[dict]]:
    """The footprints of what is drawn now, by discipline. A drawing the engine cannot read gives none (it is reported where it is edited)."""
    _, core, footprint = _plan()
    story = settings(d)["story_height_m"]
    out: Dict[str, List[dict]] = {}
    for sheet, doc in layout.documents(d):
        try:
            items = footprint.footprints(doc, sheet, story)
        except core.PlanError:
            continue
        out.setdefault(doc["discipline"], []).extend(items)
    return out


def issued_items(d: Path) -> Dict[str, List[dict]]:
    return {disc: (repository.load_emission(d, disc) or {}).get("items", []) for disc in repository.emitted_disciplines(d)}


def items_by_discipline(d: Path, source: str = "auto") -> Dict[str, dict]:
    """{discipline: {"source": "issued"|"working", "items": [...]}} for the source asked: `auto` uses what a discipline issued and, until it issues, what it has drawn."""
    if source not in SOURCES:
        raise Invalid({"source": "one of " + ", ".join(SOURCES)})
    working, issued = working_items(d), issued_items(d)
    out: Dict[str, dict] = {}
    for disc in sorted(set(working) | set(issued)):
        use = "issued" if source == "issued" or (source == "auto" and disc in issued) else "working"
        items = issued.get(disc, []) if use == "issued" else working.get(disc, [])
        if items:
            out[disc] = {"source": use, "items": items}
    return out


def reservation_items(d: Path) -> List[dict]:
    """A space reserved by a discipline counts as one of its elements while the reservation stands: the others must keep out of it."""
    out = []
    for t in repository.read(d, "threads.json", []):
        g = t.get("geom")
        if t["kind"] == "reservation" and t["status"] in ("open", "accepted") and g:
            out.append({"sheet": g.get("sheet", ""), "discipline": t["from_discipline"], "level": g["level"], "level_number": g["level_number"], "id": t["id"], "kind": "RES", "shape": "line",
                        "tag": t["title"] or t["id"], "points": g["points_m"], "width_m": g["width_m"], "z0": g["z0"], "z1": g["z1"], "clear_m": 0.0, "origin": "reservation"})
    return out


def _status(d: Path) -> dict:
    return repository.read(d, "clash_status.json", {}) or {}


def detect(d: Path, source: str = "auto", project_rules: Optional[list] = None) -> dict:
    """The clashes of the project with the state each one was left in, and where each discipline's footprints came from."""
    clash, _, _ = _plan()
    groups = items_by_discipline(d, source)
    items = [it for g in groups.values() for it in g["items"]] + reservation_items(d)
    found = clash.detect(items, project_rules if project_rules is not None else rules.effective(d))
    status = _status(d)
    for c in found:
        c.update({"status": "open", "reason": "", **{k: v for k, v in (status.get(c["id"]) or {}).items() if k in ("status", "reason", "by", "at")}})
    open_n = sum(1 for c in found if c["status"] == "open")
    return {"clashes": found, "sources": {k: v["source"] for k, v in groups.items()}, "counts": {"total": len(found), "open": open_n, "accepted": len(found) - open_n,
            "hard": sum(1 for c in found if c["type"] == "hard" and c["status"] == "open")}}


def set_status(d: Path, clash_id: str, status: str, reason: str) -> dict:
    """Leave a clash accepted (with the reason, who and when: it stops alerting but stays on record) or open it again."""
    if status not in ("open", "accepted"):
        raise Invalid({"status": "open or accepted"})
    if status == "accepted" and not reason.strip():
        raise Invalid({"reason": "say why the clash is accepted"})
    table = _status(d)
    if status == "open":
        table.pop(clash_id, None)
    else:
        table[clash_id] = {"status": "accepted", "reason": reason.strip(), "by": identity.current_user().get("email", ""), "at": clock.now_local()}
    repository.write(d, "clash_status.json", table)
    identity.audit_event("clash_status_changed", target=clash_id, detail={"status": status})
    return {"id": clash_id, "status": status, "reason": reason.strip() if status == "accepted" else ""}


def reference(d: Path, discipline: str, level: str, source: str = "auto") -> List[dict]:
    """What the other disciplines occupy on a level, for the editor to show behind the drawing: footprints only, never their drawings or calculations."""
    repository.discipline_id(discipline)
    return [it for disc, g in items_by_discipline(d, source).items() if disc != discipline for it in g["items"] if it["level"] == level] + \
           [it for it in reservation_items(d) if it["discipline"] != discipline and it["level"] == level]


def new_since_last_run(d: Path, found: List[dict]) -> List[dict]:
    """The clashes not seen in the previous coordination run; the run is recorded so the next one reports only what is new."""
    last = repository.read(d, "last_run.json", {}) or {}
    known = set(last.get("ids", []))
    fresh = [c for c in found if c["id"] not in known]
    repository.write(d, "last_run.json", {"at": clock.now_local(), "ids": sorted({c["id"] for c in found}), "new": [c["id"] for c in fresh]})
    return fresh


def overlay(d: Path, level: str, source: str = "auto") -> dict:
    """Everything every discipline occupies on a level, with the clashes of that level: one read-only view where the disciplines are seen together, each still owning its own drawing."""
    groups = items_by_discipline(d, source)
    found = detect(d, source)
    return {"items": [it for g in groups.values() for it in g["items"] if it["level"] == level] + [it for it in reservation_items(d) if it["level"] == level],
            "clashes": [c for c in found["clashes"] if c["level"] == level], "sources": {k: v["source"] for k, v in groups.items()}}
