# iram-titleblock

IRAM A0-A4 drawing sheets (frame, coordinates, IRAM 4504/4508 title block) with custom company/client blocks and logos.

- Version: 0.5.1 (generator)
- Entitlement: `feature.drawing.sheets`
- Python: openpyxl>=3.1, ezdxf, lxml

## Requires
- none

## Skills
- [`generate-titleblock-sheet`](../../skills/generate-titleblock-sheet/SKILL.md) (owner)
- [`generate-iram-sheet`](../../skills/generate-iram-sheet/SKILL.md) (owner)

## Outputs
- `.svg`: internal
- `.dxf`: internal+deliverable

See `plugin.json` for the full manifest. Legacy origin: `291_G_IRAM_Custom_TitleBlocks_Generator`.

## Engine
This plugin is packaging only. The code lives in `engine/drawing` and is copied into the built plugin under `lib/` (set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`).
