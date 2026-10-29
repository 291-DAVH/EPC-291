"""Public interface of the projects module (the only thing other modules may import)."""
from pathlib import Path
from typing import List, Optional

from epc.modules.projects import repository, service

PUBLIC_PATHS = {"/api/projects/options"}
PUBLIC_POST_PATHS = {"/api/projects"}


def get_project_dir(client: str, code: str) -> Path:
    """Validated project folder; raises NotFound for unknown or malformed ids."""
    return service.get_dir(client, code)


def list_project_dirs() -> List[Path]:
    return repository.project_dirs()


def project_id(d: Path) -> str:
    return repository.project_id(d)


def read_meta(d: Path) -> dict:
    return repository.read_meta(d)


def emissions_allowed(d: Path) -> List[str]:
    """The emissions to the client (`ifa`, `ifc`, `as-built`) the project goes through, up to the final phase it chose."""
    return service.emissions_allowed(repository.read_meta(d))


def end_phase(d: Path) -> str:
    """The last phase the project goes through (empty for a project made before the end phase existed)."""
    return repository.read_meta(d).get("end_phase") or ""


def norm_engine(jurisdiction: str, discipline: str) -> Optional[str]:
    """The norm engine that holds the norm data of a discipline in a jurisdiction (None when it has none)."""
    return repository.norm_engine(jurisdiction, discipline)


def read_status(d: Path) -> dict:
    return repository.read_status(d)


def project_count() -> int:
    return len(repository.project_dirs())


def project_tree(project_id: str, area: str, depth: int, formats: dict) -> dict:
    return service.tree(project_id, area, depth, formats)


__all__ = ["PUBLIC_PATHS", "PUBLIC_POST_PATHS", "get_project_dir", "list_project_dirs", "project_id", "read_meta", "read_status",
           "project_count", "project_tree", "emissions_allowed", "end_phase"]
