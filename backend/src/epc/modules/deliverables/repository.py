from pathlib import Path
from typing import List

from epc.core.fsutil import read_json


def read_items(d: Path) -> List[dict]:
    return read_json(d / "workspace" / "05-management" / "deliverables.json", [])


def deliverables_dir(d: Path) -> Path:
    """Client-facing folder: files are served only from here."""
    return d / "deliverables"
