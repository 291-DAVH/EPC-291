"""File-system access for projects: <projects_dir>/<client>/<code>/{.epc, workspace, deliverables}."""
import importlib.util
import shutil
from pathlib import Path
from typing import List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json


def project_dirs() -> List[Path]:
    root = settings.projects_dir
    if not root.exists():
        return []
    return [pj.parent.parent for pj in sorted(root.glob("*/*/.epc/project.json")) if not pj.parent.parent.parent.name.startswith("_")]


def project_id(d: Path) -> str:
    return f"{d.parent.name}/{d.name}"


def find(client: str, code: str) -> Optional[Path]:
    d = settings.projects_dir / client / code
    return d if (d / ".epc" / "project.json").exists() else None


def read_meta(d: Path) -> dict:
    return read_json(d / ".epc" / "project.json", {})


def status_file(d: Path) -> Path:
    return d / "workspace" / "05-management" / "project-status.json"


def read_status(d: Path) -> dict:
    return read_json(status_file(d), {})


def jurisdictions() -> List[dict]:
    out = []
    base = settings.engine / "jurisdictions"
    for d in sorted(base.iterdir()) if base.exists() else []:
        jf = d / "jurisdiction.json"
        if d.is_dir() and not d.name.startswith("_") and jf.exists():
            j = read_json(jf, {})
            out.append({"id": d.name, "name": j.get("name", d.name), "default_locale": j.get("default_locale", "es"),
                        "status": j.get("status", "active"),
                        "disciplines": sorted(x.name for x in d.iterdir() if x.is_dir() and not x.name.startswith("_"))})
    return out


def methodologies() -> List[dict]:
    out = []
    base = settings.methodologies_dir
    for d in sorted(base.iterdir()) if base.exists() else []:
        if d.is_dir():
            mf = d / "methodology.json"
            m = read_json(mf, {}) if mf.exists() else {}
            out.append({"id": d.name, "name": m.get("name", d.name), "available": mf.exists(), "default": bool(m.get("default"))})
    return out


def copy_template(target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(settings.template_dir, target, ignore=shutil.ignore_patterns("plugins.lock", "project.json"))


def write_meta(target: Path, meta: dict) -> None:
    write_json(target / ".epc" / "project.json", meta)


def stamp_status(target: Path, phase: str, today_iso: str) -> None:
    f = status_file(target)
    if f.exists():
        st = read_json(f, {})
        st.update(phase=phase, start=today_iso, updated=today_iso)
        write_json(f, st)


def _load_build_tool():
    spec = importlib.util.spec_from_file_location("epc_build", settings.build_tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def refresh_lock(target: Path) -> int:
    """Refresh the plugin registry and write <project>/.epc/plugins.lock. Returns the number of locked plugins."""
    build = _load_build_tool()
    build.cmd_registry()
    build.cmd_lock(str(target))
    return len(read_json(target / ".epc" / "plugins.lock", {}).get("plugins", {}))


def write_created_event(target: Path, at: str, plugins: int) -> None:
    write_json(target / ".epc" / "ledger" / "0001_created.json", {"event": "project_created", "at": at, "plugins": plugins})


def remove_created(target: Path) -> None:
    """Remove only a folder created by the current request (must be inside the projects directory)."""
    if target.exists() and settings.projects_dir.resolve() in target.resolve().parents:
        shutil.rmtree(target, ignore_errors=True)
