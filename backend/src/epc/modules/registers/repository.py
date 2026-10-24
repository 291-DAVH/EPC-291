"""Files of the registers: the methodology's definitions and workspace/05-management/registers/<kind>.json."""
from pathlib import Path
from typing import List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json


def definitions(methodology: str) -> Optional[dict]:
    return read_json(settings.methodologies_dir / methodology / "registers.json", None)


def _file(d: Path, kind: str) -> Path:
    return d / "workspace" / "05-management" / "registers" / f"{kind}.json"


def load(d: Path, kind: str) -> List[dict]:
    return (read_json(_file(d, kind), {}) or {}).get("items", [])


def save(d: Path, kind: str, items: List[dict]) -> None:
    write_json(_file(d, kind), {"schema_version": "1.0", "kind": kind, "items": items})
