"""End-user API (/api/app/*): projects, deliverables, input data, requirements and reports.

Only user-facing data is exposed here. Internals (plugins, rules, workflow, workspace file trees) are
available only to the admin role through the other /api endpoints.
"""
import datetime as dt
import json
import re
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/app")

SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$")
KINDS = {"voice_of_customer", "user_story", "document", "meeting_note", "report"}
ALLOWED_EXT = {".pdf", ".docx", ".xlsx", ".csv", ".txt", ".md", ".png", ".jpg", ".jpeg", ".dxf", ".dwg", ".eml", ".msg", ".pptx"}
MAX_FILE = 25 * 1024 * 1024
HEALTH_ORDER = {"delayed": 0, "at_risk": 1, "on_track": 2}


def _M():
    from apps.api import main
    return main


def _read(p: Path, default):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def _pdir(client: str, code: str) -> Path:
    if not (SLUG.match(client) and SLUG.match(code)) or client.startswith("_"):
        raise HTTPException(404, "project not found")
    d = _M().PROJECTS / client / code
    if not (d / ".epc" / "project.json").exists():
        raise HTTPException(404, "project not found")
    return d


def _today() -> dt.date:
    return dt.date.today()


def _summary(d: Path) -> dict:
    meta = _read(d / ".epc" / "project.json", {})
    ws = d / "workspace"
    st = _read(ws / "05-management" / "project-status.json", {})
    dels = _read(ws / "05-management" / "deliverables.json", [])
    intake = [_read(f, {}) for f in sorted((ws / "01-input" / "intake").glob("INT-*.json"))]
    today = _today().isoformat()
    overdue = sum(1 for x in dels if x.get("status") != "delivered" and x.get("due") and x["due"] < today)
    return {
        "id": f"{d.parent.name}/{d.name}", "name": meta.get("project_name") or meta.get("project_code") or d.name,
        "client": meta.get("client", d.parent.name), "code": meta.get("project_code", d.name), "disciplines": meta.get("disciplines", []),
        "methodology": meta.get("methodology"), "state": st.get("state", "active"), "phase": st.get("phase") or meta.get("phase"),
        "progress": st.get("progress_pct", 0), "health": st.get("health", "on_track"), "manager": st.get("manager", ""),
        "location": st.get("location", ""), "start": st.get("start"), "due": st.get("due"), "next_milestone": st.get("next_milestone"),
        "updated": st.get("updated"), "created": meta.get("created"),
        "deliverables": {"total": len(dels), "delivered": sum(1 for x in dels if x.get("status") == "delivered"), "overdue": overdue},
        "inputs": {"total": len(intake), "open": sum(1 for x in intake if x.get("status") in ("received", "analyzing"))},
    }


def _all():
    root = _M().PROJECTS
    if not root.exists():
        return []
    out = []
    for pj in sorted(root.glob("*/*/.epc/project.json")):
        if pj.parent.parent.parent.name.startswith("_"):
            continue
        out.append(_summary(pj.parent.parent))
    return out


@router.get("/portfolio")
def portfolio():
    ps = _all()
    active = [p for p in ps if p["state"] == "active"]
    today = _today()
    soon = (today + dt.timedelta(days=14)).isoformat()
    due_soon = 0
    for p in active:
        for x in _read(_M().PROJECTS / p["id"] / "workspace" / "05-management" / "deliverables.json", []):
            if x.get("status") != "delivered" and x.get("due") and x["due"] <= soon:
                due_soon += 1
    kpis = {
        "total": len(ps), "active": len(active), "closed": len(ps) - len(active),
        "on_track": sum(1 for p in active if p["health"] == "on_track"), "at_risk": sum(1 for p in active if p["health"] == "at_risk"),
        "delayed": sum(1 for p in active if p["health"] == "delayed"),
        "deliverables_delivered": sum(p["deliverables"]["delivered"] for p in ps), "deliverables_total": sum(p["deliverables"]["total"] for p in ps),
        "deliverables_due_soon": due_soon, "inputs_open": sum(p["inputs"]["open"] for p in active),
    }
    ps.sort(key=lambda p: (p["state"] != "active", HEALTH_ORDER.get(p["health"], 3), p["due"] or "9999"))
    return {"kpis": kpis, "projects": ps, "today": today.isoformat()}


@router.get("/projects/{client}/{code}")
def project(client: str, code: str):
    d = _pdir(client, code)
    s = _summary(d)
    st = _read(d / "workspace" / "05-management" / "project-status.json", {})
    s["milestones"] = st.get("milestones", [])
    s["requirements_count"] = len(_read(d / "workspace" / "00-setup" / "requirements.json", []))
    return s


@router.get("/projects/{client}/{code}/deliverables")
def deliverables(client: str, code: str):
    d = _pdir(client, code)
    today = _today().isoformat()
    items = _read(d / "workspace" / "05-management" / "deliverables.json", [])
    out = []
    for x in items:
        f = x.get("file")
        out.append({**x, "downloadable": bool(f and _inside(d / "deliverables", f)),
                    "overdue": x.get("status") != "delivered" and bool(x.get("due")) and x["due"] < today})
    return out


def _inside(base: Path, rel: str) -> bool:
    try:
        p = (base / rel).resolve()
        return base.resolve() in p.parents and p.is_file()
    except OSError:
        return False


def _safe_file(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if base.resolve() not in p.parents or not p.is_file():
        raise HTTPException(404, "file not found")
    return p


@router.get("/projects/{client}/{code}/deliverables/{item_id}/download")
def download_deliverable(client: str, code: str, item_id: str):
    d = _pdir(client, code)
    it = next((x for x in _read(d / "workspace" / "05-management" / "deliverables.json", []) if x.get("id") == item_id), None)
    if not it or not it.get("file"):
        raise HTTPException(404, "file not found")
    p = _safe_file(d / "deliverables", it["file"])
    return FileResponse(p, filename=f"{it.get('code', item_id)}.{it.get('format', p.suffix.lstrip('.'))}")


@router.get("/projects/{client}/{code}/inputs")
def inputs(client: str, code: str):
    d = _pdir(client, code)
    items = [_read(f, {}) for f in sorted((d / "workspace" / "01-input" / "intake").glob("INT-*.json"))]
    return sorted(items, key=lambda x: x.get("created", ""), reverse=True)


def _clean_name(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name).strip("._") or "file"
    return base[:96]


@router.post("/projects/{client}/{code}/inputs", status_code=201)
async def add_input(client: str, code: str, kind: str = Form(...), title: str = Form(...), text: str = Form(""),
                    source: str = Form(""), files: Optional[List[UploadFile]] = File(None)):
    d = _pdir(client, code)
    files = [f for f in (files or []) if f.filename]
    errors = {}
    if kind not in KINDS:
        errors["kind"] = "invalid"
    if not title.strip():
        errors["title"] = "required"
    if not text.strip() and not files:
        errors["text"] = "write something or attach a file"
    if len(files) > 10:
        errors["files"] = "at most 10 files"
    for f in files:
        if Path(f.filename).suffix.lower() not in ALLOWED_EXT:
            errors["files"] = f"file type not allowed: {Path(f.filename).suffix or f.filename}"
    if errors:
        raise HTTPException(422, {"errors": errors})
    idir = d / "workspace" / "01-input" / "intake"
    idir.mkdir(parents=True, exist_ok=True)
    nums = [int(m.group(1)) for f in idir.glob("INT-*.json") if (m := re.match(r"INT-(\d+)", f.name))]
    iid = f"INT-{(max(nums) + 1) if nums else 1:04d}"
    saved = []
    for f in files:
        data = await f.read()
        if len(data) > MAX_FILE:
            raise HTTPException(413, {"errors": {"files": f"{f.filename} is larger than 25 MB"}})
        target = idir / "files" / iid
        target.mkdir(parents=True, exist_ok=True)
        name = _clean_name(f.filename)
        (target / name).write_bytes(data)
        saved.append({"name": name, "size": len(data)})
    rec = {"id": iid, "kind": kind, "title": title.strip(), "text": text.strip(), "source": source.strip() or "Formulario web",
           "author": "", "created": _today().isoformat(), "status": "received", "attachments": saved}
    (idir / f"{iid}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rec


@router.get("/projects/{client}/{code}/requirements")
def requirements(client: str, code: str):
    d = _pdir(client, code)
    reqs = _read(d / "workspace" / "00-setup" / "requirements.json", [])
    titles = {r["id"]: r.get("title", "") for r in (_read(f, {}) for f in (d / "workspace" / "01-input" / "intake").glob("INT-*.json")) if r}
    return [{**r, "source_titles": [titles.get(i, i) for i in r.get("source_intake", [])]} for r in reqs]


@router.get("/projects/{client}/{code}/reports")
def reports(client: str, code: str):
    d = _pdir(client, code)
    items = _read(d / "workspace" / "05-management" / "reports" / "index.json", [])
    items = [{**x, "downloadable": bool(x.get("file") and _inside(d / "deliverables", x["file"]))} for x in items]
    return sorted(items, key=lambda x: x.get("date", ""), reverse=True)


@router.get("/projects/{client}/{code}/reports/{rid}/download")
def download_report(client: str, code: str, rid: str):
    d = _pdir(client, code)
    it = next((x for x in _read(d / "workspace" / "05-management" / "reports" / "index.json", []) if x.get("id") == rid), None)
    if not it or not it.get("file"):
        raise HTTPException(404, "file not found")
    return FileResponse(_safe_file(d / "deliverables", it["file"]), filename=f"{rid}.pdf")
