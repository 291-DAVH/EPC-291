# 01 · Datos de entrada

## Qué resuelve

Organiza la información del tablero y de cada circuito en el Excel que lee el motor.

## Entradas

Libro Excel con dos hojas obligatorias: **TABLERO** y **CIRCUITOS**. La plantilla recomendada es `src/input_motor_AEA_V2.xlsx`.

## Pasos

1. **Datos del tablero (hoja TABLERO).** Complete tensión de línea (`TENSION_V`), esquema de puesta a tierra (`SISTEMA`), Icc en barras (`ICC_KA`) y factor de potencia por defecto (`FP_DEFAULT`).
2. **Un circuito por fila (hoja CIRCUITOS).** `TAG`, `DESCRIPCION`, `DESTINO`, `CARGA` y `UNIDAD_CARGA` son obligatorios.
3. **Jerarquía.** Si un circuito cuelga de otro (por ejemplo, tomas bajo un RCCB), escriba en `PARENT_TAG` el TAG del padre. Si la carga del padre está vacía, el motor suma la de sus hijos.
4. **Unidades de carga.** A, W, kW, MW, VA, kVA, MVA o HP. Se convierten todas a corriente en el paso 2.
5. **Tendido.** `LONGITUD_m` en metros. Si se omite, la caída de tensión es cero.
6. **Instalación.** `MATERIAL`, `AISLACION`, `CLASE`, `METODO`, `N_TERNAS`, `AGRUP_CIRCUITOS`, temperaturas y resistividad del terreno. Las celdas vacías toman el valor por defecto (Cobre, PVC, método B1, clase 2, 40 °C). Ver [04 · Capacidad de conducción](04-capacidad-de-conduccion.md).
7. **Protección.** `KIND`: `auto`, `mcb`, `mccb`, `rcbo` o `rccb`. Con `auto` el motor elige MCB hasta 63 A y MCCB por encima.
8. **Verificación de la carga.** Revise avisos al ejecutar: un TAG duplicado, un PARENT_TAG inexistente o un ciclo detienen el cálculo.

## Criterio de aceptación

- No hay TAG repetidos ni PARENT_TAG inexistentes.
- Cada circuito tiene carga o hijos.

## Módulos

`aea_pipeline.load_input`, `aea_pipeline.leer_xlsx`, `aea_ampacity.parametros`.
