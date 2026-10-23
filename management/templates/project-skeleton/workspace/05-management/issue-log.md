# issue-log.md — Registro único de incidencias

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-12 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Concentrar en un solo registro todo lo que frena o amenaza el trabajo hoy: bloqueos, pendientes, información pendiente del cliente, preguntas de obra e incidencias. Reemplaza los registros dispersos `BLQ`, `PND`, `INF` y `PA` conservando sus IDs.

## 2. Alcance

Cualquier asunto abierto con responsable y fecha. Los riesgos futuros siguen en el registro de riesgos; cuando un riesgo se materializa se abre aquí una incidencia que lo cita.

## 3. Forma de utilización

1. Se registra con `registrar incidencia` (Claude asigna ID y pide responsable, fecha y tipo).
2. El tipo conserva el prefijo histórico: `BLQ` bloqueo, `PND` pendiente, `INF` información del cliente, `PA` punto de acción, `INC` incidencia.
3. Cada asunto se cierra con evidencia; los vencidos aparecen en `estado del proyecto`.

## 4. Estructura recomendada

ID, tipo, descripción, origen, impacto (paquete / fecha), responsable, fecha de apertura, fecha comprometida, estado (`ABIERTO`, `EN CURSO`, `CERRADO`), cierre con evidencia.

## 5. Ejemplos (ilustrativos)

`EJ-INF-007 | INF | Falta plano de arquitectura | PQ-03 | Cliente | 2026-10-20 | ABIERTO`.

## 6. Buenas prácticas

- Sin responsable ni fecha no se registra.
- Un asunto = una fila.
- Cerrar con evidencia enlazada.

---

# REGISTRO (completar)

| ID | Tipo | Descripción | Origen | Impacto | Responsable | Apertura | Fecha comprometida | Estado | Cierre / evidencia |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |
