# effort-baseline.md — Línea base de esfuerzo (horas)

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Fijar las horas estimadas por paquete y disciplina, como referencia para controlar el esfuerzo real sin contabilidad de costos. Con ella, el avance se mide en horas ganadas contra horas gastadas.

## 2. Alcance

Horas de ingeniería por paquete `PQ-nn`. No incluye costos monetarios. Se alimenta del plan de paquetes y se compara con el esfuerzo real en `EFFORT-nn`.

## 3. Forma de utilización

1. Se crea al aprobar el plan de paquetes (`aprobar plan de paquetes`).
2. Las horas reales se anotan por paquete al cerrarlo o al informar.
3. Un cambio de alcance aprobado (`rfc`) ajusta la línea base con `DEC` y queda trazado.

## 4. Estructura recomendada

Una fila por paquete: horas estimadas (optimista, probable, pesimista → PERT [complemento]), horas reales acumuladas, % de avance, horas ganadas, desviación.

## 5. Ejemplos (ilustrativos)

`PQ-02 | 40 / 56 / 80 | estimada 58 h | real 32 h | avance 50 % | ganadas 29 h`.

## 6. Buenas prácticas

- Estimar con tres puntos, no con uno.
- No reestimar para ocultar desvíos: usar rfc.
- Las horas reales las informa quien las trabajó.

---

# LÍNEA BASE Y REAL (completar)

| Paquete | Disciplina | Optimista h | Probable h | Pesimista h | Estimada h | Real acumulada h | % avance | Ganadas h | Desvío h |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |
