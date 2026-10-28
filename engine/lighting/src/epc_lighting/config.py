"""Loads params.json (algorithm settings) and the data catalogues once.

The catalogues are read-only: callers must never mutate what `data()` returns.
"""
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

_HERE = Path(__file__).resolve().parent

VERSION = "0.1.0"
PARAMS: Dict[str, Any] = json.loads((_HERE / "params.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def data(name: str) -> Dict[str, Any]:
    """The catalogue `data/<name>.json`, parsed once."""
    return json.loads((_HERE / "data" / f"{name}.json").read_text(encoding="utf-8"))
