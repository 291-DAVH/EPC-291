# client-requirements.md — Requisitos Específicos del Cliente

| Campo | Valor |
|---|---|
| Cliente | `[DEFINIR]` |
| Proyecto | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Registrar de forma estructurada **todo requisito impuesto por el cliente** (contractual, técnico, documental, CAD, constructivo, operativo, de mantenimiento, de seguridad, corporativo o restricción especial), con su fuente y su método de verificación, para que ninguno se pierda y todos puedan trazarse hasta su evidencia.

## 2. Alcance

Contiene requisitos que provienen del cliente o de sus normas corporativas. Los requisitos de normas obligatorias se registran en `project-information.md` (NOR) y `engineering-standards.md` (ENG); los internos de la empresa, en `DOCUMENT_RULES.md` y `CAD_standards.md`. Aquí se registra también la **tabla de correspondencia** cuando el cliente impone un estándar distinto.

## 3. Forma de utilización

1. Registrar un requisito por fila, con ID `CR-<TIPO>-nnn`. Tipos: `TEC`, `DOC`, `CAD`, `CON`, `OPE`, `MAN`, `SEG`, `COR`, `RES`.
2. Citar la **fuente exacta**: documento del cliente, código, revisión y cláusula.
3. Analizar cada requisito (estado `ANALYZED`) y clasificarlo: aceptado, requiere aclaración, o desvío.
4. Llevar cada requisito a `traceability-matrix.md` como una o más filas `REQ-<CAT>-nnn` (la columna *Fuente* referencia el `CR-`). Un `CR-` sin fila en la matriz es un hallazgo de auditoría.
5. Los requisitos ambiguos o inverificables se reformulan con el cliente (rfi) y quedan en `CLARIFICATION` hasta resolverse.
6. Los conflictos con normas, entre requisitos o con decisiones se registran en la sección de conflictos y se gestionan con `DEC-nnn`.
7. En clientes recurrentes, los requisitos estables se heredan del proyecto anterior y se **revalidan** (ver `CLAUDE.md`, sección 10).

## 4. Estructura recomendada

| Tipo | Prefijo | Categoría equivalente en matriz |
|---|---|---|
| Requisitos técnicos | `CR-TEC-nnn` | Ingeniería |
| Requisitos documentales | `CR-DOC-nnn` | Documentación |
| Requisitos CAD | `CR-CAD-nnn` | Documentación |
| Requisitos constructivos | `CR-CON-nnn` | Construcción |
| Requisitos operativos | `CR-OPE-nnn` | Operación |
| Requisitos de mantenimiento | `CR-MAN-nnn` | Mantenimiento |
| Requisitos de seguridad | `CR-SEG-nnn` | Seguridad |
| Estándares corporativos | `CR-COR-nnn` | Cliente / según contenido |
| Restricciones especiales | `CR-RES-nnn` | Cliente / según contenido |

Estados de análisis: `RECEIVED` (recibido), `ANALYZED` (analizado), `ACCEPTED` (aceptado), `CLARIFICATION` (pendiente de aclaración), `DEVIATION` (desvío propuesto o aprobado), `REJECTED` (no aplicable al proyecto, con motivo).

Prioridad: `OBLIGATORIO` (debe cumplirse) o `DESEABLE` (se cumple si es viable, con justificación si no).

## 5. Ejemplos (ilustrativos, no vinculantes)

| ID | Requisito | Fuente | Prioridad | Verificación | Estado |
|---|---|---|---|---|---|
| EJ-CR-TEC-001 | Todos los tableros de BT deberán incluir reserva de espacio para ampliación futura. | Esp. cliente `XX-ES-010` Rev 2, cl. 4.3 | OBLIGATORIO | Inspección de plano de tablero y especificación | ACCEPTED |
| EJ-CR-DOC-002 | Los documentos se codificarán con el esquema `AAA-BBB-CCC-NNNN` del cliente. | Procedimiento documental cliente, cl. 2 | OBLIGATORIO | Revisión de nomenclatura | ACCEPTED |
| EJ-CR-SEG-001 | Todo trabajo en tableros energizados requerirá permiso de trabajo del cliente. | Reglamento de seguridad del cliente, cl. 7 | OBLIGATORIO | Procedimientos de obra y commissioning | ACCEPTED |

## 6. Buenas prácticas

- Copiar el texto del requisito tal como lo escribió el cliente; la interpretación va en otra columna.
- Si el cliente envía un documento nuevo, revisarlo completo y registrar requisitos nuevos, modificados o eliminados.
- Resolver los conflictos y ambigüedades **antes** de iniciar la ingeniería de detalle.
- No “cumplir en espíritu”: cada requisito debe tener evidencia.
- Registrar los desvíos solicitados por el cliente durante la ejecución (cambios de alcance) como decisiones.

---

# REGISTRO DEL CLIENTE (completar)

## A. Documentos del cliente de referencia

| Código | Título | Revisión | Fecha | Aplicabilidad |
|---|---|---|---|---|
| `[DEFINIR]` | | | | |

## B. Requisitos técnicos (`CR-TEC`)

| ID | Requisito | Fuente (doc., rev., cláusula) | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-TEC-001 | `[DEFINIR]` | | | | RECEIVED | |

## C. Requisitos documentales (`CR-DOC`)

| ID | Requisito | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-DOC-001 | | | | | | |

Tabla de correspondencia de nomenclatura (si el cliente tiene la suya):

| Elemento | Esquema del cliente | Esquema del framework | Regla de conversión |
|---|---|---|---|
| Código de documento (sin revisión) | | `[PRY]-[DISC]-[TIPO]-[NNN]` | |
| Identificador completo / nombre de archivo | | `<código>_Rev<R>` / `<código>_Rev<R>.<ext>` | Ver `DOCUMENT_RULES.md`, 8.1 |
| Revisión | | `00.n internas / 00 en toda entrega / 01 as-built / 02, 03…` | El cliente siempre recibe Rev 00 (ver `DOCUMENT_RULES.md`, sección 9) |

## D. Requisitos CAD (`CR-CAD`)

| ID | Requisito (capas, rótulo, formato, versión del software, estilos) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-CAD-001 | | | | | | |

## E. Requisitos constructivos (`CR-CON`)

| ID | Requisito | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-CON-001 | | | | | | |

## F. Requisitos operativos (`CR-OPE`)

| ID | Requisito (continuidad, redundancia, modos de operación, ventanas de parada) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-OPE-001 | | | | | | |

## G. Requisitos de mantenimiento (`CR-MAN`)

| ID | Requisito (accesibilidad, repuestos, intercambiabilidad, manuales) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-MAN-001 | | | | | | |

## H. Requisitos de seguridad (`CR-SEG`)

| ID | Requisito (permisos, bloqueo y etiquetado, EPP, arco eléctrico, señalización) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-SEG-001 | | | | | | |

## I. Estándares corporativos (`CR-COR`)

| ID | Estándar corporativo (marcas aprobadas, listas de proveedores, especificaciones tipo, normas internas) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-COR-001 | | | | | | |

## J. Restricciones especiales (`CR-RES`)

| ID | Restricción (plazos, accesos, horarios, permisos, cortes, interferencias con producción) | Fuente | Prioridad | Verificación | Estado | Matriz |
|---|---|---|---|---|---|---|
| CR-RES-001 | | | | | | |

## K. Conflictos y ambigüedades detectados

| ID | Descripción del conflicto o ambigüedad | Elementos en conflicto (CR / NOR / ENG / DEC) | Gravedad | Acción (rfi / DEC) | Estado |
|---|---|---|---|---|---|
| CNF-001 | | | | | |

## L. Desvíos solicitados o aprobados

| ID | Requisito afectado | Desvío | Justificación | Aprobación del cliente (referencia) | Decisión |
|---|---|---|---|---|---|
| | | | | | |

## M. Historial de cambios del cliente

| Fecha | Documento del cliente modificado | Cambio | Requisitos afectados | Acción tomada |
|---|---|---|---|---|
| | | | | |
