# sld

Single-line diagram (SLD) of a board on IRAM sheets from a circuit Excel: SVG and DXF per sheet plus a circuit calculation table sheet.

- Version: 0.1.1 (generator)
- Entitlement: `feature.drawing.sld`
- Python: openpyxl>=3.1, lxml, ezdxf, svgelements, shapely

## Requires
- `aea-calc` ^1.6.0
- `iec-symbols` ^0.4.14
- `iram-titleblock` ^0.5.1

## Skills
- [`generate-sld`](../../skills/generate-sld/SKILL.md) (owner)

## Outputs
- `.svg`: internal
- `.dxf`: internal+deliverable
- `.json`: internal

See `plugin.json` for the full manifest. Legacy origin: `sld-generator`.
