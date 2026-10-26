"""Semantic roles in an SVG: which layer of the catalog each part of a drawing belongs to.

An element says what it IS with `data-layer="<role>"` (`sld.diagram`, `sld.text`, `sld.titleblock`, `sld.sheet`); the converter reads it, looking at the element and then at its ancestors,
and the catalog of layers says what that role is called in the DXF. Nothing depends any more on where an element sits on the sheet.
The sheet itself (frame, coordinates, title block) comes from the IRAM template, whose groups are known by their id: `tag_iram_sheet` marks them.
"""
import re

ATTRIBUTE = "data-layer"
SHEET_GROUPS = ("corte", "recuadro", "coordenadas", "escala_comparacion", "orientacion")
TITLEBLOCK_GROUPS = ("rotulo_IRAM4508", "modificaciones_IRAM4508")


def _mark(svg: str, group_id: str, role: str) -> str:
    """Add the role to the group with that id unless it already has one."""
    return re.sub(rf'<g id="{group_id}"(?![^>]*{ATTRIBUTE}=)', f'<g id="{group_id}" {ATTRIBUTE}="{role}"', svg)


def tag_iram_sheet(svg: str, sheet: str = "sld.sheet", titleblock: str = "sld.titleblock") -> str:
    """The IRAM template with its frame groups in the `sheet` role and its title block in the `titleblock` role."""
    for g in SHEET_GROUPS:
        svg = _mark(svg, g, sheet)
    for g in TITLEBLOCK_GROUPS:
        svg = _mark(svg, g, titleblock)
    return svg


def role_attribute(role: str) -> str:
    return f' {ATTRIBUTE}="{role}"'
