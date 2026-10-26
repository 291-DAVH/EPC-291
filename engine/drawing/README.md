# epc-drawing

Board design in one go (`python -m epc_drawing.board_design`: calculation with the project's design criteria, single-line, multi-line, memo and summary) and the exports: DXF to PDF, stamped DXF, report and transmittal PDF.
The diagrams themselves live in `epc_sld`, `epc_mld`, `epc_symbols` and `epc_titleblock`; the plan editor engine in `epc_plan`.
Tests: `tests/` (golden outputs of the drawings in `tests/golden/`).
