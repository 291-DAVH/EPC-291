"""The study of a sheet: the receptacles calculation kept with the sheet, whether it is still good for the rooms as they are drawn now, and its report as a document of the project.

  <project>/workspace/02-engineering/layout/<sheet>/src/receptacles.json            the study (what was asked, what came out, the fingerprint of both)
  <project>/workspace/02-engineering/electrical/PQ-01/docs/RECEPTACLES_<sheet>.md   its report, to read in the work environment; its PDF is made when a transmittal is issued
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from epc.core import clock, engine
from epc.core.errors import Conflict, Failure, Invalid, NotFound
from epc.core.fsutil import read_json, write_json
from epc.modules.engineering import public as engineering
from epc.modules.identity import public as identity
from epc.modules.layout import public as layout
from epc.modules.lighting import public as lighting
from epc.modules.masterdata import public as masterdata
from epc.modules.projects import public as projects
from epc.modules.receptacles import report, service
from epc.modules.receptacles.models import CalcIn, CalcOptions, RoomParams, Sheet

FILE = "receptacles.json"
DOCS = Path("workspace") / "02-engineering" / "electrical" / "PQ-01" / "docs"          # where the issuing flow looks for the documents of the engineering workspace
KEPT = ("saved_at", "saved_by", "fingerprint", "result", "placements", "skipped", "warnings")
UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _path(d: Path, sheet: str) -> Path:
    return layout.source_file(d, sheet, FILE)


def report_path(d: Path, sheet: str) -> Path:
    return d / DOCS / f"RECEPTACLES_{UNSAFE.sub('_', sheet)}.md"


def fingerprint(d: Path, body: CalcIn) -> str:
    """What a calculation was made from: the rooms, what each says, the options and the outlets of the catalogue. A later change of any of them makes the study stale."""
    seen = {"sheet": body.sheet.model_dump(exclude={"nodes"}), "rooms": {k: v.model_dump() for k, v in sorted(body.rooms.items())}, "options": body.options.model_dump(),
            "outlets": {rid: e for rid, e in sorted(service.effective(d).items()) if rid in {p.receptacle for p in body.rooms.values() if p.receptacle}}}
    return hashlib.sha256(json.dumps(seen, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def save(d: Path, sheet: str, body: CalcIn) -> dict:
    """Calculate and keep the study of a sheet (replacing the one it had). A request where no room could be calculated is not a study."""
    if layout.saved_drawing(d, sheet) is None:
        raise NotFound("sheet not found")
    out = service.calc(d, body)
    if out["result"] is None:
        raise Invalid({"study": "no room could be calculated: give each one its use"})
    stored = {"schema_version": "1.0", "sheet": sheet, "saved_at": clock.now_local(), "saved_by": _who(), "fingerprint": fingerprint(d, body), "input": body.model_dump(exclude={"sheet": {"nodes"}}),
              **{k: out[k] for k in KEPT if k in out and k not in ("saved_at", "saved_by", "fingerprint")}}
    write_json(_path(d, sheet), stored)
    identity.audit_event("receptacles_study_saved", target=f"{projects.project_id(d)}:{sheet}", org_slug=projects.read_meta(d).get("org", ""), detail={"rooms": len(out["result"]["rooms"])})
    made = _auto_report(d, sheet, body.lang)                          # the report first: the view says whether there is one
    return {**view(d, sheet), **made}


def _who() -> str:
    user = identity.current_user()
    return user.get("email", "") or user.get("name", "")


def _auto_report(d: Path, sheet: str, lang: str) -> dict:
    """The report is made with the study: it is part of the engineering and has to be among its files without anyone asking for it. A report that could not be made does not undo the study."""
    try:
        return {"report_file": make_report(d, sheet, lang)["file"], "report_error": ""}
    except (Conflict, Failure, NotFound) as exc:
        return {"report_file": "", "report_error": str(getattr(exc, "detail", exc))}


def _asked_now(saved: dict, options: dict, lang: str) -> Optional[CalcIn]:
    """The request the sheet would make today, from the drawing as it is saved (None when what it says is not a valid request)."""
    known = set(RoomParams.model_fields)
    rooms = saved.get("rooms") or []
    try:
        return CalcIn(sheet=Sheet(scale=saved.get("scale"), rooms=[lighting.models.PlanRoom(id=r["id"], name=r.get("name", ""), points=r["points"]) for r in rooms]),
                      rooms={r["id"]: RoomParams(**{k: v for k, v in r["receptacles"].items() if k in known}) for r in rooms if r.get("receptacles")}, options=CalcOptions(**options), lang=lang)
    except (ValidationError, KeyError, TypeError):
        return None


def remake(d: Path, sheet: str, lang: str) -> dict:
    """Calculate and keep the study of a sheet again from the drawing as it is saved (the rooms and what each says of its outlets), and make its report."""
    saved = layout.saved_drawing(d, sheet)
    if saved is None:
        raise NotFound("sheet not found")
    asked = _asked_now(saved, {}, lang)
    if asked is None:
        raise Invalid({"study": "the rooms of the sheet cannot be calculated: give each one an outline and its use"})
    return save(d, sheet, asked)


def _stale(d: Path, sheet: str, stored: dict) -> bool:
    """The study no longer matches the sheet: a room, what it says, the scale or an outlet of the catalogue changed since."""
    saved = layout.saved_drawing(d, sheet)
    if saved is None:
        return True
    now = _asked_now(saved, stored["input"]["options"], stored["input"]["lang"])
    return now is None or fingerprint(d, now) != stored["fingerprint"]


def view(d: Path, sheet: str) -> dict:
    """The study of the sheet with whether it is stale, or `{"exists": false}`."""
    stored = read_json(_path(d, sheet), None)
    if not stored:
        return {"exists": False}
    return {"exists": True, "sheet": sheet, "stale": _stale(d, sheet, stored), "report": report_path(d, sheet).is_file(), **{k: stored[k] for k in KEPT}}


def _report_document(d: Path, sheet: str, lang: str) -> dict:
    """The report of the study as a structured document (what the Markdown and the PDF are made from). A stale study has none: calculate it again first."""
    from epc_receptacles import config
    stored = read_json(_path(d, sheet), None)
    if not stored:
        raise NotFound("this sheet has no study")
    if _stale(d, sheet, stored):
        raise Conflict({"study": "the rooms or the outlets changed since the study was made: calculate it again first"})
    outlets = service.effective(d)
    names = {rid: service._pick(e.get("name"), lang) or rid for rid, e in outlets.items()}
    uses = {uid: service._pick(u["label"], lang) for uid, u in config.data("uses")["uses"].items()}
    meta = projects.read_meta(d)
    return report.document(stored, {"code": meta.get("project_code", ""), "name": meta.get("project_name", "")}, lang, names, uses, service._engine()[0].__version__, masterdata.titleblock(d, "electrical"))


def make_report(d: Path, sheet: str, lang: str) -> dict:
    """The report of the study as a Markdown document in the engineering workspace (to read there; the PDF is made when it is issued)."""
    from epc_aea90364.board_memo import doc_markdown                       # the shared conversion of a structured document to Markdown
    dst = report_path(d, sheet)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(doc_markdown(_report_document(d, sheet, lang)), encoding="utf-8", newline="\n")
    identity.audit_event("receptacles_report_made", target=f"{projects.project_id(d)}:{sheet}", org_slug=projects.read_meta(d).get("org", ""), detail={"file": dst.name})
    return {"file": dst.name, "path": dst.relative_to(d).as_posix()}


def _pdf_maker(d: Path, sheet: str, lang: str):
    def make(dst: Path) -> None:
        try:
            engine.render_report_pdf(_report_document(d, sheet, lang), dst)
        except RuntimeError as exc:
            raise Failure(str(exc))
    return make


def issuable(d: Path) -> list:
    """The studies still good for their sheet, offered to be issued: the PDF of each report is made when the transmittal is issued."""
    lang = "es" if str(projects.read_meta(d).get("locale", "")).startswith("es") else "en"
    out = []
    for item in layout.sheets(d):
        stored = read_json(_path(d, item["sheet"]), None)
        if stored and not _stale(d, item["sheet"], stored):
            stem = f"RECEPTACLES_{UNSAFE.sub('_', item['sheet'])}"
            out.append({"id": f"electrical/PQ-01/docs/{stem}.pdf", "name": stem, "discipline": "electrical", "package": "PQ-01", "kind": "document", "files": {"pdf": _pdf_maker(d, item["sheet"], lang)}})
    return out


engineering.register_issuable(issuable)
