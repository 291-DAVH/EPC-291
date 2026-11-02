"""Loads params.json (the settings of the algorithm) and the data of the engine (uses of a room, outlets) once.

What `data()` returns is shared and read-only: a caller that needs to change it copies it first.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent

VERSION = "0.1.0"
PARAMS: Dict[str, Any] = json.loads((_HERE / "params.json").read_text(encoding="utf-8"))
USES = _HERE / "data" / "uses.json"                       # the typical values the norms review confirms: outlets by use, mounting heights, outlets per circuit


@lru_cache(maxsize=None)
def data(name: str) -> Dict[str, Any]:
    """The catalogue `data/<name>.json`, parsed once."""
    return json.loads((_HERE / "data" / f"{name}.json").read_text(encoding="utf-8"))


def clear_cache() -> None:
    """Read the data again: the norms review rewrites `data/uses.json` while the platform runs."""
    data.cache_clear()
