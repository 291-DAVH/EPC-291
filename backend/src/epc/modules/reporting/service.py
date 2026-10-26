"""Management reports of the project's methodology (PM²: D11 status, D12 progress, D13 risks, D14 effort, D15 changes).

The catalog of report types comes from the methodology pack (`management/methodologies/<id>/reports.json`); each report is built from the project's own data
(status and milestones, WBS, schedule, backlog, deliverables, requirements and the PM² registers) in the structure of the methodology's template, saved as Markdown and PDF in
`workspace/05-management/<folder>/` and kept internal until the engineer publishes it to the client (it then appears in the client's Reports list).
"""
import datetime as dt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from epc.core.errors import Conflict, Failure, Invalid, NotFound
from epc.core.fsutil import safe_file, today
from epc.core import lang as lang_mod
from epc.modules.backlog import public as backlog
from epc.modules.deliverables import public as deliverables
from epc.modules.identity import public as identity
from epc.modules.intake import public as intake
from epc.modules.management import public as management
from epc.modules.projects import public as projects
from epc.modules.registers import public as registers
from epc.modules.reporting import builders, repository
from epc.modules.reporting.models import GenerateIn
from epc.modules.requirements import public as requirements
from epc.modules.schedule import public as schedule
from epc.modules.wbs import public as wbs



def _lang(meta: dict, lang: Optional[str]) -> str:
    return lang_mod.pick(lang, meta.get("locale"))


def _catalog(meta: dict) -> dict:
    cat = repository.catalog(meta.get("methodology") or "pm2")
    if not cat:
        raise Conflict({"methodology": "this methodology has no report catalog"})
    return cat


def _type(cat: dict, type_id: str) -> dict:
    t = next((x for x in cat["types"] if x["id"] == type_id), None)
    if not t:
        raise Invalid({"type": "one of " + ", ".join(x["id"] for x in cat["types"])})
    return t


def _date(s: Optional[str], field: str) -> Optional[dt.date]:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        raise Invalid({field: "ISO date, e.g. 2026-10-23"})


def _of_type(items: List[dict], type_id: str) -> List[dict]:
    return sorted((r for r in items if r["type"] == type_id), key=lambda r: r["nn"])


def overview(d: Path, lang: Optional[str] = None) -> dict:
    meta = projects.read_meta(d)
    lg = _lang(meta, lang)
    items = repository.generated(d)
    cat = repository.catalog(meta.get("methodology") or "pm2")
    if not cat:                                                     # a methodology without a report catalog: say so, keep the reports already generated
        return {"methodology": meta.get("methodology") or "pm2", "available": False, "language": lg, "types": [], "reports": sorted(items, key=lambda r: (r["date"], r["id"]), reverse=True)}
    types = []
    for t in cat["types"]:
        prev = _of_type(items, t["id"])
        types.append({"id": t["id"], "code": t["code"], "name": t["name"].get(lg) or t["name"]["es"], "audience": t["audience"], "command": t["command"],
                      "next_number": (prev[-1]["nn"] + 1) if prev else 1, "last_period_end": prev[-1]["period"][1] if prev else None})
    return {"methodology": cat["methodology"], "available": True, "language": lg, "types": types, "reports": sorted(items, key=lambda r: (r["date"], r["id"]), reverse=True)}


def _context(d: Path, meta: dict, lg: str, nn: int, ps: dt.date, pe: dt.date) -> dict:
    who = identity.current_user()
    return {"meta": meta, "lang": lg, "status": projects.read_status(d), "project_name": meta.get("project_name") or meta.get("project_code") or d.name,
            "wbs": wbs.view(d), "schedule": schedule.view(d), "backlog": backlog.view(d), "deliverables": deliverables.list_items(d),
            "requirements": requirements.list_requirements(d), "inputs": intake.input_counts(d),
            "rfc": registers.items(d, "change"), "risks": registers.items(d, "risk"), "issues": registers.items(d, "issue"), "stakeholders": registers.items(d, "stakeholder"),
            "closed": {k: registers.closed_states(d, k) for k in ("change", "risk", "issue")}, "label": registers.labeler(d, lg),
            "period_start": ps, "period_end": pe, "today": today(), "nn": nn, "prepared_by": who.get("name") or who.get("email") or "-"}


def generate(d: Path, body: GenerateIn) -> dict:
    meta = projects.read_meta(d)
    cat = _catalog(meta)
    t = _type(cat, body.type)
    lg = _lang(meta, body.lang)
    items = repository.generated(d)
    prev = _of_type(items, t["id"])
    nn = (prev[-1]["nn"] + 1) if prev else 1
    pe = _date(body.period_end, "period_end") or today()
    ps = _date(body.period_start, "period_start")
    if ps is None:
        last_end = _date(prev[-1]["period"][1], "period") if prev else None
        start = _date(projects.read_status(d).get("start"), "start") if not last_end else None
        ps = min(last_end + dt.timedelta(days=1), pe) if last_end else (start if start and start <= pe else pe - dt.timedelta(days=30))
    if ps > pe:
        raise Invalid({"period_start": "must not be after the end of the period"})
    ctx = _context(d, meta, lg, nn, ps, pe)
    doc = builders.BUILDERS[t["id"]](ctx, prev[-1].get("snapshot") if prev else None)
    rid = f"{t['prefix'].upper()}-{nn:02d}"
    doc["subtitle"] = rid
    stem = f"{t['prefix']}-{nn:02d}_{today().strftime('%Y%m%d')}"
    folder = repository.mgmt(d) / t["folder"]
    name = t["name"].get(lg) or t["name"]["es"]
    pdf_doc = {"title": doc["title"], "subtitle": rid, "blocks": doc["blocks"], "footer": builders.T[lg]["footer"].format(name=name, tr=rid, project=meta.get("project_code") or d.name),
               "page_label": builders.T[lg]["page"]}
    written: List[Path] = []
    try:
        repository.write_text(folder / f"{stem}.md", builders.to_markdown(doc))
        written.append(folder / f"{stem}.md")
        repository.render_pdf(pdf_doc, folder / f"{stem}.pdf")
        written.append(folder / f"{stem}.pdf")
    except Exception as exc:
        for f in written:
            f.unlink(missing_ok=True)
        raise Failure(f"could not generate the report: {exc}")
    base = d
    rec = {"id": rid, "type": t["id"], "code": t["code"], "nn": nn, "name": name, "audience": t["audience"], "date": today().isoformat(),
           "period": [ps.isoformat(), pe.isoformat()], "language": lg, "prepared_by": ctx["prepared_by"], "summary": doc["summary"],
           "md": (folder / f"{stem}.md").relative_to(base).as_posix(), "pdf": (folder / f"{stem}.pdf").relative_to(base).as_posix(),
           "snapshot": doc["snapshot"], "published": None}
    repository.save_generated(d, items + [rec])
    return rec


def _record(d: Path, rid: str) -> dict:
    rec = next((r for r in repository.generated(d) if r["id"] == rid), None)
    if not rec:
        raise NotFound("report not found")
    return rec


def file_for(d: Path, rid: str, fmt: str) -> Tuple[Path, str]:
    rec = _record(d, rid)
    if fmt not in ("pdf", "md"):
        raise Invalid({"format": "pdf or md"})
    rel = rec[fmt]
    return safe_file(d, rel), Path(rel).name


def publish(d: Path, rid: str) -> dict:
    items = repository.generated(d)
    rec = next((r for r in items if r["id"] == rid), None)
    if not rec:
        raise NotFound("report not found")
    if rec.get("published"):
        raise Conflict({"published": f"already published as {rec['published']}"})
    cat = _catalog(projects.read_meta(d))
    kind = _type(cat, rec["type"])["kind_label"]
    pdf = safe_file(d, rec["pdf"])
    item = management.publish_report(d, pdf, f"{rec['name']} {rec['nn']:02d}", kind, rec["date"], rec["summary"])
    rec["published"] = item["id"]
    repository.save_generated(d, items)
    return rec
