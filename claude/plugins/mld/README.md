# mld

Converts an SLD into a multi-line diagram (MLD) by expanding each line into its conductors. Pending.

- Version: 0.1.0 (generator) - **pending**
- Entitlement: `feature.drawing.mld`
- Python: openpyxl>=3.1, lxml, ezdxf

## Requires
- `sld` ^0.1.0
- `iram-titleblock` ^0.5.1
- `iec-symbols` ^0.4.14

## Skills
- [`convert-sld-to-mld`](../../skills/convert-sld-to-mld/SKILL.md) (owner)

## Outputs
- `.svg`: internal
- `.dxf`: internal+deliverable

See `plugin.json` for the full manifest. Legacy origin: `mld-generator`.
