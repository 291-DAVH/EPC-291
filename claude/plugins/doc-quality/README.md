# doc-quality

Document and specification verifiers and Office-to-PDF input converter used by package self-checks and audits.

- Version: 0.1.0 (workflow)
- Entitlement: `feature.quality`
- Python: stdlib only

## Requires
- none

## Skills
- none

## Outputs
- `.json`: internal

See `plugin.json` for the full manifest. Legacy origin: `00-Template-Claude/.claude/library/plugins/calculations`.

## Engine
This plugin is packaging only. The code lives in `engine/documents` and is copied into the built plugin under `lib/` (set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`).
