from pathlib import Path
from typing import List

from epc.core.fsutil import read_json, write_json


def _file(d: Path) -> Path:
    return d / "workspace" / "05-management" / "schedule.json"


def load(d: Path) -> List[dict]:
    data = read_json(_file(d), {})
    return data.get("activities", []) if isinstance(data, dict) else []


def save(d: Path, activities: List[dict]) -> None:
    write_json(_file(d), {"schema_version": "1.0", "activities": activities})
