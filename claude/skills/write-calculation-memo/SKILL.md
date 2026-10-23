---
name: "write-calculation-memo"
description: "Exports all circuits to PROJECT_calculo.json (for sld-generator) and writes the Memoria de Calculo (PROJECT_MC.md) of the board's main feeder, in the aea90364-feeder-sizing format. Markdown only, never PDF or Word. Runs after electrical-dimensioning."
---

# Calculation memo skill (JSON + MC of the main feeder)

## Prerequisite
Calculations complete (`electrical-dimensioning`). If not, run it first.

## Outputs
1. `<PROJECT>_calculo.json`: every circuit, keys In, Ib, icu, S, dU, disp (unchanged for sld-generator).
2. `<PROJECT>_MC.md`: Memoria de Calculo of the main feeder only.

## Command
`python -m epc_calc.aea_pipeline src/input_for_sld_V1.xlsx` writes both files. Use `--alimentador TAG` to choose another feeder. By default it is the first circuit with no PARENT_TAG and KIND `mccb`. If there is none, the JSON is still written and a warning is reported.

## MC structure (aea90364-feeder-sizing, stages 1 to 6)
1. Objective, scope and regulatory framework.
2. Stage 1: generic data (voltage, system, Icc, power factor, length, cable, temperature).
3. Stage 2: project current Ib, with formula and values.
4. Stage 3: verification criteria.
5. Stage 4: section selection (Iz, resistance, reactance, voltage drop).
6. Stage 5: final checks table and overall result (CUMPLE / NO CUMPLE).
7. Stage 6: conclusion and points to verify.

## Rules
- Numbers: 1 decimal in voltages and percentages; 2 significant figures in currents; exact values for mm².
- Missing data is written as "Pendiente". No signatures.
- Never recompute values in the MC. It reads them from the same calculation as the JSON.
- Do not generate PDF or Word.

## Runtime
The code is a Python package from `engine/` (`epc_calc`). In a repository checkout set `PYTHONPATH=engine/calc/src` (use `;` as separator on Windows) or run `pip install -e engine/<area>`; in an installed plugin set `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/lib"`. Run modules with `python -m <module>`.
