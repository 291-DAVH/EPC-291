# standard-ingest

Turns standards (PDFs kept in dev-knowledge) into validated rules.json files per standard: text extraction, page rendering for scanned standards, validation (schema, verbatim-copy guard, clause check) and promotion to jurisdictions/. Works with the rules engine in core/rules.

- Version: 0.1.0 (workflow)
- Entitlement: `feature.rules.ingest`
- Python: pypdf, pypdfium2, pillow, jsonschema

## Requires
- none

## Skills
- [`analyze-standard`](../../skills/analyze-standard/SKILL.md) (owner)

## Outputs
- `.json`: internal

See `plugin.json` for the full manifest. Legacy origin: `aea-calc/scripts/rules (177 rules imported by scripts/import_legacy_rules.py)`.
