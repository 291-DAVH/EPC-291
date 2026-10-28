# epc-standards

Pipeline that turns a standard (PDF kept in `local/dev-knowledge/standards/<CC>/<ID>/`) into a validated `rules.json` inside the norm engine its jurisdiction names (`engine/aea90364/...`).

| Module | Purpose |
|---|---|
| `epc_standards.extract_standard` | Text per page, clause index, table captions; detects scanned PDFs |
| `epc_standards.render_pages` | Renders pages to PNG so scanned standards can be read visually |
| `epc_standards.validate_rules` | Schema, unique ids, tables, clause exists, no verbatim copy (12+ words) |
| `epc_standards.promote_rules` | Gate: only human-verified drafts reach the norm engine (`engine/<norm>/src/epc_<norm>/standards/<ID>/rules.json`) |
| `epc_standards.import_legacy_rules` | One-off importer of the first 177 legacy rules |

Run with `PYTHONPATH=engine/standards/src` (or `pip install -e engine/standards`), for example:
`python -m epc_standards.extract_standard AR/AEA-90364-7-771`.
Tests: `python -m unittest discover -s tests` from this folder with `PYTHONPATH=src`.
Rule format: `shared/schemas/rules.schema.json`. Engine that uses the rules: `engine/rules`.
