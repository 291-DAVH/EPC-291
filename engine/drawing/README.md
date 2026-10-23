# epc-drawing

Drawing engine. One package, four subpackages:

| Subpackage | Content | Run |
|---|---|---|
| `epc_drawing.symbols` | IEC 60617 symbol library (SLD/MLD, LV/MV) with catalogs; `library_dir(kind)` | import |
| `epc_drawing.titleblock` | IRAM A0-A4 sheets, custom title blocks, SVG->DXF | `python -m epc_drawing.titleblock.titleblocks_generator` |
| `epc_drawing.sld` | Single-line diagram from the circuits Excel (uses `epc_calc`, symbols and title blocks) | `python -m epc_drawing.sld.sld_paginate default input.xlsx out NAME default default` |
| `epc_drawing.mld` | Multi-line diagram data and templates (generator pending) | - |

Run with `PYTHONPATH=engine/calc/src:engine/drawing/src` (use `;` on Windows) or install both packages (`pip install -e engine/calc -e engine/drawing`).
`SLD_ROTULO_DIR` selects the folder with `input-titleblocks.xlsx` and logos (the generator rewrites that workbook, so point it to a copy).
Examples: `examples/sld/`. Fixtures (reference outputs): `tests/fixtures/`. Symbol build scripts: `tools/symbols/`.
Tests: `python -m unittest discover -s tests` with `PYTHONPATH=src`.
