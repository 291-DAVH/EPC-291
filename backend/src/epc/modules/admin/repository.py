"""Read-only view of the Claude layer (claude/plugins, claude/skills) for the technical console."""
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterator, List

from epc.core.config import settings
from epc.core.fsutil import read_json


def frontmatter(md: Path) -> Dict[str, str]:
    if not md.exists():
        return {}
    m = re.match(r"^---\s*\n(.*?)\n---", md.read_text(encoding="utf-8"), re.S)
    out = {}
    for line in (m.group(1).splitlines() if m else []):
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"')
    return out


def plugins() -> Iterator[dict]:
    base = settings.plugins_dir
    reg = read_json(base / "registry.json", {"plugins": {}})
    dependents: Dict[str, List[str]] = {}
    manifests = {}
    for d in sorted(p for p in base.iterdir() if p.is_dir()):
        if (d / "plugin.json").exists():
            m = read_json(d / "plugin.json", {})
            manifests[m["id"]] = m
            for dep in m.get("requires", {}):
                dependents.setdefault(dep, []).append(m["id"])
    for pid, m in manifests.items():
        yield {"id": pid, "version": m["version"], "kind": m["kind"], "status": m.get("status", "active"),
               "description": m.get("description", ""), "discipline": m.get("discipline", []), "requires": m.get("requires", {}),
               "required_by": dependents.get(pid, []), "skills": m.get("skills", []), "outputs": m.get("outputs", []),
               "engine": m.get("engine", []), "entitlement": m.get("entitlement"), "python": m.get("python", {}).get("requires", []),
               "hash": reg["plugins"].get(pid, {}).get("hash")}


def plugin_readme(pid: str) -> str:
    f = settings.plugins_dir / pid / "README.md"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def skills() -> Iterator[dict]:
    base = settings.skills_dir
    reg = read_json(base / "_registry.json", {})
    owners = {s["id"]: p["id"] for p in plugins() for s in p["skills"]}
    for d in sorted(p for p in base.iterdir() if p.is_dir() and (p / "SKILL.md").exists()):
        fm = frontmatter(d / "SKILL.md")
        yield {"id": d.name, "owner": owners.get(d.name), "description": fm.get("description", ""),
               "legacy_id": reg.get(d.name, {}).get("legacy_id"), "active": d.name in owners}


def skill_conflicts() -> list:
    try:
        out = subprocess.run([sys.executable, str(settings.skill_check_tool), "--json", "--env", "production"],
                             capture_output=True, text=True, timeout=30)
        return json.loads(out.stdout or "[]")
    except Exception:
        return []


def layers_override() -> dict:
    """What the MASTER changed in the catalog of DXF layers (only the differences with the default catalog)."""
    return read_json(settings.layers_file, {}).get("layers", {})


def save_layers_override(catalog: dict) -> None:
    from epc.core.fsutil import write_json
    write_json(settings.layers_file, {"schema_version": "1.0", "layers": catalog})


def reset_layers() -> None:
    settings.layers_file.unlink(missing_ok=True)
