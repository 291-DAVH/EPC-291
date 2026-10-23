# iec-symbols

IEC 60617 symbol library for single-line (SLD) and multi-line (MLD) diagrams, LV and MV, in SVG and DXF blocks, with catalogs.

- Version: 0.4.16 (knowledge)
- Entitlement: `feature.drawing.electrical`
- Python: cairosvg, pillow

## Requires
- none

## Skills
- [`generate-electrical-symbol`](../../skills/generate-electrical-symbol/SKILL.md) (owner)

## Outputs
- `.svg`: internal
- `.dxf`: internal

See `plugin.json` for the full manifest. Legacy origin: `291_E_IEC60617_Symbols_Generator`.

## Engine
This plugin is packaging only. The code lives in `engine/drawing` and is copied into the built plugin under `lib/` (set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`).
