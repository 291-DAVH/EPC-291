"""Public interface of the engineering module."""
from pathlib import Path
from typing import Any, Optional

from epc.modules.engineering import service


def criterion_value(project_dir: Path, key: str, discipline: str = "electrical") -> Optional[Any]:
    """Current value of a design criterion of the project (override or base value); None when it does not exist."""
    try:
        return next((i["value"] for i in service.criteria_view(project_dir, discipline)["items"] if i["id"] == key), None)
    except Exception:                                    # noqa: BLE001 - no catalog for this jurisdiction/discipline
        return None


__all__ = ["criterion_value"]
