"""The delivery package: several sheets of one drawing, converted and described in one index.

`deliver` takes the SVG of every sheet in development and returns the DXF of each plus the index of the package; `describe` writes the index of sheets that were already converted.
The index (`<name>_entregable.json`) says, for every sheet, its SVG (with its hash), its DXF, the layers it uses with how many entities each holds and the roles the catalog gave them.
It carries no dates and no hash of the DXF (the file stamps itself): the same drawing gives the same index.
"""
import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from epc_dxf import deliverable
from epc_dxf import layers as _L


def _entry(svg: Path, layers: Dict[str, int], blocks: int, role_of: Dict[str, str], messages: Iterable[str]) -> dict:
    return {"sheet": svg.stem, "svg": svg.name, "svg_sha256": hashlib.sha256(svg.read_bytes()).hexdigest(), "dxf": svg.with_suffix(".dxf").name, "blocks": blocks,
            "layers": {name: {"entities": n, "role": role_of.get(name, "")} for name, n in layers.items()}, "messages": list(messages)}


def _roles_by_name(catalog: Dict[str, dict]) -> Dict[str, str]:
    return {a["name"]: role for role, a in catalog.items() if "name" in a}


def describe(svgs: Iterable[Path], out_dir: Path, name: str, layers_file=None) -> dict:
    """Write `<name>_entregable.json` for sheets whose DXF already sits next to their SVG; returns the index."""
    role_of = _roles_by_name(_L.load(layers_file))
    sheets: List[dict] = []
    for svg in (Path(s) for s in svgs):
        dxf = svg.with_suffix(".dxf")
        if dxf.is_file():
            layers, blocks = deliverable.inspect(dxf)
            sheets.append(_entry(svg, layers, blocks, role_of, []))
    index = {"schema_version": "1.0", "name": name, "sheets": sheets}
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / f"{name}_entregable.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return index


def deliver(sheets: Iterable[dict], out_dir: Path, name: str, *, layers_file=None, symbol_library: Optional[str] = None) -> dict:
    """Convert every sheet ({"svg": path, optional "symbol_library"}) and write the index. A sheet that cannot be converted is listed with its message and no DXF."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    role_of = _roles_by_name(_L.load(layers_file))
    entries: List[dict] = []
    for sheet in sheets:
        svg = Path(sheet["svg"])
        done = deliverable.convert(svg, out / svg.with_suffix(".dxf").name, symbol_library=sheet.get("symbol_library", symbol_library), layers_file=layers_file)
        entries.append(_entry(svg, done["layers"], done["blocks"], role_of, done["messages"]) if done["dxf"] else {"sheet": svg.stem, "svg": svg.name, "dxf": None, "messages": done["messages"]})
    index = {"schema_version": "1.0", "name": name, "sheets": entries}
    (out / f"{name}_entregable.json").write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return index
