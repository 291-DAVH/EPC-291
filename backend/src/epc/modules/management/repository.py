from pathlib import Path
from typing import List

from epc.core.fsutil import read_json


def reports_index(d: Path) -> List[dict]:
    return read_json(d / "workspace" / "05-management" / "reports" / "index.json", [])
