from pathlib import Path
from typing import List

from epc.core.fsutil import read_json, write_json


def _file(d: Path) -> Path:
    return d / "workspace" / "00-setup" / "requirements.json"


def read_all(d: Path) -> List[dict]:
    return read_json(_file(d), [])


def write_all(d: Path, reqs: List[dict]) -> None:
    write_json(_file(d), reqs)
