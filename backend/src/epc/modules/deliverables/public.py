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


def add_items(project_dir: Path, new_items: list) -> list:
    """Register deliverables (ENT ids are assigned) and return them."""
    return service.add_items(project_dir, new_items)


def next_code_number(project_dir: Path, prefix: str) -> int:
    return service.next_code_number(project_dir, prefix)


def set_delivered(project_dir: Path, item_ids: list, date_iso: str) -> None:
    service.set_delivered(project_dir, item_ids, date_iso)


def list_items(project_dir: Path) -> list:
    """Deliverables with their status, due date and overdue flag."""
    return service.list_items(project_dir)


__all__ = ["counts", "due_soon", "format_policy", "add_items", "next_code_number", "set_delivered", "list_items"]
