"""The study of a sheet: the lighting calculation kept with the sheet, whether it is still good for the rooms as they are drawn now, and its report as a document of the project.

  <project>/workspace/02-engineering/layout/<sheet>/src/lighting.json            the study (what was asked, what came out, the fingerprint of both)
  <project>/workspace/02-engineering/electrical/PQ-01/docs/LIGHTING_<sheet>.pdf  its report: from there the issuing flow offers it as a deliverable
"""
import re
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from epc.core import clock, engine
from epc.core.errors import Conflict, Failure, Invalid, NotFound
from epc.core.fsutil import read_json, write_json
from epc.modules.identity import public as identity
from epc.modules.layout import public as layout
from epc.modules.lighting import report, service
from epc.modules.lighting.models import CalcIn, CalcOptions, PlanRoom, RoomParams, Sheet
from epc.modules.projects import public as projects

FILE = "lighting.json"
DOCS = Path("workspace") / "02-engineering" / "electrical" / "PQ-01" / "docs"          # where the issuing flow looks for the documents of the engineering workspace
KEPT = ("saved_at", "saved_by", "fingerprint", "result", "placements", "rooms", "skipped", "warnings")
UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _path(d: Path, sheet: str) -> Path:
    return layout.source_file(d, sheet, FILE)


def _who() -> str:
    user = identity.current_user()
    return user.get("email", "") or user.get("name", "")


def report_path(d: Path, sheet: str) -> Path:
    return d / DOCS / f"LIGHTING_{UNSAFE.sub('_', sheet)}.pdf"


def save(d: Path, sheet: str, body: CalcIn) -> dict:
    """Calculate and keep the study of a sheet (replacing the one it had). A request where no room could be calculated is not a study."""
    if layout.saved_drawing(d, sheet) is None:
        raise NotFound("sheet not found")
    out = service.calc(d, body)
    if out["result"] is None:
        raise Invalid({"study": "no room could be calculated: give each one a luminaire and an activity or a target"})
    stored = {"schema_version": "1.0", "sheet": sheet, "saved_at": clock.now_local(), "saved_by": _who(), "input": body.model_dump(), **{k: out[k] for k in KEPT if k in out}}
    write_json(_path(d, sheet), stored)
    identity.audit_event("lighting_study_saved", target=f"{projects.project_id(d)}:{sheet}", org_slug=projects.read_meta(d).get("org", ""), detail={"rooms": len(out["result"]["rooms"])})
    return view(d, sheet)


def _asked_now(saved: dict, options: dict, lang: str) -> Optional[CalcIn]:
    """The request the sheet would make today, from the drawing as it is saved (None when what it says is not a valid request)."""
    known = set(RoomParams.model_fields)
    rooms = saved.get("rooms") or []
    try:
        return CalcIn(sheet=Sheet(scale=saved.get("scale"), rooms=[PlanRoom(id=r["id"], name=r.get("name", ""), points=r["points"]) for r in rooms]),
                      rooms={r["id"]: RoomParams(**{k: v for k, v in r["lighting"].items() if k in known}) for r in rooms if r.get("lighting")},
                      options=CalcOptions(**options), lang=lang)
    except (ValidationError, KeyError, TypeError):
        return None


def _stale(d: Path, sheet: str, stored: dict) -> bool:
    """The study no longer matches the sheet: a room, its parameters, the scale, the options or a luminaire of the catalogue changed since."""
    saved = layout.saved_drawing(d, sheet)
    if saved is None:
        return True
    now = _asked_now(saved, stored["input"]["options"], stored["input"]["lang"])
    return now is None or service.fingerprint(d, now) != stored["fingerprint"]


def view(d: Path, sheet: str) -> dict:
    """The study of the sheet with whether it is stale, or `{"exists": false}`."""
    stored = read_json(_path(d, sheet), None)
    if not stored:
        return {"exists": False}
    return {"exists": True, "sheet": sheet, "stale": _stale(d, sheet, stored), "report": report_path(d, sheet).is_file(), **{k: stored[k] for k in KEPT}}


def make_report(d: Path, sheet: str, lang: str) -> dict:
    """The report of the study as a PDF in the documents of the engineering workspace. A stale study has none: calculate it again first."""
    stored = read_json(_path(d, sheet), None)
    if not stored:
        raise NotFound("this sheet has no study")
    if _stale(d, sheet, stored):
        raise Conflict({"study": "the rooms or the luminaires changed since the study was made: calculate it again first"})
    luminaires = service.effective(d)
    used = {r.get("luminaire", "") for r in stored["input"]["rooms"].values()}
    names = {lid: service.label(luminaires[lid], lang) for lid in used if lid in luminaires}
    meta = projects.read_meta(d)
    doc = report.document(stored, {"code": meta.get("project_code", ""), "name": meta.get("project_name", "")}, lang, names,
                          any(luminaires.get(lid, {}).get("illustrative") for lid in used), service.engine_version())
    dst = report_path(d, sheet)
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        engine.render_report_pdf(doc, dst)
    except RuntimeError as exc:
        raise Failure(str(exc))
    identity.audit_event("lighting_report_made", target=f"{projects.project_id(d)}:{sheet}", org_slug=meta.get("org", ""), detail={"file": dst.name})
    return {"file": dst.name, "path": dst.relative_to(d).as_posix()}
