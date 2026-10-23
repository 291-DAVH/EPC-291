"""Public interface of the management module."""
from pathlib import Path

from epc.modules.management import service


def project_summary(project_dir: Path) -> dict:
    """Card data of one project: progress, health, milestone, deliverable and input counters."""
    return service.summary(project_dir)


__all__ = ["project_summary"]
