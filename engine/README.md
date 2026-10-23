# engine

Engineering libraries: pure Python, no web and no Claude dependency. The backend orchestrates them, Claude plugins wrap them (the build copies the packages a plugin needs into its `lib/`), and the future desktop app will embed them.

| Area | Package | Content | Tests |
|---|---|---|---|
| [calc](calc/README.md) | `epc_calc` | LV electrical sizing (AEA 90364 / IEC 60364): demand, protection, cable section, voltage drop, short circuit, earthing; Excel pipeline | 205 |
| [rules](rules/README.md) | `epc_rules` | Rules engine: load `rules.json` per jurisdiction, query, check (PASS / FAIL / not evaluated) | 8 |
| [standards](standards/README.md) | `epc_standards` | Standards pipeline: extract, validate (verbatim-copy guard), promote | 6 |
| [drawing](drawing/README.md) | `epc_drawing` | IEC 60617 symbols, IRAM sheets and title blocks, SLD generator, MLD data | 3 + smoke |
| [documents](documents/README.md) | `epc_documents` | Document and specification verifiers, input converter, CCPM, PM2 exporters | 216 (11 skipped by environment) |
| [jurisdictions](jurisdictions/README.md) | data | Country packs (AR): promoted `rules.json` per standard | - |

## Use
```
# from the repository root, without installing (Windows uses ; as separator)
set PYTHONPATH=engine/calc/src;engine/rules/src;engine/standards/src;engine/drawing/src;engine/documents/src
python -m epc_calc.aea_pipeline input.xlsx

# or install them editable into your environment
pip install -e engine/calc -e engine/rules -e engine/standards -e engine/drawing -e engine/documents
```
Layout of every area: `pyproject.toml`, `src/epc_<area>/`, `tests/`, `README.md` (plus `docs/`, `examples/` where relevant).
Dependencies between areas: `epc_drawing` needs `epc_calc`; the rest are independent. `python tools/ci/run_gate.py` runs every area's tests.
