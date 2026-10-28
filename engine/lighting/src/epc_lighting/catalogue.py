"""The catalogue of luminaires: a factory list (`data/luminaires.json`) that a company and a project change on top of, one entry per id.

A level (a file) is `{"schema_version": "1.0", "luminaires": {id: entry}}` and holds only what it changes: an entry replaces the one of the same id below it, and
`{"disabled": true}` removes it. An entry carries what the document of the engine needs (`lamps`, `lamp_flux_lm`, `power_w`, optionally `cu`, `cu_table`, `photometry`,
`distribution`, `spacing_ratio`), a name in both languages and `kind` (`interior` or `exterior`); `illustrative` says the numbers are typical, not a maker's.
"""
import copy
from typing import Any, Dict, List, Sequence

from epc_lighting.config import data
from epc_lighting.document import parse_luminaire
from epc_lighting.model import LightingError

LANGUAGES = ("es", "en")
KINDS = ("interior", "exterior")
_NOT_IN_DOCUMENT = ("name", "kind", "illustrative", "disabled", "power_factor", "favorite", "group")          # what the platform keeps about a luminaire and the engine does not read


def defaults() -> Dict[str, Dict[str, Any]]:
    """The factory luminaires, by id (a copy: callers may change it)."""
    return copy.deepcopy(data("luminaires")["luminaires"])


def merge(layers: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """The factory luminaires with the changes of each level applied in order (a level is the `luminaires` object of its file)."""
    out = defaults()
    for layer in layers:
        for lid, entry in (layer or {}).items():
            if isinstance(entry, dict) and entry.get("disabled"):
                out.pop(lid, None)
            else:
                out[lid] = copy.deepcopy(entry)
    return out


def check(lid: str, entry: Any) -> List[str]:
    """What is wrong with an entry, as messages that say what to correct (empty when it is valid)."""
    if not isinstance(entry, dict):
        return [f"{lid}: must be an object"]
    problems = []
    name = entry.get("name")
    if not isinstance(name, dict) or any(not str(name.get(lang, "")).strip() for lang in LANGUAGES):
        problems.append(f"{lid}.name: give the name in both languages ({', '.join(LANGUAGES)})")
    if entry.get("kind", "interior") not in KINDS:
        problems.append(f"{lid}.kind: must be one of {', '.join(KINDS)}")
    problems += _check_extras(lid, entry)
    try:
        parse_luminaire(as_document(lid, entry), "luminaire")
    except LightingError as exc:
        problems.append(str(exc))
    return problems


def _check_extras(lid: str, entry: Dict[str, Any]) -> List[str]:
    """The fields the platform keeps with a luminaire: the power factor of its driver, whether it is a favourite and the group it is listed under."""
    found = []
    factor = entry.get("power_factor")
    if factor is not None and (isinstance(factor, bool) or not isinstance(factor, (int, float)) or not 0 < factor <= 1):
        found.append(f"{lid}.power_factor: a number above 0 and up to 1")
    if entry.get("favorite") is not None and not isinstance(entry["favorite"], bool):
        found.append(f"{lid}.favorite: true or false")
    group = entry.get("group")
    if group is not None and (not isinstance(group, str) or len(group) > 40):
        found.append(f"{lid}.group: text, up to 40 characters")
    return found


def as_document(lid: str, entry: Dict[str, Any], lang: str = "en") -> Dict[str, Any]:
    """The entry as a luminaire of the engine's document (its name in the language asked)."""
    name = entry.get("name")
    label = (name.get(lang) or name.get("en") or lid) if isinstance(name, dict) else str(name or lid)
    return {**{k: v for k, v in entry.items() if k not in _NOT_IN_DOCUMENT}, "id": lid, "name": label}          # the key is the id: an "id" inside the entry does not rename it
