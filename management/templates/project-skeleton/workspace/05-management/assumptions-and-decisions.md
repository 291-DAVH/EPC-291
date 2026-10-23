# assumptions-and-decisions.md — Registro Oficial de Decisiones y Supuestos

> Este archivo es la **fuente oficial de decisiones del proyecto**. Una decisión que no figura aquí no es vinculante. Los registros **no se borran**: se reemplazan por estado.

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 0.1 |
| Fecha | `[DEFINIR]` |
| Responsable del registro | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Mantener un **registro histórico, trazable y cronológico** de las decisiones técnicas y de gestión, y de los supuestos adoptados por falta de información, de modo que cualquier dato de un documento pueda explicarse y cualquier cambio pueda rastrearse a su origen.

## 2. Alcance

Incluye: decisiones técnicas, de alcance, documentales, de CAD, de estructura de carpetas, de reutilización de criterios históricos, desvíos respecto de normas o requisitos, y supuestos de diseño. No incluye actas de reunión completas (se archivan en `90-management`) ni comunicaciones del cliente (las instrucciones del cliente se registran como decisión con referencia a la comunicación).

## 3. Forma de utilización

1. **Toda** decisión o supuesto que afecte un documento, plano, cálculo o entregable se registra **antes** de aplicarse.
2. Cada registro tiene ID correlativo único (`DEC-nnn`, `SUP-nnn`, `RIE-nnn`); nunca se reutilizan.
3. Una decisión se **reemplaza** creando otra y marcando la anterior como `SUPERSEDED` con referencia cruzada; no se edita ni se borra.
4. El campo *Documentos afectados* se completa con códigos; ante una decisión aprobada, los documentos afectados se actualizan y se verifican en la siguiente auditoría.
5. Los supuestos se validan o invalidan cuando llega la información; si se invalidan, se evalúa el impacto y se registra la decisión correctiva.
6. **Todo supuesto lleva su base del valor:** práctica típica citada, catálogo u otro proyecto identificable. Un valor sin base no es un supuesto aceptable: queda `[DEFINIR]` (`CLAUDE.md`, 6.1, principio 5). El auditor verifica la base.
7. **Autorización de un supuesto sobre un parámetro crítico** (opción B de la puerta de preparación, `CLAUDE.md`, 8.3): se registra como una `DEC-nnn` de autorización (quién, para qué documento, fecha) además del `SUP-nnn`. No se pueden autorizar los críticos no autorizables (`deliverables.md`, sección 9).
8. **Plan de paquetes y autorizaciones de secuencia:** la confirmación del plan de paquetes (`deliverables.md`, 4.1; `CLAUDE.md`, 8.1, Fase 4), cada reordenamiento que viole el orden por defecto, la autorización de desarrollar dos paquetes independientes a la vez y cualquier apartamiento de la puerta de dependencias se registran como `DEC-nnn`.
9. **Respuestas del usuario en la hoja de revisión** (`review-sheet.md`, sección 5): `CAMBIO` sobre un `SUP` crea una `DEC` nueva que lo reemplaza y el `SUP` queda `CLOSED`; `RECHAZO` lo deja `INVALIDATED`; `ACEPTO` lo mantiene `OPEN` con la aceptación fechada.
10. **Los documentos no escriben el estado** de una `DEC`, un `SUP` o un `RIE`: citan el ID y el estado vive solo aquí (`DOCUMENT_RULES.md`, RG-16).
11. **Riesgos (`RIE-nnn`):** los riesgos iniciales los propone Claude en `iniciar proyecto` (Fase 3) a partir de los `INF-nnn` abiertos, los supuestos `OPEN`, las restricciones y las dependencias, y quedan aprobados con el charter. Cada riesgo lleva causa, evento y efecto, probabilidad (1 a 5), impacto (1 a 5), nivel (`P × I`), estrategia de respuesta y responsable. Se revisan en cada cambio de estado del proyecto y cuando un `INF` o un `SUP` cambia; un riesgo materializado se cierra como `OCCURRED` y, si cambia el alcance, el plazo o la línea base, genera `rfc-nnn` o `DEC-nnn`. El registro **no incluye costos ni montos** (`DOCUMENT_RULES.md`, RG-21).
6. Una decisión que contradiga una norma de cumplimiento obligatorio o un requisito del cliente es un **desvío**: requiere aprobación explícita del cliente o autoridad competente y se marca `Desvío = SÍ`.

## 4. Estructura recomendada

| Estado de decisión | Significado |
|---|---|
| `PROPOSED` | Propuesta pendiente de aprobación |
| `APPROVED` | Aprobada y vigente |
| `REJECTED` | Rechazada (se conserva el motivo) |
| `SUPERSEDED` | Reemplazada por otra decisión |

| Estado de supuesto | Significado |
|---|---|
| `OPEN` | Vigente, sin confirmar |
| `VALIDATED` | Confirmado con información real |
| `INVALIDATED` | Refutado; requiere acción correctiva |
| `CLOSED` | Reemplazado por una decisión (`DEC-nnn`) que fija el valor; ya no es supuesto |

| Estado de riesgo | Significado |
|---|---|
| `OPEN` | Identificado y vigente; con estrategia de respuesta definida |
| `MITIGATED` | Las acciones de respuesta se aplicaron y el nivel bajó; se sigue vigilando |
| `OCCURRED` | Se materializó: se registran el efecto real y la decisión o rfc asociada |
| `CLOSED` | Ya no puede ocurrir o dejó de ser relevante (se conserva el motivo) |

Estrategias de respuesta: **amenazas** — Evitar, Reducir, Transferir, Aceptar; **oportunidades** — Explotar, Mejorar, Compartir, Aceptar. Nivel = probabilidad × impacto (1 a 25); desde 15 se considera **alto** y se informa al usuario en el charter y en cada informe de avance.

## 5. Ejemplos (ilustrativos, no vinculantes)

**Decisión**

| ID | Fecha | Descripción | Motivo | Impacto | Responsable | Estado |
|---|---|---|---|---|---|---|
| EJ-DEC-005 | 2026-11-10 | Adoptar canalización por bandeja ventilada de acero galvanizado en caliente para recorridos interiores de MT y BT. | Ambiente interior sin agresividad química según `EJ-CON-001`; requisito `EJ-CR-CON-002`. | Planos `E-PL-2xx`, cómputo `E-LM-001`, especificación `E-ET-004`. | Líder Técnico | APPROVED |

**Supuesto**

| ID | Fecha | Supuesto | Motivo | Impacto si resulta falso | Responsable | Estado |
|---|---|---|---|---|---|---|
| EJ-SUP-003 | 2026-11-12 | Se adopta temporalmente un factor de utilización de 0,8 para las tomas de uso general del tablero seccional. | No se recibió dato del cliente (EJ-INF-002). Base del valor: práctica típica citada en el catálogo del fabricante del tablero (hoja de datos en la biblioteca). | Revisar el balance de cargas y el dimensionamiento de conductores y protecciones. | Ingeniero Senior | OPEN |

## 6. Buenas prácticas

- Redactar la decisión de modo que pueda entenderse sin el contexto de la reunión.
- Indicar siempre **por qué**, no solo **qué**.
- Cuantificar el impacto en documentos, plazos y alcance.
- Cerrar los supuestos con fecha objetivo: un supuesto sin fecha de validación se vuelve una decisión silenciosa.
- Revisar los supuestos `OPEN` en cada cambio de estado del proyecto.
- Vincular las decisiones a los requisitos de `traceability-matrix.md` que afectan.

---

# REGISTRO DE DECISIONES

| ID | Fecha | Descripción | Motivo | Impacto | Responsable | Estado | Documentos afectados | Reemplaza / Reemplazada por | Desvío (SÍ/NO) | Aprobado por |
|---|---|---|---|---|---|---|---|---|---|---|
| DEC-001 | `[DEFINIR]` | Selección de plantilla de carpetas (A / B / C / D / E) según `folder-templates.md`. | Tipo de proyecto y cliente. | Estructura de `FOLDER_templates`. | `[DEFINIR]` | PROPOSED | — | — | NO | |
| DEC-002 | `[DEFINIR]` | Estándar CAD aplicable: corporativo (`CAD_standards.md`), del cliente, o mixto con tabla de correspondencia. | Requisitos CAD del cliente / proyectos históricos. | Plantillas y planos. | `[DEFINIR]` | PROPOSED | — | — | NO | |
| DEC-003 | `[DEFINIR]` | Conjunto normativo base y ediciones aplicables (IEC + reglamentación local + normas del cliente). | `project-information.md`, sección G. | Todos los criterios `ENG-`. | `[DEFINIR]` | PROPOSED | — | — | NO | |
| DEC-004 | `[DEFINIR]` | Reutilización de criterios y nomenclaturas de proyectos históricos del cliente (si existen): qué se reutiliza y qué no. | `CLAUDE.md`, sección 10. | Nomenclatura, criterios, CAD. | `[DEFINIR]` | PROPOSED | — | — | NO | |

Agregar nuevas decisiones a continuación, en orden cronológico.

# REGISTRO DE SUPUESTOS

| ID | Fecha | Supuesto | Motivo (información faltante) | Base del valor (práctica típica citada, catálogo, otro proyecto) | Impacto si resulta falso | Responsable | Estado | Fecha objetivo de validación | Información pendiente (INF-nnn) | Decisión asociada | Documentos que lo usan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SUP-001 | | | | | | | OPEN | | | | |

# REGISTRO DE RIESGOS

| ID | Fecha | Riesgo (causa → evento → efecto) | Origen (`INF-` / `SUP-` / restricción) | Prob. (1-5) | Impacto (1-5) | Nivel (P×I) | Estrategia de respuesta | Acción | Responsable | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| RIE-001 | | | | | | | | | | OPEN |

# CONTROL DE DESVÍOS

| ID decisión | Norma o requisito desviado | Justificación | Medidas compensatorias | Aprobación (quién, fecha, referencia) |
|---|---|---|---|---|
| | | | | |

# HISTORIAL DEL REGISTRO

| Versión | Fecha | Cambio | Responsable |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Versión de plantilla con decisiones iniciales obligatorias | |
