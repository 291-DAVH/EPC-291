# goals.md — Objetivos, Alcance y Criterios de Éxito

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

Registrar de forma única y verificable **para qué existe el proyecto**, bajo qué restricciones se ejecuta y cómo se sabrá que fue exitoso. Es el punto de partida de la cadena de trazabilidad: *Objetivo → Requisito → Criterio de Ingeniería → Documento → Plano → Entregable*.

## 2. Alcance

Cubre objetivos generales, técnicos y operativos; restricciones; criterios de éxito. No contiene alcance ni exclusiones (van en `project-scope.md`), requisitos detallados del cliente (`client-requirements.md`) ni datos técnicos (`project-information.md`).

## 3. Forma de utilización

1. Claude lo completa en `iniciar proyecto` y el usuario lo aprueba con el charter (`aprobar charter`); se valida con el cliente o con el responsable del contrato.
2. Asignar un ID único a cada objetivo, restricción y criterio de éxito. Los IDs no se reutilizan.
3. Todo objetivo debe derivar en al menos un requisito de `traceability-matrix.md`.
4. Los cambios se hacen por decisión registrada en `assumptions-and-decisions.md`; se conserva el ID y se anota la nueva versión.
5. Cada **criterio de éxito debe ser medible** (cuantificable o verificable por evidencia).

## 4. Estructura recomendada

| Sección | Prefijo de ID |
|---|---|
| Objetivos generales | `OBJ-GEN-nnn` |
| Objetivos técnicos | `OBJ-TEC-nnn` |
| Objetivos operativos | `OBJ-OPE-nnn` |
| Restricciones | `RES-nnn` |
| Criterios de éxito | `CRI-nnn` |

## 5. Ejemplos (ilustrativos, no vinculantes)

| ID | Texto de ejemplo |
|---|---|
| EJ-OBJ-GEN-001 | Adecuar la alimentación eléctrica de la planta para la ampliación de la línea de producción. |
| EJ-OBJ-TEC-001 | Garantizar selectividad y protección de las instalaciones afectadas según criterios IEC aplicables. |
| EJ-OBJ-OPE-001 | Ejecutar los trabajos sin interrumpir la producción fuera de las ventanas de parada acordadas. |
| EJ-RES-001 | Corte de energía permitido únicamente en parada programada informada por el cliente. |
| EJ-CRI-001 | 100 % de los requisitos de la matriz de trazabilidad en estado VERIFIED o NOT_APPLICABLE justificado al cierre. |

## 6. Buenas prácticas

- Redactar objetivos como resultados, no como actividades ("Alimentar X con Y", no "Hacer planos").
- Una frase, una idea, un ID.
- Criterios de éxito sin métrica ni evidencia posible deben reescribirse o descartarse.
- Revisar este archivo al pasar a cada nuevo estado del proyecto.

---

# REGISTRO DEL PROYECTO (completar)

## A. Objetivos generales

| ID | Objetivo | Origen (contrato / cliente / interno) | Estado |
|---|---|---|---|
| OBJ-GEN-001 | `[DEFINIR]` | `[DEFINIR]` | OPEN |

## B. Objetivos técnicos

| ID | Objetivo técnico | Norma / criterio asociado | Estado |
|---|---|---|---|
| OBJ-TEC-001 | `[DEFINIR]` | `[DEFINIR]` | OPEN |

## C. Objetivos operativos

| ID | Objetivo operativo | Condición de operación / mantenimiento | Estado |
|---|---|---|---|
| OBJ-OPE-001 | `[DEFINIR]` | `[DEFINIR]` | OPEN |

## D. Restricciones

| ID | Tipo (técnica, plazo, económica, operativa, normativa, ambiental) | Descripción | Fuente |
|---|---|---|---|
| RES-001 | `[DEFINIR]` | `[DEFINIR]` | `[DEFINIR]` |

## E. Criterios de éxito

| ID | Criterio medible | Método de verificación | Objetivo asociado | Estado |
|---|---|---|---|---|
| CRI-001 | `[DEFINIR]` | `[DEFINIR]` | OBJ-xxx-nnn | OPEN |

## F. Historial de cambios

| Versión | Fecha | Cambio | Decisión asociada |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Versión inicial de plantilla | — |
