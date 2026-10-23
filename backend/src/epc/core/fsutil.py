"""Small file-system helpers shared by modules (no business rules here)."""
import datetime as dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from epc.core.errors import NotFound

SLUG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,47}$")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return default


def write_json(path: Path, obj: Any) -> None:
    """Atomic write (temporary file + rename), UTF-8, LF."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def count_files(folder: Path) -> int:
    folder = Path(folder)
    return sum(1 for f in folder.rglob("*") if f.is_file() and f.name != ".gitkeep") if folder.exists() else 0


def is_inside(base: Path, rel: str) -> bool:
    """True when base/rel is an existing file that stays inside base (no path traversal)."""
    try:
        p = (Path(base) / rel).resolve()
        return Path(base).resolve() in p.parents and p.is_file()
    except OSError:
        return False


def safe_file(base: Path, rel: str) -> Path:
    if not is_inside(base, rel):
        raise NotFound("file not found")
    return (Path(base) / rel).resolve()


def today() -> dt.date:
    return dt.date.today()
