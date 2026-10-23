---
name: "analyze-standard"
description: "Turns a standard (PDF stored in local/dev-knowledge) into a validated rules.json for the rules engine: extract, read, draft rules with clause references, validate, hand to the human reviewer, promote."
---

# analyze-standard

Owner plugin: `standard-ingest`. The code is the `epc_standards` package (`engine/standards`); run its modules with `python -m epc_standards.<module>` and the project venv.

## Hard rules
1. **Copyright.** The PDF and any verbatim quote stay in `local/dev-knowledge/` (never versioned). A rule in `rules.json` carries the clause number, the page, a **paraphrased** summary (max 240 characters) and machine-readable parameters. Never copy 12 or more consecutive words from the standard; the validator rejects it.
2. **Never invent values.** Every number comes from the standard. If a value is unreadable or ambiguous, lower `confidence`, set `verification`, and list it as an open question for the reviewer.
3. **Claude drafts, the human validates.** `source_status` stays `draft` until the human reviewer says they validated it. Only then run `python -m epc_standards.promote_rules --mark-verified "<name>"`.
4. Product content (ids, topics, parameter names, `title`) is English; `summary` is a locale object (`es` for Argentina). Explain progress to the user in Spanish.

## Workflow
1. **Locate.** Standard folder: `local/dev-knowledge/standards/<CC>/<STANDARD-ID>/` with `source/*.pdf` and `standard.json`. If the PDF sits in `_inbox/`, move it there and create `standard.json` (id, country, body, edition, language, domain).
2. **Extract.** `python -m epc_standards.extract_standard <CC>/<ID>`.
   - `text` or `mixed`: use `extracted/<pdf>/pages/pNNNN.txt`, `clauses.json`, `tables.json`.
   - `scanned` (no text layer): read the pages visually. Render with `python -m epc_standards.render_pages <pdf> 41-45` and open the PNGs, or read the PDF pages directly. Mark those rules `verification: "visual"` (or `"ocr"`).
3. **Scope the pass.** List the chapters/clauses to cover with the user (for example, circuits, protection, conductors, earthing). Work chapter by chapter; do not draft a whole 300-page standard blindly.
4. **Draft** `draft/rules.json` (schema `shared/schemas/rules.schema.json`, version 1.1):
   - one rule per requirement: `id` (stable, dotted), `clause`, `page` (printed and pdf), `topic`, `title`, `summary.<locale>`, `type` (`mandatory | recommended | prohibited`), `applies_to.installation_types`, `params` with the unit in the key suffix (`_m`, `_mm`, `_pct`, `_a`);
   - add `check` only when the requirement is a clean comparison on a named context field (for example `{"field": "tray_reserve_pct", "op": ">=", "value": 20}`); set `applies_to.when` for conditions such as room type;
   - put numeric tables in `tables[]` and reference them with `table_ref`; keep the table notes;
   - put the verbatim quote (if you need one for traceability) in `analysis/evidence.json` under the same key as `evidence_ref`.
5. **Validate.** `python -m epc_standards.validate_rules <draft>`. Fix every ERROR. Review WARNINGs: derived checks need human confirmation; informative rules have no check.
6. **Hand to the human.** Give the reviewer a short Spanish list: rules with `confidence: low`, derived checks, scanned pages, open questions. Do not promote on your own.
7. **Promote** (only after the reviewer validated): `python -m epc_standards.promote_rules <CC>/<ID> --mark-verified "<name>"`. Result: `engine/jurisdictions/<CC>/<domain>/<ID>/rules.json`.
8. **Use.** Calculation plugins load rules through `engine/rules` (`epc_rules`) (`RuleSet.load("AR", "electrical")`); production builds only see `verified` standards.

## Legacy
The 177 rules previously kept in `engine/calc/src/epc_calc/rules/*.json` were imported with `epc_standards.import_legacy_rules` as drafts of six standards. Their ids and parameter names are still Spanish (`i18n_pending`).

## Runtime
The code is a Python package from `engine/` (`epc_standards, epc_rules`). In a repository checkout set `PYTHONPATH=engine/standards/src;engine/rules/src` (use `;` as separator on Windows) or run `pip install -e engine/<area>`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
