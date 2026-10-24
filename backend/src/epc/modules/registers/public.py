"""Public interface of the registers module."""
from pathlib import Path
from typing import Callable, List, Optional

from epc.modules.registers import service


def items(project_dir: Path, kind: str) -> List[dict]:
    """Records of a register (risk, change, issue, decision, assumption, stakeholder), oldest first."""
    return service.items(project_dir, kind)


def closed_states(project_dir: Path, kind: str) -> List[str]:
    """Statuses that take a record of this register out of the active list."""
    return service.closed_states(project_dir, kind)


def labeler(project_dir: Path, lang: Optional[str] = None) -> Callable[[str, str, str], str]:
    """label(kind, field, value) -> the text of an option in the report language."""
    return service.labeler(project_dir, lang)


__all__ = ["items", "closed_states", "labeler"]
