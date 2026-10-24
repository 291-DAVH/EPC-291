# Knowledge: from a standard to the engine

How the platform learns from standards (NFPA, AEA, IEC, IRAM...) without distributing them.

## The three layers

| Layer | What it is | Where | Versioned / public |
|---|---|---|---|
| **1. Sources** | The standards themselves (PDF) and study material. Protected by copyright: they cannot be distributed. | `local/dev-knowledge/` | **Never** (ignored folder, `*.pdf` ignored, pre-commit hook) |
| **2. Extracted knowledge** | What Claude learns by reading, analysing and understanding a standard, written in our own words as structured data: requirements, parameters, formulas, tables of values, checks. | `engine/jurisdictions/<country>/<domain>/<standard>/rules.json` and the calculation data inside `engine/calc` | **Yes**: it belongs to the engine and ships with it |
| **3. Execution** | Python code that applies that knowledge: it evaluates checks, runs formulas and queries tables. | `engine/rules`, `engine/calc`, exposed by the backend module `knowledge` and by the Claude skills | Yes |

The backend module `backend/src/epc/modules/knowledge` is only the API over layer 2 (search, topics, check an installation against the rules). It is source code, not study material.

## Workflow (when a new standard arrives)
1. You place the PDF in `local/dev-knowledge/standards/<country>/<standard>/source/`.
2. Claude studies it (skill `analyze-standard`) and writes a draft `rules.json` in its own words: clause, topic, type (mandatory / recommended / prohibited), parameters, and a machine-readable `check` when the requirement can be evaluated.
3. The guard rejects drafts that copy the standard (no passage of 12 or more words in common with the source).
4. A human validates the draft; its `source_status` goes from `draft` to `verified`. Production uses only verified rules.
5. Whatever is extracted ships with the engine; the PDF never leaves `local/`.

## Python first, so tokens are not spent on arithmetic
Claude reads and interprets the standard **once**; from then on the numbers are produced by Python, not by the model:
- a requirement with a numeric limit becomes a `check` evaluated by `epc_rules`;
- a formula becomes a function in `epc_calc` (voltage drop, ampacity, short circuit, protection, hydraulics...);
- a table becomes data queried by code (`aea_tables.json`).

Each of these has tests in `engine/<area>/tests` (`engine/calc/tests`: 15 test files over the calculation modules, run by `python tools/ci/run_gate.py`). When a new calculation is derived from a standard, the rule is: Python function + test with a worked example first, then the skill that calls it.

## Rules for what is committed
- No PDF, no scanned page, no text copied from a standard. Extracted rules are paraphrased; a short reference (standard, edition, clause, page) is enough to locate the source.
- Values (limits, coefficients, table cells) are data of the engine; keep the clause reference next to them.
- Everything unverified is marked `draft` and is not used in production.

## Literal quotations
The early AEA rules in `engine/calc/src/epc_calc/rules/*.json` used to carry a `cita` field with a short literal quotation. It was removed (2026-10-23): a rule keeps only the reference (standard, edition, clause, page). The original rules with their quotations, and the scripts that verified them against the PDFs, are kept privately under `local/dev-knowledge/extracted/`. A test prevents literal text from coming back.
