"""Public interface of the schedule module."""
from pathlib import Path

from epc.modules.schedule import service


def view(project_dir: Path) -> dict:
    """Activities with dates, critical path and late flags."""
    return service.view(project_dir)


__all__ = ["view"]
