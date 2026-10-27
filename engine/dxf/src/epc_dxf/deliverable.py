"""The deliverable service: a drawing hands over its SVG in development and gets back the DXF.

Whoever draws (the single-line, the multi-line, any plan) does not know DXF. It says "here is my SVG, make it a deliverable": symbols that have a DXF block become INSERTs, the strokes are
converted, every entity goes to the layer of its role (`data-layer` in the SVG) as the catalog of layers names it, and colour and line weight follow the SVG.
"""
import hashlib
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import ezdxf

from epc_dxf import layers as _L


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare(text: str, symbol_library, tmp_svg: Path) -> list:
    """Write the SVG the converter reads (without the symbols that go as blocks) and return those symbols."""
    from epc_dxf import bloques_dxf
    stripped, instances = bloques_dxf.separar(text, symbol_library) if symbol_library else (text, [])
    tmp_svg.write_text(stripped, encoding="utf-8", newline="\n")
    return instances


def _finish(tmp_dxf: Path, tmp_svg: Path, instances: list, symbol_library, height_mm: float, catalog: Dict[str, dict], a3: Optional[bool]) -> int:
    from epc_dxf import bloques_dxf, capas_dxf
    capas_dxf.aplicar(str(tmp_dxf), catalog)
    capas_dxf.colorear(str(tmp_svg), str(tmp_dxf), catalog, a3)                       # colour, line weight and the layer of each entity by its role
    return bloques_dxf.insertar(str(tmp_dxf), symbol_library, instances, height_mm, catalog)[0] if instances else 0


def _retarget(entity, name: str) -> None:
    entity.dxf.layer = name
    for attrib in getattr(entity, "attribs", []):                                   # the attributes of a block reference go with it
        attrib.dxf.layer = name


def finish_draft(doc, dxf_path, layers_file=None) -> dict:
    """A DXF in development (an ezdxf document) whose entities sit on layers named by their ROLE (`plan.ELEC-LUM`) becomes the deliverable: every role layer is renamed
    and given the look the catalog says, the entities follow and the file is saved. Returns {"dxf": path, "layers": {name: entities}, "blocks": inserts}."""
    catalog = _L.load(layers_file)                                                   # a path or a list of paths: global, company, project
    drafts = [lay.dxf.name for lay in doc.layers if lay.dxf.name in catalog]
    final = {role: _L.apply(doc, role, catalog) for role in drafts}
    for entity in doc.modelspace():
        if entity.dxf.layer in final:
            _retarget(entity, final[entity.dxf.layer])
    for role in drafts:
        if final[role] != role:
            doc.layers.remove(role)
    Path(dxf_path).parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(dxf_path))
    layers, blocks = inspect(Path(dxf_path))
    return {"dxf": str(dxf_path), "layers": layers, "blocks": blocks}


def inspect(dxf: Path) -> tuple:
    """(entities per layer, symbols inserted as blocks) of the model space of a DXF."""
    counts: Dict[str, int] = {}
    blocks = 0
    for e in ezdxf.readfile(str(dxf)).modelspace():
        counts[e.dxf.layer] = counts.get(e.dxf.layer, 0) + 1
        blocks += e.dxftype() == "INSERT"
    return dict(sorted(counts.items())), blocks


def layers_used(dxf: Path) -> Dict[str, int]:
    """How many entities each layer of the DXF holds (the model space)."""
    return inspect(dxf)[0]


def convert(svg_path, dxf_path=None, *, symbol_library=None, layers_file=None, a3: Optional[bool] = None) -> dict:
    """SVG in development -> DXF deliverable. Returns {"dxf": path or None, "blocks": symbols inserted as blocks, "layers": {name: entities}, "messages": [...]}.
    `symbol_library` is the folder with the DXF blocks of the symbols (the SVG keeps those it does not know as strokes); `layers_file` an extra catalog that wins over the global one."""
    from epc_dxf import svg_to_dxf
    svg = Path(svg_path)
    dxf = Path(dxf_path) if dxf_path else svg.with_suffix(".dxf")
    text = svg.read_text(encoding="utf-8")
    tmp_svg, tmp_dxf = svg.with_name(svg.stem + "_trazos.svg"), svg.with_name(svg.stem + "_trazos.dxf")
    catalog = _L.load(layers_file)
    try:
        instances = _prepare(text, symbol_library, tmp_svg)
        svg_to_dxf.convertir(str(tmp_svg))
        height = float(re.search(r'height="([\d.]+)mm"', text).group(1)) if instances else 0.0
        blocks = _finish(tmp_dxf, tmp_svg, instances, symbol_library, height, catalog, a3)
        os.replace(tmp_dxf, dxf)
    except PermissionError:
        return {"dxf": None, "blocks": 0, "layers": {}, "messages": [f"AVISO no se pudo escribir {dxf.name}: está abierto en otro programa (cerrarlo y volver a generar)"]}
    finally:
        tmp_svg.unlink(missing_ok=True)
    msgs: List[str] = [f"DXF {svg.stem}: {blocks} símbolos como bloques"] if blocks else []
    return {"dxf": str(dxf), "blocks": blocks, "layers": layers_used(dxf), "messages": msgs}
