"""Public interface of the wbs module."""
from pathlib import Path

from epc.modules.wbs import service


def has_node(project_dir: Path, node_id: str) -> bool:
    return service.has_node(project_dir, node_id)


def overall_progress(project_dir: Path) -> float:
    """Weighted progress (0-100) rolled up from the WBS leaves."""
    return service.overall_progress(project_dir)


__all__ = ["has_node", "overall_progress"]
