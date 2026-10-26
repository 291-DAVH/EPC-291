"""The catalog of DXF layers: what every drawing is delivered with (name, colour, line weight, line type, state).

A drawing asks for a layer by its ROLE (`sld.diagram`, `sld.text`, `plan.ELEC-LUM`...), never by a name written in the code. The catalog says what that role is called and how it looks.
Three sources, the later one winning role by role (a file may carry only the roles or fields it changes):
  1. the default catalog that travels with this package (`data/layers.json`);
  2. the global file the platform's MASTER edits: the path in the environment variable EPC_LAYERS_JSON;
  3. files passed to `load` (later: the project's own file).
"""
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Optional

ENV_VAR = "EPC_LAYERS_JSON"
DEFAULT_FILE = Path(__file__).resolve().parent / "data" / "layers.json"
LINEWEIGHTS = (0.0, 0.05, 0.09, 0.13, 0.15, 0.18, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.53, 0.6, 0.7, 0.8, 0.9, 1.0, 1.06, 1.2, 1.4, 1.58, 2.0, 2.11)      # mm: the ones DXF knows
LINETYPES = ("CONTINUOUS", "DASHED", "DASHDOT", "CENTER", "HIDDEN", "PHANTOM", "DOT")
FLAGS = ("on", "frozen", "locked", "plot")
FORBIDDEN_IN_NAME = '<>/\\":;?*|=`'
BLANK = {"name": "", "color": 7, "lineweight": None, "linetype": "CONTINUOUS", "on": True, "frozen": False, "locked": False, "plot": True}


def _read(path: Path) -> Dict[str, dict]:
    return json.loads(path.read_text(encoding="utf-8-sig")).get("layers", {})


def load(*extra: Optional[os.PathLike]) -> Dict[str, dict]:
    """The catalog: role -> attributes, the default one overridden by the global file and by `extra` files (those that exist)."""
    out = {role: dict(a) for role, a in _read(DEFAULT_FILE).items()}
    paths = [os.environ.get(ENV_VAR), *extra]
    for p in (Path(x) for x in paths if x):
        if p.is_file():
            for role, a in _read(p).items():
                out[role] = {**out.get(role, {}), **a}
    return out


def defaults() -> Dict[str, dict]:
    """The catalog that travels with the package, without any override."""
    return {role: dict(a) for role, a in _read(DEFAULT_FILE).items()}


def override_of(catalog: Dict[str, dict]) -> Dict[str, dict]:
    """What a catalog changes with respect to the default one: role -> only the fields that differ (what the global file stores)."""
    base = defaults()
    out: Dict[str, dict] = {}
    for role, a in catalog.items():
        diff = {k: v for k, v in a.items() if k != "description" and base.get(role, {}).get(k) != v}
        if diff:
            out[role] = diff
    return out


def resolve(catalog: Optional[Dict[str, dict]] = None) -> Dict[str, dict]:
    """The catalog given, or the one in force (default, global file) when none is given."""
    return catalog if catalog is not None else load()


def get(role: str, catalog: Optional[Dict[str, dict]] = None) -> dict:
    """The attributes of a role; a role the catalog does not know gets plain defaults under the role's own name."""
    cat = resolve(catalog)
    return {**BLANK, "name": role.split(".", 1)[-1], **cat.get(role, {})}


def name(role: str, catalog: Optional[Dict[str, dict]] = None) -> str:
    return get(role, catalog)["name"]


def apply(doc, role: str, catalog: Optional[Dict[str, dict]] = None) -> str:
    """Make sure the layer of `role` is in the ezdxf document with its attributes; returns its name."""
    a = get(role, catalog)
    lay = doc.layers.get(a["name"]) if a["name"] in doc.layers else doc.layers.add(a["name"])
    lay.color = int(a["color"])
    lay.dxf.linetype = doc.linetypes.get(a["linetype"]).dxf.name if a["linetype"] in doc.linetypes else "Continuous"       # the name as the document writes it
    if a["lineweight"] is not None:                 # empty: the layer keeps the standard weight (what drawings had before the catalog)
        lay.dxf.lineweight = int(round(float(a["lineweight"]) * 100))
    lay.on, lay.is_frozen, lay.is_locked = bool(a["on"]), bool(a["frozen"]), bool(a["locked"])
    if not a["plot"]:
        lay.dxf.plot = 0
    return a["name"]


def _name_problems(role: str, a: dict) -> Iterable[str]:
    n = str(a.get("name", "")).strip()
    if not n or len(n) > 255 or any(c in n for c in FORBIDDEN_IN_NAME):
        yield f"{role}.name: required, up to 255 characters, none of {FORBIDDEN_IN_NAME}"


def _look_problems(role: str, a: dict) -> Iterable[str]:
    if not isinstance(a.get("color"), int) or isinstance(a.get("color"), bool) or not 1 <= a["color"] <= 255:
        yield f"{role}.color: a whole number from 1 to 255 (AutoCAD colour index)"
    if a.get("lineweight") is not None and a.get("lineweight") not in LINEWEIGHTS:
        yield f"{role}.lineweight: empty (standard) or one of {', '.join(str(x) for x in LINEWEIGHTS)} mm"
    if a.get("linetype") not in LINETYPES:
        yield f"{role}.linetype: one of {', '.join(LINETYPES)}"


def _problems(role: str, a: dict) -> Iterable[str]:
    yield from _name_problems(role, a)
    yield from _look_problems(role, a)
    yield from (f"{role}.{f}: true or false" for f in FLAGS if not isinstance(a.get(f), bool))


def validate(catalog: Dict[str, dict]) -> Dict[str, str]:
    """{field: message} for what a catalog may not contain; empty when it is valid. Two roles may not share a layer name."""
    errors: Dict[str, str] = {}
    seen: Dict[str, str] = {}
    for role, a in catalog.items():
        for msg in _problems(role, a):
            errors[msg.split(":")[0]] = msg.split(": ", 1)[1]
        key = str(a.get("name", "")).strip().lower()
        if key in seen:
            errors[f"{role}.name"] = f"already used by {seen[key]}"
        seen.setdefault(key, role)
    return errors


def dump(catalog: Dict[str, dict], path: os.PathLike) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({"schema_version": "1.0", "layers": catalog}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
