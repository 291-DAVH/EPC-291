# audit-register.md — Registro de Auditorías, Avance y Hallazgos

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 1.0 |
| Fecha | 2026-10-07 |
| Responsable | Project Engineer (gestor del proyecto) |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Llevar en un solo lugar, fuera de la guía de auditoría, el **registro de los informes de avance, de las auditorías y de los hallazgos abiertos** del proyecto. `project-audit.md` es una guía que no se edita; este archivo es el registro vivo.

## 2. Alcance

Todos los informes del auditor: `AUD-nn` (auditorías de entrega, re-entrega, cierre y re-auditorías parciales) y `progress-nn` (informes de avance), y el seguimiento de cada hallazgo `HAL-nn-nnn` hasta su cierre verificado.

## 3. Forma de utilización

1. **Ubicación.** Este archivo vive en `90-management/audit-register.md`, tanto en la plantilla maestra como en el proyecto (`CLAUDE.md`, 8.1 (copia de la plantilla, `M3`)).
2. **Quién lo escribe.** El **gestor del proyecto** (Claude en el rol de Project Manager), después de recibir cada informe. El auditor escribe solamente su informe y no modifica este archivo (`project-audit.md`, 3.2, paso 7).
3. **Nombres de los informes.** `AUD-nn_YYYYMMDD.md` y `progress-nn_YYYYMMDD.md`, en la misma carpeta que este registro. La numeración `nn` es correlativa por tipo y no se reutiliza; la fecha es la de emisión del informe. Una re-auditoría parcial lleva el número siguiente (`AUD-nn+1`) y cita el informe de origen.
4. **Cuándo.** Al recibir un informe, el mismo día: una fila en la tabla A o B y una fila en la tabla C por cada hallazgo abierto.
5. **Hallazgos.** El estado de cada hallazgo se actualiza con la evidencia de cierre; solo el auditor lo pasa a `VERIFIED_CLOSED` (con su verificación en un informe posterior).
6. **No se borra nada:** las filas cerradas se conservan.

## 4. Estructura recomendada

Tabla A (informes de avance) → tabla B (auditorías) → tabla C (hallazgos). Los estados de hallazgo son `OPEN`, `IN_progress`, `CLOSED` (cerrado por el gestor con evidencia) y `VERIFIED_CLOSED` (verificado por el auditor).

## 5. Ejemplos (ilustrativos)

| ID | Fecha | Estado del proyecto | Avance global verificado | Bloqueos | Informe (ruta) |
|---|---|---|---|---|---|
| EJ-progress-01 | 2026-11-20 | `ENGINEERING` | 35 % | 1 | `90-management/progress/progress-01_20261120.md` |

## 6. Buenas prácticas

- Registrar el informe el mismo día en que se recibe.
- Cada hallazgo cerrado cita la evidencia por código y revisión.
- No resumir aquí el contenido del informe: se cita su ruta.

---

# REGISTRO DE INFORMES DE AVANCE (completar)

| ID | Fecha | Estado del proyecto | Avance global verificado | Bloqueos | Informe (ruta) |
|---|---|---|---|---|---|
| progress-01 | | | | | `90-management/progress/progress-01_YYYYMMDD.md` |

# REGISTRO DE AUDITORÍAS (completar)

| ID | Fecha | Tipo | Entrega objetivo | Alcance | Veredicto | CRITICAL | MAJOR | MINOR | OBS | Estado de cierre de hallazgos | Aprobación humana | Informe (ruta) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUD-01 | | | | | | | | | | | | `04-audit/audit-reports/AUD-01_YYYYMMDD.md` |

# REGISTRO DE HALLAZGOS ABIERTOS (completar)

| ID | Auditoría | Severidad | Check | Descripción | Acción requerida | Responsable | Fecha límite | Estado (OPEN / IN_progress / CLOSED / VERIFIED_CLOSED) | Evidencia de cierre |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |
