"""Where the catalogs of drawing live: one file per level and kind.

  global   <EPC_DATA>/global/<file>                               the MASTER's (console)
  company  <EPC_DATA>/orgs/<organization>/<file>                  the organization's own
  project  <project>/workspace/00-setup/<file>                    the project's own
Each file holds only what its level changes with respect to the levels above it; the engine applies them in that order.
"""
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

FILES: Dict[str, str] = {"layers": "drawing-layers.json", "solutions": "standard-solutions.json"}


def global_file(kind: str) -> Path:
    return settings.layers_file if kind == "layers" else settings.solutions_file


def company_file(kind: str, slug: str) -> Path:
    return settings.data_dir / "orgs" / slug / FILES[kind]


def project_file(kind: str, project_dir: Path) -> Path:
    return project_dir / "workspace" / "00-setup" / FILES[kind]


def chain(kind: str, org_slug: str = "", project_dir: Optional[Path] = None) -> List[Path]:
    """The files of a kind in order of authority: global, then the company's, then the project's (those that apply, whether or not they exist yet)."""
    files = [global_file(kind)]
    if org_slug:
        files.append(company_file(kind, org_slug))
    if project_dir is not None:
        files.append(project_file(kind, project_dir))
    return files


def read(path: Path) -> dict:
    return read_json(path, {}) or {}


def write(path: Path, content: dict) -> None:
    write_json(path, {"schema_version": "1.0", **content})


def delete(path: Path) -> None:
    path.unlink(missing_ok=True)
