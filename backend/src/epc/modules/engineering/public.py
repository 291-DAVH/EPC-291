"""Public interface of the engineering module."""
from pathlib import Path
from typing import Any, Optional

from epc.modules.engineering import repository, service


def criterion_value(project_dir: Path, key: str, discipline: str = "electrical") -> Optional[Any]:
    """Current value of a design criterion of the project (override or base value); None when it does not exist."""
    try:
        return next((i["value"] for i in service.criteria_view(project_dir, discipline)["items"] if i["id"] == key), None)
    except Exception:                                    # noqa: BLE001 - no catalog for this jurisdiction/discipline
        return None




def criteria_values(project_dir: Path, discipline: str = "electrical") -> dict:
    """Current design criteria of the project as {criterion id: value} (overrides applied over the base values); {} when there is no catalog."""
    try:
        return {i["id"]: i["value"] for i in service.criteria_view(project_dir, discipline)["items"]}
    except Exception:                                    # noqa: BLE001
        return {}


def issuable(project_dir: Path) -> list:
    """Sources that can be issued: [{id, name, discipline, package, kind: drawing|document, files: {format: Path}}]."""
    return repository.issuable(project_dir)


__all__ = ["criterion_value", "criteria_values", "issuable"]
