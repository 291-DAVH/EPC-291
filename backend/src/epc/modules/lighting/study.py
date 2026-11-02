"""The study of a sheet: the lighting calculation kept with the sheet, whether it is still good for the rooms as they are drawn now, and its report as a document of the project.

  <project>/workspace/02-engineering/layout/<sheet>/src/lighting.json            the study (what was asked, what came out, the fingerprint of both)
  <project>/workspace/02-engineering/electrical/PQ-01/docs/LIGHTING_<sheet>.md   its report, to read in the work environment; its PDF is made when a transmittal is issued
"""
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
from epc.modules.lighting import figures, report, service
from epc.modules.lighting.energy import energy_checks
from epc.modules.lighting.models import CalcIn, CalcOptions, PlanRoom, RoomParams, Sheet
from epc.modules.masterdata import public as masterdata
from epc.modules.projects import public as projects

FILE = "lighting.json"
DOCS = Path("workspace") / "02-engineering" / "electrical" / "PQ-01" / "docs"          # where the issuing flow looks for the documents of the engineering workspace
KEPT = ("saved_at", "saved_by", "fingerprint", "result", "placements", "rooms", "areas", "skipped", "warnings")
UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def _path(d: Path, sheet: str) -> Path:
    return layout.source_file(d, sheet, FILE)


def _who() -> str:
    user = identity.current_user()
    return user.get("email", "") or user.get("name", "")


def report_path(d: Path, sheet: str) -> Path:
    return d / DOCS / f"LIGHTING_{UNSAFE.sub('_', sheet)}.md"


def save(d: Path, sheet: str, body: CalcIn) -> dict:
    """Calculate and keep the study of a sheet (replacing the one it had). A request where no room could be calculated is not a study."""
    if layout.saved_drawing(d, sheet) is None:
        raise NotFound("sheet not found")
    out = service.calc(d, body)
    if out["result"] is None:
        raise Invalid({"study": "no room could be calculated: give each one a luminaire and an activity or a target"})
    stored = {"schema_version": "1.0", "sheet": sheet, "saved_at": clock.now_local(), "saved_by": _who(), "input": body.model_dump(exclude={"sheet": {"nodes"}}), **{k: out[k] for k in KEPT if k in out}}
    write_json(_path(d, sheet), stored)
    identity.audit_event("lighting_study_saved", target=f"{projects.project_id(d)}:{sheet}", org_slug=projects.read_meta(d).get("org", ""), detail={"rooms": len(out["result"]["rooms"])})
    made = _auto_report(d, sheet, body.lang)
    return {**view(d, sheet), **made}


def _auto_report(d: Path, sheet: str, lang: str) -> dict:
    """The report is made with the study: it is part of the engineering and has to be among its files (Engineering, Files) without anyone asking for it. A report that could not be made does not undo the study:
    the reason is given and the person can ask for it again."""
    try:
        return {"report_file": make_report(d, sheet, lang)["file"], "report_error": ""}
    except (Conflict, Failure, NotFound) as exc:
        return {"report_file": "", "report_error": str(getattr(exc, "detail", exc))}


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


OPTION_NUMBERS = ("power_limit_w_m2", "kwh_price", "hours_default")           # the options a sheet keeps in its lighting settings


def _settings_options(saved: dict) -> dict:
    """The calculation options the sheet itself says (limit of power density, tariff, hours, automatic luminaire): what the plan editor sends with every request."""
    s = saved.get("lighting_settings") or {}
    out = {k: s[k] for k in OPTION_NUMBERS if isinstance(s.get(k), (int, float)) and not isinstance(s.get(k), bool)}
    return {**out, "auto_luminaire": True} if s.get("auto_luminaire") else out


def remake(d: Path, sheet: str, lang: str) -> dict:
    """Calculate and keep the study of a sheet again from the drawing as it is saved (the rooms, what each says of its lighting and the options of the sheet), and make its report."""
    saved = layout.saved_drawing(d, sheet)
    if saved is None:
        raise NotFound("sheet not found")
    asked = _asked_now(saved, _settings_options(saved), lang)
    if asked is None:
        raise Invalid({"study": "the rooms of the sheet cannot be calculated: give each one an outline, a luminaire and an activity or a target"})
    return save(d, sheet, asked)


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


def _extras(d: Path, stored: dict, lang: str) -> dict:
    """What the report has besides the study: the title block of the project, the energy against what the person set and the plan of the sheet with the luminaires and the illuminance of its rooms (calculated again
    from what the study was made from, so the figures are the ones of the study)."""
    asked = CalcIn(**stored["input"])
    fresh = service.calc(d, asked.model_copy(update={"options": asked.options.model_copy(update={"map": True})}))
    t = report.TEXT["es" if lang == "es" else "en"]
    outlines = [{"id": r.id, "name": r.name, "points": r.points} for r in asked.sheet.rooms]
    return {"titleblock": masterdata.titleblock(d, "electrical"), "energy_checks": energy_checks(stored["result"], asked.options), "figure": figures.sheet_figure(outlines, fresh, t["figure"], t["scale"])}


def _report_document(d: Path, sheet: str, lang: str) -> dict:
    """The report of the study as a structured document (what the Markdown and the PDF are made from). A stale study has none: calculate it again first."""
    stored = read_json(_path(d, sheet), None)
    if not stored:
        raise NotFound("this sheet has no study")
    if _stale(d, sheet, stored):
        raise Conflict({"study": "the rooms or the luminaires changed since the study was made: calculate it again first"})
    luminaires = service.effective(d)
    used = {name for r in stored["input"]["rooms"].values() for name in (r.get("luminaire", ""), r.get("emergency_luminaire", ""))}
    names = {lid: service.label(luminaires[lid], lang) for lid in used if lid in luminaires}
    meta = projects.read_meta(d)
    return report.document(stored, {"code": meta.get("project_code", ""), "name": meta.get("project_name", "")}, lang, names,
                           any(luminaires.get(lid, {}).get("illustrative") for lid in used), service.engine_version(), _extras(d, stored, lang))


def make_report(d: Path, sheet: str, lang: str) -> dict:
    """The report of the study as a Markdown document in the engineering workspace (to read there; the PDF is made when it is issued)."""
    from epc_aea90364.board_memo import doc_markdown                       # the shared conversion of a structured document to Markdown
    meta = projects.read_meta(d)
    dst = report_path(d, sheet)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(doc_markdown(_report_document(d, sheet, lang)), encoding="utf-8", newline="\n")
    identity.audit_event("lighting_report_made", target=f"{projects.project_id(d)}:{sheet}", org_slug=meta.get("org", ""), detail={"file": dst.name})
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
            stem = f"LIGHTING_{UNSAFE.sub('_', item['sheet'])}"
            out.append({"id": f"electrical/PQ-01/docs/{stem}.pdf", "name": stem, "discipline": "electrical", "package": "PQ-01", "kind": "document", "files": {"pdf": _pdf_maker(d, item["sheet"], lang)}})
    return out


engineering.register_issuable(issuable)
