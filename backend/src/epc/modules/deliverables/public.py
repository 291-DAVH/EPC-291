"""Public interface of the deliverables module."""
from pathlib import Path

from epc.modules.deliverables import service


def counts(project_dir: Path) -> dict:
    """{total, delivered, overdue} deliverables of a project."""
    return service.counts(project_dir)


def due_soon(project_dir: Path, limit_iso: str) -> int:
    """Undelivered deliverables due on or before `limit_iso` (overdue included)."""
    return service.due_soon(project_dir, limit_iso)


def format_policy() -> dict:
    """Which formats may leave the workspace (shared/schemas/deliverable-policy.json)."""
    return service.format_policy()


__all__ = ["counts", "due_soon", "format_policy"]
