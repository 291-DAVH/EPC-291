"""Public interface of the requirements module."""
from pathlib import Path

from epc.modules.requirements import service


def count(project_dir: Path) -> int:
    return service.count(project_dir)


def list_requirements(project_dir: Path) -> list:
    """Requirements with open and answered questions."""
    return service.list_requirements(project_dir)


__all__ = ["count", "list_requirements"]
