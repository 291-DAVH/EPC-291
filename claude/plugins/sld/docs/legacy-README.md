# sld-generator

Carpeta de trabajo del generador de diagramas unifilares (SLD) de tablero.

## Estructura

- `src/`: código fuente de los scripts (`sld_generator.py`, `sld_paginate.py`, `vendor_loader.py`, `make_variants.py`) y los Excel de entrada:
  - `input_for_sld_V1.xlsx`: circuitos del tablero (hojas CIRCUITOS).
  - `input-titleblocks.xlsx`: datos del rótulo IRAM (una fila por lámina; lo usa el plugin iram-titleblock-plugin).
- `plugin/sld-generator/`: manifiesto del plugin, README y skills (`sld-generator`).
- `plugin/sld-generator.plugin`: paquete ZIP del plugin, generado desde `src/` + `plugin/`.
- `assets/`: PDFs de SLD de referencia.
- `test/`: salidas de prueba (SVG, PDF, JSON de cálculo y capturas de control).
- `test/entradas/`: planillas Excel de entrada para las pruebas.
- `vendor/`: plugins de los que depende (`elec-calc-generator`, `iec60617-symbol-generator`, `iram-titleblock-plugin`).
