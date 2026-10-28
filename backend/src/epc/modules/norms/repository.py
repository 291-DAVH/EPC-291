"""Files of the norms review: the engine's norm data (rules, calculation tables, design-criteria catalog), the review state next to them and the review log.

The data files stay the single source of truth and are rewritten with the same formatting they have (so git shows only what the reviewer changed).
The rules of the lighting engine (`epc_lighting/rules/*.rules.json`) are one more unit: the reviewer's approval is kept with the others and the engine reads it from the `review` field of the rule.
The review state lives in the norm package (`epc_aea90364/data/review.json`) (who approved which point, when, and the fingerprint of the approved value) and every action is appended to
`epc_aea90364/data/review-log.jsonl`.
"""
import importlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings

_override: Optional[dict] = None


def override(paths: Optional[dict]) -> None:
    """Tests point the module at a temporary copy of the data."""
    global _override
    _override = paths


def paths() -> dict:
    if _override:
        return _override
    from epc_aea90364 import aea_rules, aea_tables, norm_data
    from epc_lighting import norm_data as lighting_norms
    return {"rules": Path(aea_rules.CARPETA), "tables": Path(aea_tables.RUTA_JSON), "criteria": norm_data.criteria_file("electrical"), "review": norm_data.REVIEW, "log": norm_data.REVIEW_LOG,
            "lighting_rules": lighting_norms.RULES_DIR}


def read(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _indent_of(text: str) -> int:
    lines = text.split("\n")
    return (len(lines[1]) - len(lines[1].lstrip(" "))) if len(lines) > 1 else 1


def write_atomic(path: Path, text: str) -> None:
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def write_like(path: Path, data) -> None:
    """Rewrite a JSON file keeping its indentation and final newline."""
    original = Path(path).read_text(encoding="utf-8-sig")
    text = json.dumps(data, ensure_ascii=False, indent=_indent_of(original.replace("\r\n", "\n")))
    write_atomic(path, text + ("\n" if original.endswith("\n") else ""))


# ---- rules: one file per group
def rule_files() -> List[Path]:
    return sorted(p for p in paths()["rules"].glob("*.json") if not p.name.startswith("_"))


# ---- lighting rules: one file per norm of the lighting engine (`<norm>.rules.json`)
def lighting_files() -> List[Path]:
    folder = paths().get("lighting_rules")
    return sorted(folder.glob("*.rules.json")) if folder else []


# ---- design criteria: header keys, then one compact criterion per line
def dumps_criteria(data: dict) -> str:
    head = [f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}," for k, v in data.items() if k != "criteria"]
    rows = ",\n".join("    " + json.dumps(c, ensure_ascii=False) for c in data["criteria"])
    return "{\n" + "\n".join(head) + '\n  "criteria": [\n' + rows + "\n  ]\n}\n"


def write_criteria(data: dict) -> None:
    write_atomic(paths()["criteria"], dumps_criteria(data))


# ---- review state and log
def review() -> Dict[str, dict]:
    f = paths()["review"]
    return read(f).get("points", {}) if f.exists() else {}


def save_review(points: Dict[str, dict]) -> None:
    f = paths()["review"]
    write_atomic(f, json.dumps({"schema_version": "1.0", "points": dict(sorted(points.items()))}, ensure_ascii=False, indent=1) + "\n")


def log_append(entry: dict) -> None:
    f = paths()["log"]
    with open(f, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def log_read(point_id: Optional[str] = None, limit: int = 100) -> List[dict]:
    f = paths()["log"]
    if not f.exists():
        return []
    rows = [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    if point_id:
        rows = [r for r in rows if r.get("point") == point_id]
    return rows[-limit:][::-1]


_ENGINE_CACHES = (("epc_aea90364.aea_rules", "limpiar_cache_reglas"), ("epc_aea90364.aea_tables", "limpiar_cache_tablas"), ("epc_lighting.norm_data", "clear_cache"))


def _clear(module: str, function: str) -> None:
    try:
        getattr(importlib.import_module(module), function)()
    except ImportError:
        pass


def clear_engine_cache() -> None:
    """The calculation engines keep the data in memory: after a correction they read the files again."""
    for module, function in _ENGINE_CACHES:
        _clear(module, function)
