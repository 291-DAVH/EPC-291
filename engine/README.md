# engine

Engineering libraries: pure Python, no web and no Claude dependency. The backend orchestrates them, Claude plugins wrap them (the build copies the packages a plugin needs into its `lib/`), and the future desktop app will embed them.

| Area | Package | Content | Tests |
|---|---|---|---|
| [calc](calc/README.md) | `epc_calc` | LV electrical sizing (AEA 90364 / IEC 60364): demand, protection, cable section, voltage drop, short circuit, earthing; Excel pipeline; standard solutions (which symbols build each circuit) and automatic differential groups | 205 |
| [rules](rules/README.md) | `epc_rules` | Rules engine: load `rules.json` per jurisdiction, query, check (PASS / FAIL / not evaluated) | 8 |
| [standards](standards/README.md) | `epc_standards` | Standards pipeline: extract, validate (verbatim-copy guard), promote | 6 |
| [dxf](dxf/README.md) | `epc_dxf` | Catalog of DXF layers (the MASTER edits it), the deliverable service (SVG in development to DXF, semantic roles) and the delivery package | 9 |
| [symbols](symbols/README.md) | `epc_symbols` | IEC 60617 symbol library (SVG and DXF blocks, catalogs) for single-line and multi-line diagrams | 3 |
| [titleblock](titleblock/README.md) | `epc_titleblock` | IRAM A0-A4 sheets as a service: a JSON request (formats, fields, logos) in, the filled sheets out | 8 |
| [sld](sld/README.md) | `epc_sld` | Single-line diagram generator: it draws what `epc_calc` calculated | 2 + smoke |
| [mld](mld/README.md) | `epc_mld` | Multi-line diagram generator: each line expanded into its conductors | 2 |
| [plan](plan/README.md) | `epc_plan` | Plan-drawing engine: graph, tags, circuit routes (moment method), schedules, DXF | 56 |
| [drawing](drawing/README.md) | `epc_drawing` | Board design (calculation + SLD + MLD in one go) and the exports: PDF, stamped DXF, report and transmittal PDF | 17 |
| [documents](documents/README.md) | `epc_documents` | Document and specification verifiers, input converter, CCPM, PM2 exporters | 216 (11 skipped by environment) |
| [jurisdictions](jurisdictions/README.md) | data | Country packs (AR): promoted `rules.json` per standard | - |

## Use
```
# from the repository root, without installing (Windows uses ; as separator)
set PYTHONPATH=engine/calc/src;engine/rules/src;engine/standards/src;engine/dxf/src;engine/symbols/src;engine/titleblock/src;engine/plan/src;engine/sld/src;engine/mld/src;engine/drawing/src;engine/documents/src
python -m epc_calc.aea_pipeline input.xlsx

# or install them editable into your environment
pip install -e engine/calc -e engine/rules -e engine/standards -e engine/dxf -e engine/symbols -e engine/titleblock -e engine/plan -e engine/sld -e engine/mld -e engine/drawing -e engine/documents
```
Layout of every area: `pyproject.toml`, `src/epc_<area>/`, `tests/`, `README.md` (plus `docs/`, `examples/` where relevant).
Dependencies between areas (enforced by the `engine-layers` contract and listed in `docs/architecture/DEPENDENCIAS.md`): `epc_drawing` > `epc_mld`, `epc_sld` > `epc_titleblock`, `epc_symbols`, `epc_plan`, `epc_calc` > `epc_dxf`; `epc_standards` needs `epc_calc`; the rest are independent. Each area installs and is updated on its own. `python tools/ci/run_gate.py` runs every area's tests.
