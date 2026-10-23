"""Public interface of the intake module."""
from pathlib import Path
from typing import Dict

from epc.modules.intake import service


def input_counts(project_dir: Path) -> dict:
    """{total, open}: open = received or still under analysis."""
    return service.input_counts(project_dir)


def titles_by_id(project_dir: Path) -> Dict[str, str]:
    return service.titles_by_id(project_dir)


__all__ = ["input_counts", "titles_by_id"]
