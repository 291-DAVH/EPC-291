"""EPC Platform API (read-mostly). Run from platform/:  uvicorn apps.api.main:app --reload --port 8000

Serves the hub registry, skills, the rules engine and the projects folder to the web app.
Environment: EPC_ENV (dev|production), EPC_DEV_KNOWLEDGE (drafts source, development only), EPC_PROJECTS.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

PLATFORM = Path(__file__).resolve().parents[2]
WORKSPACE = PLATFORM.parent
HUB, SKILLS = PLATFORM / "hub", PLATFORM / "skills"
PROJECTS = Path(os.environ.get("EPC_PROJECTS", WORKSPACE / "projects"))
DEV_KNOWLEDGE = Path(os.environ.get("EPC_DEV_KNOWLEDGE", WORKSPACE / "dev-knowledge"))
ENV = os.environ.get("EPC_ENV", "dev")
ROLE = os.environ.get("EPC_ROLE", "user")      # "admin" unlocks the technical console; end users never see internals

sys.path.insert(0, str(PLATFORM / "core" / "rules"))
from epc_rules import RuleSet  # noqa: E402

app = FastAPI(title="EPC Platform API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])


PUBLIC_PATHS = {"/api/health", "/api/me", "/api/projects/options"}


@app.middleware("http")
async def role_guard(request, call_next):
    """Only the admin role may call the technical endpoints. End users get the /api/app/* surface."""
    path = request.url.path
    if path.startswith("/api/") and globals()["ROLE"] != "admin":
        public = path in PUBLIC_PATHS or path.startswith("/api/app/") or (path == "/api/projects" and request.method == "POST")
        if not public:
            return JSONResponse({"detail": "forbidden"}, status_code=403)
    return await call_next(request)


@app.get("/api/me")
def me():
    return {"role": ROLE, "name": os.environ.get("EPC_USER", ""), "org": os.environ.get("EPC_ORG", "")}


def _json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def _rules() -> RuleSet:
    return RuleSet.load("AR", "electrical", env=ENV, include_drafts_from=DEV_KNOWLEDGE if ENV != "production" else None)


def _frontmatter(md: Path) -> Dict[str, str]:
    if not md.exists():
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", md.read_text(encoding="utf-8"), re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"')
    return out


def _rule_view(r: dict, full: bool = False) -> dict:
    v = {"id": r["id"], "standard": r["_standard"], "status": r["_status"], "clause": r["clause"], "part": r.get("part"),
         "page": r.get("page", {}).get("printed"), "topic": r["topic"], "title": r.get("title", ""), "type": r["type"],
         "summary": r.get("summary", {}), "has_check": bool(r.get("check")), "derived": bool(r.get("check", {}).get("derived")),
         "confidence": r.get("confidence"), "verification": r.get("verification"),
         "installation_types": r.get("applies_to", {}).get("installation_types", [])}
    if full:
        v.update(params=r.get("params", {}), check=r.get("check"), applies_to=r.get("applies_to", {}), table_ref=r.get("table_ref"))
    return v


@app.get("/api/health")
def health():
    return {"ok": True, "env": ENV}


@app.get("/api/overview")
def overview():
    rs = _rules()
    plugins = list(_plugins())
    conflicts = []
    try:
        out = subprocess.run([sys.executable, str(PLATFORM / "tools/ci/check_skill_conflicts.py"), "--json", "--env", "production"],
                             capture_output=True, text=True, timeout=30)
        conflicts = json.loads(out.stdout or "[]")
    except Exception:
        pass
    by_status: Dict[str, int] = {}
    for s in rs.standards.values():
        by_status[s["source_status"]] = by_status.get(s["source_status"], 0) + 1
    return {"env": ENV, "plugins": len(plugins), "plugins_pending": sum(1 for p in plugins if p["status"] != "active"),
            "skills": len(list(_skills())), "standards": len(rs.standards), "standards_by_status": by_status,
            "rules": len(rs.rules), "rules_with_check": sum(1 for r in rs.rules if r.get("check")),
            "derived_checks": sum(1 for r in rs.rules if r.get("check", {}).get("derived")),
            "projects": len(list(_projects())), "skill_conflicts": conflicts}


def _plugins():
    reg = _json(HUB / "registry.json") if (HUB / "registry.json").exists() else {"plugins": {}}
    dependents: Dict[str, List[str]] = {}
    manifests = {}
    for d in sorted(p for p in HUB.iterdir() if p.is_dir()):
        if (d / "plugin.json").exists():
            m = _json(d / "plugin.json")
            manifests[m["id"]] = m
            for dep in m.get("requires", {}):
                dependents.setdefault(dep, []).append(m["id"])
    for pid, m in manifests.items():
        yield {"id": pid, "version": m["version"], "kind": m["kind"], "status": m.get("status", "active"),
               "description": m.get("description", ""), "discipline": m.get("discipline", []), "requires": m.get("requires", {}),
               "required_by": dependents.get(pid, []), "skills": m.get("skills", []), "outputs": m.get("outputs", []),
               "entitlement": m.get("entitlement"), "python": m.get("python", {}).get("requires", []),
               "hash": reg["plugins"].get(pid, {}).get("hash")}


@app.get("/api/plugins")
def plugins():
    return list(_plugins())


@app.get("/api/plugins/{pid}")
def plugin(pid: str):
    for p in _plugins():
        if p["id"] == pid:
            readme = HUB / pid / "README.md"
            return {**p, "readme": readme.read_text(encoding="utf-8") if readme.exists() else ""}
    raise HTTPException(404, "plugin not found")


def _skills():
    reg = _json(SKILLS / "_registry.json") if (SKILLS / "_registry.json").exists() else {}
    owners = {}
    for p in _plugins():
        for s in p["skills"]:
            owners[s["id"]] = p["id"]
    for d in sorted(p for p in SKILLS.iterdir() if p.is_dir() and (p / "SKILL.md").exists()):
        fm = _frontmatter(d / "SKILL.md")
        yield {"id": d.name, "owner": owners.get(d.name), "description": fm.get("description", ""),
               "legacy_id": reg.get(d.name, {}).get("legacy_id"), "active": d.name in owners}


@app.get("/api/skills")
def skills():
    return list(_skills())


@app.get("/api/rules/standards")
def rule_standards():
    rs = _rules()
    out = []
    for sid, s in rs.standards.items():
        rules = [r for r in rs.rules if r["_standard"] == sid]
        out.append({"id": sid, "body": s.get("body"), "edition": s.get("edition"), "domain": s.get("domain"), "status": s["source_status"],
                    "validated_by": s.get("validated_by"), "rules": len(rules), "with_check": sum(1 for r in rules if r.get("check")),
                    "derived": sum(1 for r in rules if r.get("check", {}).get("derived")),
                    "low_confidence": sum(1 for r in rules if r.get("confidence") == "low")})
    return out


@app.get("/api/rules/topics")
def rule_topics():
    return sorted({r["topic"].split(".")[0] for r in _rules().rules})


@app.get("/api/rules")
def rules(standard: Optional[str] = None, topic: Optional[str] = None, q: Optional[str] = None, type: Optional[str] = None,
          installation: Optional[str] = None, only_checks: bool = False, limit: int = Query(300, le=1000)):
    rs = _rules()
    out = []
    for r in rs.query(topic=topic, standard=standard, installation_type=installation, type=type):
        if only_checks and not r.get("check"):
            continue
        if q:
            hay = " ".join([r["id"], r["clause"], r.get("title", ""), " ".join(r.get("summary", {}).values())]).lower()
            if q.lower() not in hay:
                continue
        out.append(_rule_view(r))
    return {"total": len(out), "items": out[:limit]}


@app.get("/api/rules/{rule_id}")
def rule(rule_id: str):
    r = _rules().get(rule_id)
    if not r:
        raise HTTPException(404, "rule not found")
    return _rule_view(r, full=True)


class CheckRequest(BaseModel):
    context: Dict[str, Any] = {}
    installation_type: Optional[str] = None
    topic: Optional[str] = None
    standard: Optional[str] = None


@app.post("/api/rules/check")
def check(req: CheckRequest):
    rep = _rules().check(req.context, installation_type=req.installation_type, topic=req.topic, standard=req.standard)
    return {"summary": rep.summary(), "findings": [f.__dict__ for f in rep.findings]}


def _count(d: Path) -> int:
    return sum(1 for f in d.rglob("*") if f.is_file() and f.name != ".gitkeep") if d.exists() else 0


def _projects():
    if not PROJECTS.exists():
        return
    for pj in sorted(PROJECTS.glob("*/.epc/project.json")) + sorted(PROJECTS.glob("*/*/.epc/project.json")):
        root = pj.parent.parent
        meta = _json(pj)
        yield {"id": str(root.relative_to(PROJECTS)).replace("\\", "/"), "name": root.name, **meta,
               "workspace_files": _count(root / "workspace"), "deliverable_files": _count(root / "deliverables"),
               "is_template": root.name == "_template"}


@app.get("/api/projects")
def projects():
    return list(_projects())


SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$")


def _load_build():
    import importlib.util
    spec = importlib.util.spec_from_file_location("epc_build", PLATFORM / "tools" / "build" / "epc_build.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _options() -> dict:
    juris, methods = [], []
    for d in sorted((PLATFORM / "jurisdictions").iterdir()):
        jf = d / "jurisdiction.json"
        if d.is_dir() and not d.name.startswith("_") and jf.exists():
            j = _json(jf)
            juris.append({"id": d.name, "name": j.get("name", d.name), "default_locale": j.get("default_locale", "es"),
                          "status": j.get("status", "active"),
                          "disciplines": sorted(x.name for x in d.iterdir() if x.is_dir() and not x.name.startswith("_"))})
    for d in sorted((PLATFORM / "methodologies").iterdir()):
        if d.is_dir():
            mf = d / "methodology.json"
            m = _json(mf) if mf.exists() else {}
            methods.append({"id": d.name, "name": m.get("name", d.name), "available": mf.exists(), "default": bool(m.get("default"))})
    return {"jurisdictions": juris, "methodologies": methods, "locales": ["es-AR", "es", "en"], "phases": ["IC", "IB", "ID", "IE"]}


@app.get("/api/projects/options")
def project_options():
    return _options()


class NewProject(BaseModel):
    client_name: str
    client_code: str
    project_code: str
    project_name: str = ""
    jurisdiction: str = "AR"
    methodology: str = "pm2"
    locale: Optional[str] = None
    disciplines: List[str] = ["electrical"]
    phase: str = "IC"


@app.post("/api/projects", status_code=201)
def create_project(p: NewProject):
    import datetime
    import shutil
    opts = _options()
    errors = {}
    if not p.client_name.strip():
        errors["client_name"] = "required"
    if not SLUG.match(p.client_code):
        errors["client_code"] = "letters, digits, '-' or '_' (max 48), must start with a letter or digit"
    if not SLUG.match(p.project_code):
        errors["project_code"] = "letters, digits, '-' or '_' (max 48), must start with a letter or digit"
    if p.client_code.startswith("_") or p.project_code.startswith("_"):
        errors["client_code"] = errors.get("client_code", "names starting with '_' are reserved")
    jur = next((j for j in opts["jurisdictions"] if j["id"] == p.jurisdiction), None)
    if not jur:
        errors["jurisdiction"] = "unknown jurisdiction"
    meth = next((m for m in opts["methodologies"] if m["id"] == p.methodology), None)
    if not meth:
        errors["methodology"] = "unknown methodology"
    elif not meth["available"]:
        errors["methodology"] = "not available yet"
    if jur and (not p.disciplines or any(d not in jur["disciplines"] for d in p.disciplines)):
        errors["disciplines"] = "choose at least one discipline of the jurisdiction"
    if p.phase not in opts["phases"]:
        errors["phase"] = "unknown phase"
    if errors:
        raise HTTPException(422, {"errors": errors})

    template = PROJECTS / "_template"
    target = PROJECTS / p.client_code / p.project_code
    if not template.is_dir():
        raise HTTPException(500, "projects/_template not found")
    if target.exists():
        raise HTTPException(409, {"errors": {"project_code": "a project with this client and code already exists"}})
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copytree(template, target, ignore=shutil.ignore_patterns("plugins.lock", "project.json"))
        meta = {"schema_version": "1.0", "client": p.client_name.strip(), "client_code": p.client_code, "project_code": p.project_code,
                "project_name": p.project_name.strip(), "jurisdiction": p.jurisdiction, "locale": p.locale or jur["default_locale"],
                "methodology": p.methodology, "disciplines": p.disciplines, "phase": p.phase, "engine_min_version": "0.1.0",
                "created": datetime.datetime.now().isoformat(timespec="seconds")}
        epc = target / ".epc"
        epc.mkdir(exist_ok=True)
        (epc / "project.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        st_file = target / "workspace" / "05-management" / "project-status.json"
        if st_file.exists():
            st = json.loads(st_file.read_text(encoding="utf-8"))
            st.update(phase=p.phase, start=datetime.date.today().isoformat(), updated=datetime.date.today().isoformat())
            st_file.write_text(json.dumps(st, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        build = _load_build()
        build.cmd_registry()                 # refresh hub/registry.json so the lock matches the current hub
        build.cmd_lock(str(target))
        lock = json.loads((epc / "plugins.lock").read_text(encoding="utf-8"))
        (epc / "ledger").mkdir(exist_ok=True)
        (epc / "ledger" / "0001_created.json").write_text(json.dumps(
            {"event": "project_created", "at": meta["created"], "plugins": len(lock["plugins"])}, indent=2) + "\n", encoding="utf-8")
    except Exception as e:
        if target.exists() and PROJECTS.resolve() in target.resolve().parents:
            shutil.rmtree(target, ignore_errors=True)       # remove only the folder created by this request
        raise HTTPException(500, f"could not create project: {e}")
    return next(x for x in _projects() if x["id"] == f"{p.client_code}/{p.project_code}") | {"plugins_locked": len(lock["plugins"])}


@app.get("/api/policy")
def policy():
    return _json(PLATFORM / "schemas" / "deliverable-policy.json")


@app.get("/api/projects/{project_id:path}/tree")
def project_tree(project_id: str, area: str = "workspace", depth: int = 3):
    root = (PROJECTS / project_id).resolve()
    if PROJECTS.resolve() not in root.parents and root != PROJECTS.resolve():
        raise HTTPException(400, "bad path")
    base = root / area
    if area not in ("workspace", "deliverables") or not base.exists():
        raise HTTPException(404, "area not found")
    fmt = _json(PLATFORM / "schemas" / "deliverable-policy.json")["formats"]

    def walk(d: Path, level: int):
        items = []
        for p in sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if p.name == ".gitkeep":
                continue
            if p.is_dir():
                items.append({"name": p.name, "type": "dir", "files": _count(p), "children": walk(p, level + 1) if level < depth else []})
            else:
                ext = p.suffix.lstrip(".").lower()
                rule_ = fmt.get(ext, {})
                items.append({"name": p.name, "type": "file", "ext": ext, "size": p.stat().st_size, "deliver": rule_.get("deliver", False),
                              "role": rule_.get("role", "internal")})
        return items

    return {"project": project_id, "area": area, "tree": walk(base, 1)}


from apps.api import app_routes  # noqa: E402  (registered last so it can import this module)

app.include_router(app_routes.router)
