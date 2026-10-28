"""Where the catalogue of luminaires is kept: the factory list lives in the engine; a company and a project keep only what they change.

  company  <EPC_DATA>/orgs/<organization>/luminaires.json
  project  <project>/workspace/00-setup/luminaires.json
"""
from pathlib import Path
from typing import List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

FILE = "luminaires.json"


def company_file(slug: str) -> Path:
    return settings.data_dir / "orgs" / slug / FILE


def project_file(project_dir: Path) -> Path:
    return project_dir / "workspace" / "00-setup" / FILE


def chain(org_slug: str = "", project_dir: Optional[Path] = None) -> List[Path]:
    """The files that apply, in order of authority: the company's, then the project's (whether or not they exist yet). The factory list is the engine's."""
    files = []
    if org_slug:
        files.append(company_file(org_slug))
    if project_dir is not None:
        files.append(project_file(project_dir))
    return files


def read(path: Path) -> dict:
    """The `luminaires` object of a level's file (empty when it has none)."""
    return (read_json(path, {}) or {}).get("luminaires", {}) or {}


def write(path: Path, luminaires: dict) -> None:
    write_json(path, {"schema_version": "1.0", "luminaires": luminaires})


def delete(path: Path) -> None:
    path.unlink(missing_ok=True)
