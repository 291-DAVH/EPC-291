"""Public interface of the backlog module."""
from pathlib import Path

from epc.modules.backlog import service


def counts(project_dir: Path) -> dict:
    """Items per status: backlog, todo, doing, done."""
    return service.counts(project_dir)


__all__ = ["counts"]
