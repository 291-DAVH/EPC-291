# Generar listado — `$ARGUMENTS`

Los listados son documentos de la **etapa 7** del grafo de dependencias (M5): requieren que los planos/diagramas (unifilares, P&IDs, planos de distribución) y sus insumos de dibujo (`_DIN_`) estén en estado `REVIEWED` o `DRAWN`.

## Antes de generar (puerta de preparación)

Verificar que están `REVIEWED`:
- **LC (cables)**: unifilar `DG`, multifilar `MLD`, insumos de distribución de bandejas.
- **LE (equipos)**: unifilar `DG`, memoria descriptiva `MD`, datasheet/hoja técnica de cada equipo (`ET`).
- **LM (materiales)**: insumos de planos de montaje, especificaciones técnicas de materiales (`ET`).
- **LI (instrumentos)**: P&ID, hoja de datos de instrumentos (`ET`), lista I/O.

Si alguno de los anteriores no está `REVIEWED`, no generar: informar cuál falta y proponer desarrollarlo primero.

## Estructura del listado

### LC — Listado de cables

| ID | Circuito | Origen (tablero/bornes) | Destino | Tipo de cable | Sección mm² | N° conductores | Longitud (m) | Bandeja / cañería | Observaciones |
|---|---|---|---|---|---|---|---|---|---|
| CAB-001 | | | | | | | | | |

Fuente de cada columna:
- **Circuito, Origen, Destino**: unifilar + multifilar.
- **Tipo y sección**: memoria de cálculo de conductores (etapa 2 del grafo).
- **Longitud**: insumos de planos de distribución (`_DIN_`); marcar `[DEFINIR]` si el plano no está dibujado.
- **Bandeja / cañería**: insumos de distribución de bandejas.

### LE — Listado de equipos

| Código | Descripción | Disciplina | Tablero/Panel | Potencia (kW) | Tensión (V) | Ubicación | Datasheet | Estado |
|---|---|---|---|---|---|---|---|---|
| EQ-001 | | | | | | | | |

Fuente: unifilar, memoria descriptiva, datasheets.

### LM — Listado de materiales

| Ítem | Descripción | Especificación / Norma | Unidad | Cantidad | Observaciones |
|---|---|---|---|---|---|
| | | | | | |

Fuente: planos de montaje e instalación, especificaciones técnicas.

### LI — Listado de instrumentos

| Tag | Descripción | Servicio | P&ID ref. | Tipo | Rango | Señal | Alimentación | Ubicación | Datasheet |
|---|---|---|---|---|---|---|---|---|---|
| FT-001 | | | | | | 4-20 mA | | | |

Fuente: P&IDs, hojas de datos de instrumentos, lista I/O.

## Reglas de completitud

- Toda fila con dato no disponible lleva `[DEFINIR]` con el `INF-nnn` correspondiente.
- Cantidades sin plano terminado llevan `[VERIFICAR]`.
- El listado no debe tener filas con datos inventados: si no hay fuente identificable, la celda queda `[DEFINIR]`.
- Un listado con más del 20 % de filas `[DEFINIR]` en columnas críticas (tipo, sección, longitud para LC; tag, servicio para LI) **no se envía a revisión**: reportar el bloqueo y listar los datos faltantes.

## Al terminar

1. Correr `document_verifier.py`.
2. Actualizar `deliverables.md` y `traceability-matrix.md`.
3. Ejecutar el skill `/autocontrol-paquete PQ-nn`.
