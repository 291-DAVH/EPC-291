# project-charter.md — Project Charter (versión técnica completa y línea base)

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Código de proyecto | `[DEFINIR]` |
| Versión de la línea base | 0.1 (borrador) |
| Estado | BORRADOR |
| Fecha | `[DEFINIR]` |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Es la **ficha de arranque completa** del proyecto, con la estructura del *Project Charter* de PM² (resumen ejecutivo, caso de negocio, descripción, costo-plazo-recursos, enfoque, gobierno y referencias), adaptada a este framework. Reúne en un solo archivo lo esencial para que el usuario lo apruebe de una vez y registra la **línea base** aprobada. Se genera con `iniciar proyecto` y se aprueba con `aprobar charter`.

Tiene **dos salidas** de una misma información:

| Salida | Archivo | Para quién | Forma |
|---|---|---|---|
| Técnica (este archivo) | `project-charter.md` | Equipo técnico, cliente, auditoría | Completa, con el ID de la fuente en cada línea |
| Ejecutiva | `project-charter-executive.md` | Jefes y dirección | Una página, estilo *Project Initiation Canvas* de PM², sin IDs ni jerga |

## 2. Alcance

Es una **vista consolidada, no una fuente**. Cada línea cita el archivo o el ID de donde sale (`starting-data.md`, `project-scope.md`, `goals.md`, `client-requirements.md`, `project-information.md`, `deliverables.md`, `assumptions-and-decisions.md`) y no agrega datos propios. Solo cinco bloques son propios de este archivo: el **control del documento**, los **riesgos iniciales propuestos** (sección 3.8, que al aprobarse pasan al registro de riesgos), el **plan de paquetes propuesto** hasta que se aprueba (sección 7), las **preguntas pendientes** (sección 8) y el **registro de la línea base** (sección 9).

Correspondencia con la plantilla PM²: las secciones 1 a 6 y el Apéndice 1 siguen sus títulos; las secciones 7 a 9 son propias del framework. El control del documento de PM² (autor, propietario, aprobadores, historial, ubicación) está en la tabla de control más abajo.

## 3. Forma de utilización

1. Claude lo genera al final de `iniciar proyecto`, después de leer `starting-data.md` y toda la documentación de entrada y de completar los archivos fuente. **Completa la sección 1 (Resumen ejecutivo) al final.** Genera también `project-charter-executive.md` y presenta ambos en el chat en forma resumida; después se detiene.
2. El usuario responde **en un solo mensaje**: las preguntas de la sección 8 (por número; «no sé» es válido) y la aprobación: `aprobar charter` o `corregir charter: …`.
3. Con `aprobar charter` se fija la **línea base 1.0** (de ambas salidas), el plan de paquetes pasa a `deliverables.md` (fuente), los riesgos propuestos pasan al registro de riesgos de `assumptions-and-decisions.md` y Claude ejecuta la generación (`M3`, Fase 4).
4. Si una fuente cambia (por decisión o rfc), Claude **regenera** el charter y su versión ejecutiva con una nueva versión de línea base; no se editan a mano. Ante una diferencia entre el charter y una fuente, manda la fuente. Con `charter ejecutivo` el usuario pide regenerar y presentar solo la salida ejecutiva (por ejemplo, antes de una reunión con la dirección).
5. **Costos:** la sección 4.1 queda `[DEFINIR]`. Un monto solo se escribe si el usuario lo pide expresamente para ese proyecto (por ejemplo, porque el cliente lo informó): se registra una `DEC-nnn` (`DOCUMENT_RULES.md`, RG-21), se coloca en el campo libre de la sección 4.1 tal como lo dio el usuario y Claude no lo calcula, no lo extrae de la documentación de entrada ni lo usa en cronogramas.
6. Las celdas sin dato llevan `[DEFINIR]`; lo que no aplica al proyecto se deja como «No aplica» con su motivo.

## 4. Estructura

Control del documento; secciones 1 a 9 y Apéndice 1. Sin límite de páginas, pero cada sección es breve: viñetas y tablas, con el ID de la fuente en cada línea. Lo extenso vive en las fuentes.

## 5. Buenas prácticas

- Resumir, no copiar: una línea por elemento y el ID de su fuente.
- El resumen ejecutivo (sección 1) se escribe al final y se entiende sin leer el resto.
- Una pregunta pendiente por línea, numerada, con la opción sugerida y el `INF-nnn` que la registra.
- Si una sección se vuelve larga, el problema está en la fuente: se resuelve allí.
- Sin costos ni montos, salvo lo indicado en la forma de utilización 5.

---

# CONTROL DEL DOCUMENTO

| Campo | Valor |
|---|---|
| Título del documento | Project Charter |
| Proyecto | `[DEFINIR]` |
| Autor del documento | Claude (generado con `iniciar proyecto`) |
| Propietario del proyecto (PO) | `[DEFINIR]` |
| Responsable del proyecto (PM) | `[DEFINIR]` |
| Versión del documento | 0.1 |
| Sensibilidad | `[DEFINIR]` (Pública / Limitada / Alta) |
| Fecha | `[DEFINIR]` |
| Ubicación vigente | `02_PROJECT/project-charter.md` |

**Aprobadores y revisores.** Todos los aprobadores son obligatorios; se conserva el registro de cada aprobación.

| Nombre | Rol | Acción (Aprueba / Revisa) | Fecha |
|---|---|---|---|
| `[DEFINIR]` | | | |

**Historial del documento.** Más reciente primero. Cambios editoriales, de formato y de redacción no requieren nueva aprobación; todo cambio de contenido sí (se regenera con nueva versión de línea base).

| Revisión | Fecha | Creada por | Descripción breve del cambio |
|---|---|---|---|
| 0.1 | `[DEFINIR]` | Claude | Borrador generado con `iniciar proyecto` |

---

# REGISTRO DEL PROYECTO (generado por Claude)

## 1. Resumen ejecutivo

`[DEFINIR]` — Qué se hace, para quién, con qué alcance, en qué plazo y qué se necesita del usuario. Entre 5 y 8 líneas, sin IDs. Se escribe al final, con todo lo demás completo.

## 2. Consideraciones sobre el caso de negocio

`[DEFINIR]` — Situación o necesidad que origina el proyecto, impacto y **urgencia** (son cosas distintas: algo de poco impacto puede ser urgente), influencias externas (interfaces, requisitos regulatorios, plazos del cliente). Fuente: `goals.md` y `starting-data.md`, secciones 1, 2 y 6. Si el cliente no informó un caso de negocio, se indica «No informado» y se registra el `INF-nnn`.

## 3. Descripción del proyecto

### 3.1 Alcance

**3.1.1 Incluye (IN).** `[DEFINIR]` — Por disciplina (`ALD-nnn`), con las fases a nuestro cargo y las que corresponden al Contratista. Fuente: `project-scope.md` y `starting-data.md`, sección 4.

**3.1.2 Excluye (OUT).** `[DEFINIR]` — Exclusiones principales (`EXC-nnn`) y áreas que podrían parecer parte del alcance y no lo son. Fuente: `project-scope.md`.

**3.1.3 Enunciado del alcance.** `[DEFINIR]` — Un párrafo que la dirección pueda leer y entender qué se entrega y qué no.

### 3.2 Criterios de éxito

`[DEFINIR]` — Criterios por los que el proyecto se considera un éxito o un fracaso, separando los **críticos** (sin ellos no hay éxito) de los deseables, y los del producto de los del proyecto en su conjunto. Incluye los criterios de aceptación (`CAC-nnn`). Fuente: `goals.md` y `project-scope.md`, sección C.

| N.º | Criterio | Tipo (Crítico / Deseable) | Fuente |
|---|---|---|---|
| 1 | `[DEFINIR]` | | |

### 3.3 Necesidades de las partes interesadas

`[DEFINIR]` — Qué necesita cada parte, por qué y con qué prioridad. Fuente: `client-requirements.md` (`CR-nnn`).

| ID | Descripción de la necesidad | Parte interesada | Prioridad |
|---|---|---|---|
| `CR-nnn` | `[DEFINIR]` | | |

### 3.4 Entregables

`[DEFINIR]` — Qué elaboramos (5-a), qué exige el pliego al Contratista (5-b) y qué presenta el oferente (5-c); cantidad de documentos de la LME. No se incluyen los entregables de gestión del propio framework. Fuente: `starting-data.md`, sección 5, y `deliverables.md`.

| ID | Entregable | Descripción |
|---|---|---|
| `[DEFINIR]` | | |

### 3.5 Características

`[DEFINIR]` — Capacidades de alto nivel que deben tener los entregables para cubrir cada necesidad (el qué y el porqué, no el cómo). Una necesidad puede requerir varias características.

| Necesidad (`CR-nnn`) | Característica | Entregable(s) |
|---|---|---|
| `[DEFINIR]` | | |

### 3.6 Restricciones

`[DEFINIR]` — Restricciones de personas, plazo, recursos, tecnología, interfaces, normas, restricciones operativas, decisiones ya tomadas y requisitos de confidencialidad. Fuente: `goals.md`, `project-information.md` y `assumptions-and-decisions.md` (`DEC-nnn`).

| N.º | Restricción | Origen |
|---|---|---|
| 1 | `[DEFINIR]` | |

### 3.7 Supuestos

`[DEFINIR]` — Supuestos vigentes. Se consideran ciertos hasta validarse; sin validar pueden convertirse en riesgos. Fuente: `assumptions-and-decisions.md` (`SUP-nnn`). El estado vive solo allí.

| ID | Supuesto | Fecha objetivo de validación |
|---|---|---|
| `SUP-nnn` | `[DEFINIR]` | |

### 3.8 Riesgos

`[DEFINIR]` — Riesgos iniciales **propuestos por Claude** a partir de `INF-nnn` abiertos, supuestos sin validar, restricciones y dependencias. Probabilidad e impacto de 1 a 5; nivel = P × I. Hasta la aprobación son propuesta de este archivo; con `aprobar charter` pasan al registro de riesgos de `assumptions-and-decisions.md`, que es su fuente.

| ID | Riesgo (causa → evento → efecto) | Prob. | Impacto | Nivel | Estrategia | Acción | Responsable |
|---|---|---|---|---|---|---|---|
| `RIE-nnn` | `[DEFINIR]` | | | | | | |

## 4. Costo, plazo y recursos

### 4.1 Costo

`[DEFINIR]` — Campo libre. Por defecto no se completa: los costos los maneja el cliente internamente y no se plasman en el proyecto (`DOCUMENT_RULES.md`, RG-21). Si el usuario pide expresamente incluir un monto (por ejemplo, informado por el cliente), se coloca aquí tal como lo dio, sin cálculos, con la `DEC-nnn` que lo autoriza.

### 4.2 Plazo e hitos

`[DEFINIR]` — Plazo contractual y unidad, modo de gestión y emisiones previstas (ifa / ifc por fase). Solo con gestión del proyecto: duraciones propuestas, plazo resultante frente al límite y, si hay déficit, las tres opciones de `schedule-ccpm.md`. Fuente: `starting-data.md`, secciones 4, 6 y 7.

| ID | Hito | Fecha objetivo |
|---|---|---|
| H-01 | Línea base 1.0 aprobada (`aprobar charter`) | `[DEFINIR]` |

### 4.3 Recursos previstos

`[DEFINIR]` — Personas y perfiles por disciplina y fase, herramientas (CAD, normas, biblioteca), información que debe aportar el cliente y quién provee cada cosa. Fuente: `starting-data.md` y `project-information.md`.

| ID | Recurso | Descripción |
|---|---|---|
| R-01 | `[DEFINIR]` | |

## 5. Enfoque

### 5.1 Metodología

`[DEFINIR]` — Se trabaja con este framework: fases `IC` / `IB` / `ID` / `IE`, paquetes `PQ-nn` que avanzan por Ingeniería → Revisión → Auditoría → Liberado → Entregables, revisión del usuario sobre PDF y auditoría única por emisión. Modo de gestión: solo ingeniería o ingeniería + gestión (CCPM). Indicar cualquier desvío acordado. Fuente: `starting-data.md`, sección 7, y `DEC-001`.

### 5.2 Gestión de cambios

**5.2.1 Cambios de proyecto.** Los cambios que modifican la línea base, el alcance o los requisitos se piden con `rfc-nnn` (`change-requests.md`) y los cambios de este archivo se aprueban formalmente: el charter se regenera con una nueva versión de línea base.

**5.2.2 Gestión de la configuración.** Todo documento nace en revisión `00.R.C.FF`; el estado de cada paquete es su ubicación y su integridad se controla con el manifiesto del registro (`90-management/ledger`). Un paquete modificado vuelve a Ingeniería. Detalle en `DOCUMENT_RULES.md` y `m6-states-quality.md`.

**5.2.3 Cambio organizacional.** `[DEFINIR]` — No aplica salvo que el proyecto implique cambios en la organización del cliente.

## 6. Gobierno y partes interesadas

### 6.1 Estructura

`[DEFINIR]` — Quién decide, quién dirige y quién ejecuta. Correspondencia con los roles de PM²:

| Rol PM² | En este proyecto | Nombre |
|---|---|---|
| Propietario del proyecto (PO) | Cliente / responsable del contrato | `[DEFINIR]` |
| Gerente de negocio (BM) | `[DEFINIR]` | `[DEFINIR]` |
| Proveedor de la solución (SP) | Nuestra organización | `[DEFINIR]` |
| Responsable del proyecto (PM) / Líder técnico | Usuario (su rol en `starting-data.md`) | `[DEFINIR]` |
| Equipo central (PCT) | Usuario + Claude (desarrollo); revisor; auditor | `[DEFINIR]` |
| Comité de dirección (PSC) | `[DEFINIR]` (si existe) | `[DEFINIR]` |

### 6.2 Roles y responsabilidades

`[DEFINIR]` — Quién redacta, quién revisa (hoja de revisión sobre PDF), quién audita y quién aprueba las liberaciones y las emisiones. Referencia: `m6-states-quality.md` y `CLAUDE.md`.

Matriz RASCI de los hitos principales (R = responsable, A = aprueba, S = apoya, C = consultado, I = informado):

| Actividad / hito | Cliente (PO) | Líder técnico (PM) | Redactor | Revisor | Auditor |
|---|---|---|---|---|---|
| Aprobar charter | A | R | S | C | I |
| Desarrollar paquete | I | A | R | C | I |
| Revisión del paquete | I | S | S | R/A | I |
| Auditoría de la emisión | I | A | I | C | R |
| Emisión ifa / ifc | A | R | S | I | C |
| Aceptación y cierre | A | R | I | I | C |

Los interesados con poder o interés alto se detallan en `90-management/Governance/stakeholders.md`.

### 6.3 Otras partes interesadas

`[DEFINIR]` — Partes interesadas, perfil breve y qué problema perciben que el proyecto resuelve (no sus requisitos, que están en 3.3). Fuente: `project-information.md` (contactos) y `starting-data.md`.

| Parte interesada | Perfil | Interés / problema percibido | Influencia (Alta / Media / Baja) |
|---|---|---|---|
| `[DEFINIR]` | | | |

## 7. Plan de paquetes

`[DEFINIR]` — Orden, paquete, documentos y dependencias de la fase de inicio. Hasta la aprobación es propuesta de este archivo; luego su fuente es `deliverables.md`.

| Orden | Paquete | Documentos | Depende de |
|---|---|---|---|
| 1 | PQ-01 | `[DEFINIR]` | — |

## 8. Preguntas pendientes

Responda por número, todas de una vez. «No sé» es válido: se registra `[DEFINIR]`, se crea el `INF-nnn` y el proyecto sigue.

| N.º | Pregunta | Opción sugerida | Registro |
|---|---|---|---|
| 1 | `[DEFINIR]` | | INF-001 |

## 9. Línea base

La línea base es la **definición aprobada** del proyecto y la fuente de verdad: ningún documento puede contradecirla sin una decisión formal (`DEC-nnn`) en `assumptions-and-decisions.md`.

| Versión | Fecha de aprobación | Aprobada por | Contenido que congela | Datos pendientes (`INF-nnn`) | Decisión asociada |
|---|---|---|---|---|---|
| 1.0 | `[DEFINIR]` | | `starting-data.md`, `project-scope.md`, `goals.md`, `client-requirements.md` y `project-information.md` | | |

## Apéndice 1. Referencias y documentos relacionados

| N.º | Documento o referencia | Versión / fecha | Ubicación o fuente |
|---|---|---|---|
| 1 | Carpeta del proyecto | | `[DEFINIR]` |
| 2 | Versión de la plantilla del framework | | `project-information.md`, sección A |
| 3 | Documentación recibida del cliente | | `01-input/_INPUT_REGISTER.md` |
| 4 | Charter ejecutivo (misma línea base) | | `02_PROJECT/project-charter-executive.md` |
