# traceability-matrix.md — Matriz de Trazabilidad

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Permitir el seguimiento completo de cada requisito desde su origen hasta su implementación y verificación, aplicando la cadena obligatoria:

```text
Objetivo
   ↓
Requisito
   ↓
Criterio de Ingeniería
   ↓
Documento
   ↓
Plano
   ↓
Entregable
```

**Nada debe quedar fuera de esta cadena.** Un requisito sin eslabón es un hallazgo; un documento, plano o entregable sin requisito asociado también.

## 2. Alcance

Incluye todos los requisitos del proyecto, cualquiera sea su origen: cliente (`CR-`), objetivos (`OBJ-`), criterios de aceptación (`CAC-`), normas (`NOR-`), decisiones (`DEC-`), seguridad, operación, mantenimiento, construcción, commissioning, documentación y as-built.

## 3. Forma de utilización

1. **Alta:** cada objetivo de `goals.md` y cada requisito de `client-requirements.md` genera una o más filas en la matriz principal. Un requisito se descompone en varias filas cuando se implementa en diferentes documentos o fases.
2. **ID:** `REQ-<CAT>-nnn` correlativo por categoría, sin reutilizar. Categorías y códigos en la tabla 4.1.
3. **Avance:** al redactar o entregar un documento o plano, se completan las columnas *Documento*, *Plano* y *Entregable* y se actualiza el *Estado*.
4. **Cadena extendida:** la tabla B vincula cada requisito con su objetivo, criterio de ingeniería, decisión y evidencia. Completarla para todo requisito en estado `IMPLEMENTED` o `VERIFIED`.
5. **Verificación:** `VERIFIED` solo se asigna con evidencia de verificación identificable (informe, cálculo revisado, protocolo, inspección) y, preferentemente, por una persona o pasada distinta de la que implementó.
6. **No aplica:** `NOT_APPLICABLE` exige justificación y una decisión `DEC-nnn`.
7. **Auditoría:** cada auditoría comprueba que cada requisito: **existe, está documentado, tiene evidencia, está asociado a entregables y está correctamente verificado** (`project-audit.md`, auditoría A5).

## 4. Estructura recomendada

### 4.1 Categorías

| Código | Categoría | Contenido típico |
|---|---|---|
| `CLI` | Cliente | Requisitos contractuales o generales del cliente que no encajan en otra categoría |
| `SEG` | Seguridad | Seguridad de personas e instalaciones, arco, bloqueo y etiquetado, protecciones |
| `ING` | Ingeniería | Criterios de diseño, normas, cálculos, equipos |
| `OPE` | Operación | Continuidad, modos de operación, ventanas de parada |
| `MAN` | Mantenimiento | Accesibilidad, repuestos, manuales |
| `CON` | Construcción | Métodos, inspecciones, tolerancias, interferencias |
| `COM` | COMMISSIONING | Pruebas, protocolos, energización, puesta en servicio |
| `DOC` | Documentación | Nomenclatura, formatos, CAD, entregables documentales |
| `ASB` | As-Built | Documentación final conforme a obra, dossier |

### 4.2 Estados

| Estado | Definición | Condición para asignarlo |
|---|---|---|
| `PENDING` | Identificado, sin trabajo iniciado | — |
| `IN_progress` | En desarrollo | Existe documento o plano en elaboración |
| `IMPLEMENTED` | Implementado en documentos / planos / obra | Documento (y plano si aplica) generado, en `FOR_REVIEW` o posterior, con evidencia localizable. Aplica ya con el documento en `FOR_REVIEW` (sin revisar); la verificación queda en «—» hasta `AUDITED` |
| `VERIFIED` | Implementación verificada con evidencia | Evidencia de verificación registrada en tabla B |
| `NON_COMPLIANT` | No cumple | Se genera hallazgo y plan de acción o desvío (`DEC-nnn`) |
| `NOT_APPLICABLE` | No aplica al proyecto | Justificación y decisión registradas |

### 4.3 Reglas de consistencia

- `IMPLEMENTED` o `VERIFIED` sin *Documento* es inválido.
- `VERIFIED` sin entrada en la tabla B (evidencia de verificación) es inválido.
- En la tabla B, la columna *Evidencia de verificación* lleva «—» mientras el requisito está `IMPLEMENTED` y el documento no ha sido auditado; solo se completa al pasar a `VERIFIED` (tras `AUDITED`).
- Los códigos de *Documento*, *Plano* y *Entregable* deben existir en `deliverables.md` (con revisión vigente).
- Un requisito `NON_COMPLIANT` abierto impide cerrar el proyecto.
- Una modificación posterior a una auditoría que afecte un requisito `VERIFIED` lo devuelve a `IMPLEMENTED` hasta re-verificar.

## 5. Ejemplos (ilustrativos, no vinculantes)

**Tabla A (matriz principal)**

| ID | Categoria | Requisito | Fuente | Documento | Plano | Entregable | Estado |
|---|---|---|---|---|---|---|---|
| EJ-REQ-ING-001 | Ingeniería | Verificar el poder de corte de las celdas de MT frente al nivel de cortocircuito. | EJ-OBJ-TEC-001; ENG-MT-003 | ACM01-E-MC-002 Rev 00.2 | ACM01-E-PL-110 Rev 00.2 | EJ-ENT-014 | VERIFIED |
| EJ-REQ-SEG-001 | Seguridad | Enclavamientos entre seccionador de puesta a tierra e interruptor. | EJ-CR-SEG-002; ENG-PRO-006 | ACM01-E-LI-004 Rev 00.0 | ACM01-E-DG-020 Rev 00.0 | EJ-ENT-031 | IMPLEMENTED |
| EJ-REQ-DOC-001 | Documentación | Codificación de documentos según el estándar del cliente. | EJ-CR-DOC-002 | ACM01-G-PC-001 Rev 00.0 | — | EJ-ENT-002 | VERIFIED |
| EJ-REQ-COM-001 | COMMISSIONING | Medición de resistencia de aislación de cables de MT. | ENG-PRE-004; ENG-PRE-005 | ACM01-E-PT-003 Rev 00.0 | — | EJ-ENT-058 | PENDING |

**Tabla B (cadena extendida)**

| ID | Objetivo | Criterio de ingeniería | Decisión / supuesto | Evidencia de implementación | Evidencia de verificación | Verificado por | Fecha |
|---|---|---|---|---|---|---|---|
| EJ-REQ-ING-001 | EJ-OBJ-TEC-001 | ENG-MT-003 | EJ-SUP-003 | MC-002 §6.2, tabla 4 | Informe de auditoría AUD-01, check A3-07 | Auditor Técnico | 2026-12-02 |
| EJ-REQ-SEG-001 | EJ-OBJ-TEC-002 | ENG-PRO-006 | — | LI-004 §3 (documento en `FOR_REVIEW`) | — (hasta `AUDITED`) | — | — |

## 6. Buenas prácticas

- Una fila = un requisito verificable. Si no puede verificarse, se reformula.
- Referenciar documentos con código y revisión.
- No cerrar un requisito por ausencia de comentarios: se cierra por evidencia.
- Actualizar la matriz en el mismo acto de entregar un documento.
- Revisar huérfanos (objetivos, documentos, planos, entregables sin requisito) en cada auditoría.
- Usar los mismos IDs en memorias, planos y protocolos para poder buscarlos.

---

# MATRIZ DEL PROYECTO (completar)

## A. Matriz principal

| ID | Categoria | Requisito | Fuente | Documento | Plano | Entregable | Estado |
|---|---|---|---|---|---|---|---|
| REQ-CLI-001 | Cliente | `[DEFINIR]` | | | | | PENDING |
| REQ-SEG-001 | Seguridad | `[DEFINIR]` | | | | | PENDING |
| REQ-ING-001 | Ingeniería | `[DEFINIR]` | | | | | PENDING |
| REQ-OPE-001 | Operación | `[DEFINIR]` | | | | | PENDING |
| REQ-MAN-001 | Mantenimiento | `[DEFINIR]` | | | | | PENDING |
| REQ-CON-001 | Construcción | `[DEFINIR]` | | | | | PENDING |
| REQ-COM-001 | COMMISSIONING | `[DEFINIR]` | | | | | PENDING |
| REQ-DOC-001 | Documentación | `[DEFINIR]` | | | | | PENDING |
| REQ-ASB-001 | As-Built | `[DEFINIR]` | | | | | PENDING |

*(Las filas anteriores son marcadores de posición: reemplazar por los requisitos reales y agregar las filas necesarias.)*

## B. Cadena de trazabilidad extendida

| ID | Objetivo | Criterio de ingeniería | Decisión / supuesto | Evidencia de implementación | Evidencia de verificación | Verificado por | Fecha |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## B2. Cumplimiento de criterios de ingeniería (ENG)

Cada criterio de `engineering-standards.md` con *Aplica* `SÍ` o `PARCIAL` tiene una fila: documento, sección y evidencia donde se cumple. Un criterio aplicable sin fila o sin evidencia es un hallazgo de auditoría (A3). Los criterios `NO` se justifican en la columna *Aplica* con la decisión (`DEC-nnn`).

| Criterio ENG | Documento y sección que lo cumple | Evidencia | Estado |
|---|---|---|---|
| | | | |

## C. Control de cobertura (actualizar en cada auditoría)

| Categoría | PENDING | IN_progress | IMPLEMENTED | VERIFIED | NON_COMPLIANT | NOT_APPLICABLE | Total |
|---|---|---|---|---|---|---|---|
| Cliente | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Seguridad | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ingeniería | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Operación | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mantenimiento | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Construcción | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| COMMISSIONING | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Documentación | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| As-Built | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## D. Control de huérfanos (verificar en cada auditoría)

| Control | Resultado | Detalle |
|---|---|---|
| Objetivos (`OBJ-`) sin requisito | | |
| Requisitos del cliente (`CR-`) sin fila en la matriz | | |
| Requisitos sin criterio de ingeniería ni justificación | | |
| Requisitos sin documento | | |
| Requisitos que exigen plano y no lo tienen | | |
| Requisitos sin entregable | | |
| Documentos, planos o entregables de `deliverables.md` sin requisito asociado | | |
| IDs duplicados o referencias inexistentes | | |

## E. Historial de cambios de la matriz

| Versión | Fecha | Cambio | Responsable |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Versión de plantilla | |
