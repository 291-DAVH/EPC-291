"""Public interface of the requirements module."""
from pathlib import Path

from epc.modules.requirements import service


def count(project_dir: Path) -> int:
    return service.count(project_dir)


__all__ = ["count"]
