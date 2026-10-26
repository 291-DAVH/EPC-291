# epc-sld

Single-line diagram of a board on IRAM sheets (SVG and DXF per sheet, plus the circuit table). It only draws: the calculation (`SLD_CALC_JSON`, `SLD_CALC_DETAIL`) and the board figures (`SLD_FIGURES_JSON`) come from `epc_calc`. Use it through `epc_drawing.board_design`.
Needs `epc_calc`, `epc_symbols` and `epc_titleblock`. Example workbook: `examples/sld/`.
