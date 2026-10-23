---
name: "write-memo-summary"
description: "Writes the Sintesis de Proyecto (PROJECT_SP.md) of the board's main feeder: one page, requirement | technical data, at most three observations. Runs after calculation-memo. Markdown only, never PDF or Word."
---

# Project summary skill (SP of the main feeder)

## Prerequisite
`<PROJECT>_calculo.json` and `<PROJECT>_MC.md` exist (see `calculation-memo`).

## Output
`<PROJECT>_SP.md`, one page, with this structure:
- Table: normative requirement | technical data (capacity, voltage drop, protection and breaking capacity, minimum short-circuit current, minimum section).
- Overall result: CUMPLE / NO CUMPLE.
- Observations: at most three, numbered.

## Rules
- Take every value from the calculation. Do not recompute.
- Pending items are written as "Pendiente" and listed as observations.
- No signatures. No PDF or Word.

## Runtime
The code is a Python package from `engine/` (`epc_calc`). In a repository checkout set `PYTHONPATH=engine/calc/src` (use `;` as separator on Windows) or run `pip install -e engine/<area>`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
