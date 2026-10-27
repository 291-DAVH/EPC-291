"""Templates of layout: a group of nodes and lines saved with a name (a standard office, a pump room) to put in other drawings and other projects of the organization.

They live with the organization (`<data>/orgs/<slug>/plan-templates/`) so every project of the company sees them; a project without organization keeps them with itself.
Positions are relative to the group's own corner, so a template can be put anywhere.
"""
import re
from pathlib import Path
from typing import List

from epc.core.config import settings
from epc.core.errors import Invalid, NotFound
from epc.core.fsutil import read_json, write_json
from epc.modules.identity import public as identity
from epc.modules.layout.models import TemplateIn
from epc.modules.projects import public as projects

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,47}$")


def _folder(d: Path) -> Path:
    org = projects.read_meta(d).get("org", "")
    return settings.data_dir / "orgs" / org / "plan-templates" if org else d / "workspace" / "00-setup" / "plan-templates"


def _file(d: Path, name: str) -> Path:
    if not NAME.match(name or ""):
        raise Invalid({"name": "letters, digits, spaces, dots, dashes and underscores (up to 48)"})
    return _folder(d) / (name.replace(" ", "_") + ".json")


def listing(d: Path) -> List[dict]:
    folder = _folder(d)
    out = [read_json(p, None) for p in sorted(folder.glob("*.json"))] if folder.is_dir() else []
    return [t for t in out if t]


def save(d: Path, name: str, body: TemplateIn) -> dict:
    path = _file(d, name)
    if not body.nodes and not body.lines:
        raise Invalid({"nodes": "a template needs something to put in it"})
    data = {"name": name, "discipline": body.discipline, "nodes": body.nodes, "lines": body.lines}
    write_json(path, data)
    identity.audit_event("layout_template_saved", target=f"{projects.project_id(d)}:{name}", org_slug=projects.read_meta(d).get("org", ""))
    return data


def remove(d: Path, name: str) -> None:
    path = _file(d, name)
    if not path.is_file():
        raise NotFound("template not found")
    path.unlink()
