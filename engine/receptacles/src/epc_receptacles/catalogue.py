"""The catalogue of socket outlets: a factory list (`data/receptacles.json`) that a company and a project change on top of, one entry per id.

A level (a file) is `{"schema_version": "1.0", "receptacles": {id: entry}}` and holds only what it changes: an entry replaces the one of the same id below it, and
`{"disabled": true}` removes it. An entry carries a name in both languages, `kind` (`general` or `special`), `poles`, `rated_a`, `power_va`, `height_m` (mounting) and `ip`;
`illustrative` says the numbers are typical, not a maker's.
"""
import copy
from typing import Any, Dict, List, Sequence

from epc_receptacles.config import data

LANGUAGES = ("es", "en")
KINDS = ("general", "special")
_NOT_IN_DOCUMENT = ("name", "illustrative", "disabled", "favorite", "group")


def defaults() -> Dict[str, Dict[str, Any]]:
    """The factory outlets, by id (a copy: callers may change it)."""
    return copy.deepcopy(data("receptacles")["receptacles"])


def merge(layers: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """The factory outlets with the changes of each level applied in order (a level is the `receptacles` object of its file)."""
    out = defaults()
    for layer in layers:
        for rid, entry in (layer or {}).items():
            if isinstance(entry, dict) and entry.get("disabled"):
                out.pop(rid, None)
            else:
                out[rid] = copy.deepcopy(entry)
    return out


def _number(rid: str, entry: Dict[str, Any], key: str, low: float, high: float) -> List[str]:
    value = entry.get(key)
    if value is None:
        return []
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
        return [f"{rid}.{key}: a number from {low} to {high}"]
    return []


def check(rid: str, entry: Any) -> List[str]:
    """What is wrong with an entry, as messages that say what to correct (empty when it is valid)."""
    if not isinstance(entry, dict):
        return [f"{rid}: must be an object"]
    problems = []
    name = entry.get("name")
    if not isinstance(name, dict) or any(not str(name.get(lang, "")).strip() for lang in LANGUAGES):
        problems.append(f"{rid}.name: give the name in both languages ({', '.join(LANGUAGES)})")
    if entry.get("kind", "general") not in KINDS:
        problems.append(f"{rid}.kind: must be one of {', '.join(KINDS)}")
    for key, low, high in (("power_va", 0, 100000), ("rated_a", 0, 1000), ("height_m", 0, 5), ("poles", 1, 4)):
        problems += _number(rid, entry, key, low, high)
    if entry.get("ip") is not None and not isinstance(entry["ip"], str):
        problems.append(f"{rid}.ip: text, for example IP20")
    return problems


def as_document(rid: str, entry: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """The entry as an outlet of the engine's document (its name in the language asked)."""
    name = entry.get("name")
    label = (name.get(lang) or name.get("en") or rid) if isinstance(name, dict) else str(name or rid)
    return {**{k: v for k, v in entry.items() if k not in _NOT_IN_DOCUMENT}, "id": rid, "name": label}
