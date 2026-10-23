from pathlib import Path
from typing import List

from epc.core.fsutil import read_json


def read_all(d: Path) -> List[dict]:
    return read_json(d / "workspace" / "00-setup" / "requirements.json", [])
