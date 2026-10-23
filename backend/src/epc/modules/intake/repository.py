import re
from pathlib import Path
from typing import List

from epc.core.fsutil import read_json, write_json


def intake_dir(d: Path) -> Path:
    return d / "workspace" / "01-input" / "intake"


def read_all(d: Path) -> List[dict]:
    return [read_json(f, {}) for f in sorted(intake_dir(d).glob("INT-*.json"))]


def next_id(d: Path) -> str:
    nums = [int(m.group(1)) for f in intake_dir(d).glob("INT-*.json") if (m := re.match(r"INT-(\d+)", f.name))]
    return f"INT-{(max(nums) + 1) if nums else 1:04d}"


def save_attachment(d: Path, intake_id: str, name: str, data: bytes) -> None:
    target = intake_dir(d) / "files" / intake_id
    target.mkdir(parents=True, exist_ok=True)
    (target / name).write_bytes(data)


def save_record(d: Path, record: dict) -> None:
    write_json(intake_dir(d) / f"{record['id']}.json", record)
