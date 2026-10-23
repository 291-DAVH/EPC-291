# pm2-docs

PM2 management artifacts: CCPM scheduling, charter/canvas exporters, phase canvases. Implements the pm2 methodology pack.

- Version: 0.1.0 (workflow)
- Entitlement: `feature.management.pm2`
- Python: stdlib only

## Requires
- `doc-quality` ^0.1.0

## Skills
- [`create-management-document`](../../skills/create-management-document/SKILL.md) (owner)

## Outputs
- `.md`: internal
- `.pdf`: internal+deliverable

See `plugin.json` for the full manifest. Legacy origin: `00-Template-Claude/.claude/library/plugins/calculations + skill create-pm2-document`.

## Engine
This plugin is packaging only. The code lives in `engine/documents` and is copied into the built plugin under `lib/` (set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`).
