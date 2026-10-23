from pathlib import Path
from typing import List

from epc.core.fsutil import read_json, write_json


def _file(d: Path) -> Path:
    return d / "workspace" / "05-management" / "backlog.json"


def load(d: Path) -> List[dict]:
    data = read_json(_file(d), {})
    return data.get("items", []) if isinstance(data, dict) else []


def save(d: Path, items: List[dict]) -> None:
    write_json(_file(d), {"schema_version": "1.0", "items": items})
