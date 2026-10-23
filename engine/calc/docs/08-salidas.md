# 08 · Salidas

## Qué resuelve

Entrega los resultados en formatos que consumen otras herramientas y el personal de proyecto.

## Pasos

1. **JSON de cálculo** (`<proyecto>_calculo.json` o el nombre indicado con `-o`). Contiene, por circuito, In, Ib, icu, S, ΔU y el dispositivo. Es el contrato con `sld-generator` y no cambia de forma.
2. **Memoria de Cálculo** del alimentador principal (`_MC.md`): objeto, marco normativo, datos de entrada, cinco etapas de verificación y resultado. Sale en Markdown, sin PDF.
3. **Síntesis de Proyecto** del alimentador principal (`_SP.md`): una página con requisito normativo y dato técnico, con hasta tres observaciones.
4. **Avisos** en pantalla: circuitos sin sección que cumpla, Icc mínima insuficiente, icu fuera de serie, combinaciones de instalación no tabuladas.
5. **Alimentador principal:** primer circuito sin padre con KIND `mccb`, o el que indique `--alimentador TAG`.

## Comando

```
python -B library/calculations/aea_pipeline.py src/input_motor_AEA_V2.xlsx
```

Opciones: `-o` (JSON de salida), `--alimentador TAG`, `--margen-iz`, `--eta-motores`, `--temp-c`, `--k-magnetico`.

## Módulos

`aea_export.export_calculation`, `aea_export.validate_calculation`, `aea_feeder_report.generar_documentos`.
