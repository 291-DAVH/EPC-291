"""Coordination between disciplines that stay separate: each issues what it occupies, the clashes are found on those issues, and the conversations and the data that cross
go through threads and exchanges. A discipline's drawings and calculations are never opened to another; only footprints are."""
from pathlib import Path
from typing import Dict, List

from epc.core import clock
from epc.core.errors import Forbidden, Invalid
from epc.modules.coordination import detection, exchanges, repository, threads
from epc.modules.identity import public as identity
from epc.modules.layout import public as layout
from epc.modules.projects import public as projects

MEMBERS = "members.json"


# ---------------------------------------------------------------- who may edit which discipline
def members(d: Path) -> Dict[str, List[str]]:
    return repository.read(d, MEMBERS, {}) or {}


def set_members(d: Path, table: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Who works in each discipline. A discipline without members is open to everyone who can edit the project; with members, only they (and the engineering team) edit its drawings."""
    clean = {repository.discipline_id(k): sorted({e.strip().lower() for e in v if e.strip()}) for k, v in table.items()}
    clean = {k: v for k, v in clean.items() if v}
    repository.write(d, MEMBERS, clean)
    identity.audit_event("discipline_members_changed", target=projects.project_id(d), org_slug=projects.read_meta(d).get("org", ""), detail={"disciplines": sorted(clean)})
    return clean


def guard(d: Path, discipline: str) -> None:
    """Refuse a change to the drawings of a discipline to someone who is not in it. Reading and commenting are open to all."""
    allowed = members(d).get(discipline)
    if not allowed or identity.is_admin():
        return
    if identity.current_user().get("email", "").lower() not in allowed:
        raise Forbidden(f"the drawings of {discipline} are edited by its own team: ask for a change on a thread")


layout.set_edit_guard(guard)                                    # the layout module asks this before it saves, deletes or replaces anything


# ---------------------------------------------------------------- issuing
def emit(d: Path, discipline: str, note: str = "") -> dict:
    """A discipline issues what it has drawn: the footprints become the version the others coordinate against. Returns the clashes that were not there at the last run."""
    repository.discipline_id(discipline)
    guard(d, discipline)
    drawn = detection.working_items(d).get(discipline, [])
    if not drawn:
        raise Invalid({"discipline": "there is nothing to issue: draw and calibrate the scale of a sheet of this discipline first"})
    user = identity.current_user()
    rev = repository.save_emission(d, discipline, {"discipline": discipline, "at": clock.now_local(), "by": user.get("email", ""), "note": note.strip()[:500],
                                                     "sheets": sorted({i["sheet"] for i in drawn}), "items": drawn})
    result = detection.detect(d, "auto")
    fresh = detection.new_since_last_run(d, result["clashes"])
    identity.audit_event("coordination_issued", target=f"{projects.project_id(d)}:{discipline}", org_slug=projects.read_meta(d).get("org", ""), detail={"rev": rev, "new_clashes": len(fresh)})
    return {"discipline": discipline, "rev": rev, "elements": len(drawn), "new_clashes": fresh, "counts": result["counts"]}


def emissions(d: Path) -> List[dict]:
    """The latest issue of each discipline (without the footprints), and how many issues it has made."""
    out = []
    for disc in repository.emitted_disciplines(d):
        e = repository.load_emission(d, disc) or {}
        out.append({"discipline": disc, "rev": e.get("rev"), "at": e.get("at"), "by": e.get("by"), "note": e.get("note", ""), "sheets": e.get("sheets", []), "elements": len(e.get("items", [])),
                    "issues": len(repository.emission_revs(d, disc))})
    return out


def _drawn_disciplines(d: Path) -> List[str]:
    return sorted({s["discipline"] for s in layout.sheets(d)})


def overview(d: Path) -> dict:
    found = detection.detect(d, "auto")
    open_threads = [t for t in threads.listing(d) if t["status"] in ("open", "review")]
    people = members(d)
    return {"disciplines": sorted(set(_drawn_disciplines(d)) | set(repository.emitted_disciplines(d)) | set(people)), "drawn": _drawn_disciplines(d), "emissions": emissions(d), "members": people,
            "counts": {**found["counts"], "threads": len(open_threads)}, "sources": found["sources"], "settings": detection.settings(d), "matrix": exchanges.matrix(d)}


def _open_clashes_of(d: Path, discipline: str) -> List[dict]:
    return [c for c in detection.detect(d, "auto")["clashes"] if c["status"] == "open" and discipline in (c["a"]["discipline"], c["b"]["discipline"])]


def _asked_of(d: Path, discipline: str) -> List[dict]:
    return [t for t in threads.listing(d, discipline=discipline) if t["to_discipline"] == discipline and t["status"] in ("open", "review")]


def _stale_data_of(d: Path, discipline: str) -> List[dict]:
    return [x for x in exchanges.listing(d) if discipline in x["consumers"] and x["states"][discipline] != "delivered"]


def notifications(d: Path, discipline: str) -> dict:
    """What a discipline should look at: clashes that appeared at the last coordination run, requests addressed to it that are still open, and data it uses that changed."""
    repository.discipline_id(discipline)
    new_ids = set((repository.read(d, "last_run.json", {}) or {}).get("new", []))
    clashes, asked, stale = _open_clashes_of(d, discipline), _asked_of(d, discipline), _stale_data_of(d, discipline)
    return {"discipline": discipline, "open_clashes": len(clashes), "new_clashes": [c for c in clashes if c["id"] in new_ids], "requests": asked, "data": stale,
            "count": len(clashes) + len(asked) + len(stale)}
