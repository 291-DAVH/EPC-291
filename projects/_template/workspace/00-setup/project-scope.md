# project-scope.md — Alcance, Exclusiones y Criterios de Aceptación

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Cliente | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Es el **único lugar donde se define qué incluye el proyecto, qué no incluye y cómo se acepta**: el alcance por disciplina (`ALD-nnn`), las exclusiones (`EXC-nnn`) y los criterios de aceptación (`CAC-nnn`). Claude lo arma directamente con `iniciar proyecto`, a partir de la documentación depositada y de `starting-data.md`.

## 2. Alcance

Contiene solo alcance, exclusiones y aceptación. **No contiene** los datos declarados por el usuario (`starting-data.md`: qué se contrata, disciplinas, fases, categorías de entregables, plazo), los objetivos (`goals.md`), los requisitos del cliente (`client-requirements.md`), los parámetros técnicos (`project-information.md`) ni la lista de entregables (`deliverables.md`, LME). Cita esos archivos por ID; no los repite.

## 3. Forma de utilización

1. Claude lo completa en `iniciar proyecto`, antes de presentar el `project-charter.md`. El usuario lo aprueba con `aprobar charter`.
2. Una fila `ALD-nnn` por cada **disciplina declarada** en `starting-data.md`, sección 3. Las demás se eliminan solo con justificación.
3. Cada `ALD-nnn` declara qué incluye cada actividad (**S** suministro, **C** construcción, **M** montaje, **E** ensayos), quién la ejecuta y las exclusiones propias de esa disciplina. Lo que es transversal o no pertenece a una disciplina va en `EXC-nnn`.
4. Cada criterio `CAC-nnn` es **medible o verificable por evidencia** y se traslada a `traceability-matrix.md`.
5. Aprobada la línea base, ninguna fila se cambia sin decisión en `assumptions-and-decisions.md` (o rfc si el cliente ya aprobó). Se conserva el ID y se anota la nueva versión en el historial.
6. Los IDs no se reutilizan. Lo desconocido se registra como `[DEFINIR]` con su `INF-nnn`.

## 4. Estructura

| Sección | Prefijo de ID |
|---|---|
| A. Alcance por disciplina | `ALD-nnn` |
| B. Exclusiones | `EXC-nnn` |
| C. Criterios de aceptación | `CAC-nnn` |

## 5. Ejemplos (ilustrativos, no vinculantes)

| ID | Texto de ejemplo |
|---|---|
| EJ-ALD-001 | Eléctrico: suministro e instalación de tableros y cables de la ampliación; ensayos y puesta en servicio por el Contratista. |
| EJ-EXC-001 | Obra civil mayor y suministro de equipos de proceso: a cargo del cliente. |
| EJ-CAC-001 | SAT: protocolos firmados con resultados dentro de las tolerancias de la norma aplicable. |

## 6. Buenas prácticas

- Las exclusiones son tan importantes como el alcance: evitan reclamos y omisiones.
- Una frase, una idea, un ID.
- Un criterio sin método ni evidencia posible se reescribe o se descarta.
- Sin montos, precios ni condiciones comerciales (`CLAUDE.md`, principio 14).

---

# REGISTRO DEL PROYECTO (completar)

## A. Alcance por disciplina

| ID | Disciplina | Descripción del alcance | S | C | M | E | Responsable (Contratista / Cliente / Tercero) | Exclusiones propias |
|---|---|---|---|---|---|---|---|---|
| ALD-001 | `[DEFINIR]` | `[DEFINIR]` | | | | | | |

Códigos de disciplina: `CAD_standards.md`, sección 5.

## B. Exclusiones

| ID | Elemento excluido | Responsable alternativo | Fuente |
|---|---|---|---|
| EXC-001 | `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` |

## C. Criterios de aceptación

| ID | Tipo (FAT / SAT / Funcional / Protecciones / Ensayo eléctrico / Capacitación / Entrega documental / Puesta en marcha) | Criterio de aceptación | Método y norma de referencia | Evidencia exigida | Fuente | Estado |
|---|---|---|---|---|---|---|
| CAC-001 | FAT | `[DEFINIR]` | | | | PENDING |
| CAC-002 | SAT | `[DEFINIR]` | | | | PENDING |
| CAC-003 | Funcional | `[DEFINIR]` | | | | PENDING |
| CAC-004 | Protecciones | `[DEFINIR]` | | | | PENDING |
| CAC-005 | Ensayo eléctrico | `[DEFINIR]` | | | | PENDING |
| CAC-006 | Capacitación | `[DEFINIR]` | | | | PENDING |
| CAC-007 | Entrega documental | `[DEFINIR]` | | | | PENDING |
| CAC-008 | Puesta en marcha | `[DEFINIR]` | | | | PENDING |

Los ocho tipos son la base; se eliminan, con justificación, los que no apliquen (por ejemplo FAT y SAT en un proyecto de solo pliego).
## D. Historial de cambios

| Versión | Fecha | Cambio | Decisión asociada |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Versión inicial de plantilla | — |
