from pathlib import Path
from typing import List

from epc.core.fsutil import read_json, write_json


def reports_index(d: Path) -> List[dict]:
    return read_json(d / "workspace" / "05-management" / "reports" / "index.json", [])


def save_reports_index(d: Path, items: List[dict]) -> None:
    write_json(d / "workspace" / "05-management" / "reports" / "index.json", items)
