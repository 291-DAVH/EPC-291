"""Where the catalogue of socket outlets is kept: the factory list lives in the engine; a company and a project keep only what they change.

  company  <EPC_DATA>/orgs/<organization>/receptacles.json
  project  <project>/workspace/00-setup/receptacles.json
"""
from pathlib import Path

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

FILE = "receptacles.json"


def company_file(slug: str) -> Path:
    return settings.data_dir / "orgs" / slug / FILE


def project_file(project_dir: Path) -> Path:
    return project_dir / "workspace" / "00-setup" / FILE


def read(path: Path) -> dict:
    """The `receptacles` object of a level's file (empty when it has none)."""
    return (read_json(path, {}) or {}).get("receptacles", {}) or {}


def write(path: Path, receptacles: dict) -> None:
    write_json(path, {"schema_version": "1.0", "receptacles": receptacles})


def delete(path: Path) -> None:
    path.unlink(missing_ok=True)
