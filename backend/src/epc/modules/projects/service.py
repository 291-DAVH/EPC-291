"""Use cases of the projects module: create from the template, list, project tree for the admin console."""
from pathlib import Path
from typing import Dict, List

from epc.core import clock
from epc.core.config import settings
from epc.core.errors import Conflict, Failure, Invalid, NotFound
from epc.core.fsutil import SLUG, count_files, today
from epc.modules.identity import public as identity
from epc.modules.projects import repository
from epc.modules.projects.models import NewProject

PHASES = ["IC", "IB", "ID", "IE"]
LOCALES = ["es-AR", "es", "en"]


def get_dir(client: str, code: str) -> Path:
    if not (SLUG.match(client) and SLUG.match(code)) or client.startswith("_"):
        raise NotFound("project not found")
    d = repository.find(client, code)
    if d is None:
        raise NotFound("project not found")
    return d


def admin_view(d: Path) -> dict:
    return {"id": repository.project_id(d), "name": d.name, **repository.read_meta(d),
            "workspace_files": count_files(d / "workspace"), "deliverable_files": count_files(d / "deliverables"),
            "is_template": d.name == "_template"}


def admin_list() -> List[dict]:
    return [admin_view(d) for d in repository.project_dirs()]


def options() -> dict:
    return {"jurisdictions": repository.jurisdictions(), "methodologies": repository.methodologies(), "locales": LOCALES, "phases": PHASES}


def _validate(p: NewProject, opts: dict) -> dict:
    errors: Dict[str, str] = {}
    if not p.client_name.strip():
        errors["client_name"] = "required"
    msg = "letters, digits, '-' or '_' (max 48), must start with a letter or digit"
    if not SLUG.match(p.client_code):
        errors["client_code"] = msg
    if not SLUG.match(p.project_code):
        errors["project_code"] = msg
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
    if p.phase not in PHASES:
        errors["phase"] = "unknown phase"
    return errors


def create(p: NewProject) -> dict:
    opts = options()
    errors = _validate(p, opts)
    if errors:
        raise Invalid(errors)
    jur = next(j for j in opts["jurisdictions"] if j["id"] == p.jurisdiction)
    if not settings.template_dir.is_dir():
        raise Failure("project skeleton not found (management/templates/project-skeleton)")
    owner = identity.org_for_new_project(p.org)
    target = settings.projects_dir / p.client_code / p.project_code
    if target.exists():
        raise Conflict({"project_code": "a project with this client and code already exists"})
    try:
        repository.copy_template(target)
        created = clock.now_local()
        meta = {"schema_version": "1.0", "client": p.client_name.strip(), "client_code": p.client_code, "project_code": p.project_code,
                "project_name": p.project_name.strip(), "jurisdiction": p.jurisdiction, "locale": p.locale or jur["default_locale"],
                "methodology": p.methodology, "disciplines": p.disciplines, "phase": p.phase, "engine_min_version": "0.1.0", "created": created}
        if owner:
            meta["org"] = owner
        repository.write_meta(target, meta)
        repository.stamp_status(target, p.phase, today().isoformat())
        locked = repository.refresh_lock(target)
        repository.write_created_event(target, created, locked)
    except Exception as e:
        repository.remove_created(target)
        raise Failure(f"could not create project: {e}")
    return {**admin_view(target), "plugins_locked": locked}


def set_org(client: str, code: str, org: str) -> dict:
    """Staff: give a project to an organization (projects created before accounts existed have none and are visible only to staff)."""
    d = get_dir(client, code)
    if org and not identity.org_exists(org):
        raise Invalid({"org": "unknown organization"})
    meta = repository.read_meta(d)
    if org:
        meta["org"] = org
    else:
        meta.pop("org", None)
    repository.write_meta(d, meta)
    return admin_view(d)


def tree(project_id: str, area: str, depth: int, formats: dict) -> dict:
    root = (settings.projects_dir / project_id).resolve()
    base_dir = settings.projects_dir.resolve()
    if base_dir not in root.parents and root != base_dir:
        raise NotFound("bad path")
    parts = Path(project_id).parts
    if len(parts) != 2 or repository.find(parts[0], parts[1]) is None:                # only a project the caller may see
        raise NotFound("project not found")
    base = root / area
    if area not in ("workspace", "deliverables") or not base.exists():
        raise NotFound("area not found")

    def walk(d: Path, level: int):
        items = []
        for p in sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
            if p.name == ".gitkeep":
                continue
            if p.is_dir():
                items.append({"name": p.name, "type": "dir", "files": count_files(p), "children": walk(p, level + 1) if level < depth else []})
            else:
                ext = p.suffix.lstrip(".").lower()
                rule = formats.get(ext, {})
                items.append({"name": p.name, "type": "file", "ext": ext, "size": p.stat().st_size, "deliver": rule.get("deliver", False),
                              "role": rule.get("role", "internal")})
        return items

    return {"project": project_id, "area": area, "tree": walk(base, 1)}
