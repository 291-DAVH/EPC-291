"""Public interface of the backlog module."""
from pathlib import Path

from epc.modules.backlog import service


def counts(project_dir: Path) -> dict:
    """Items per status: backlog, todo, doing, done."""
    return service.counts(project_dir)


def view(project_dir: Path) -> dict:
    """Backlog items with counts and the open estimate (hours)."""
    return service.view(project_dir)


__all__ = ["counts", "view"]
