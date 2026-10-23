# project-audit.md — Sistema de Auditoría Técnica y Documental

> **REGLA OBLIGATORIA:** cuando `project-status.md` indique `FOR_AUDIT`, Claude realiza **automáticamente** una auditoría completa utilizando toda la documentación disponible, antes de cualquier otra tarea.
> **Nunca se asume conformidad. Siempre se exige evidencia.**
> **Ningún proyecto ni documento se considera finalizado sin una auditoría aprobada.**

| Campo | Valor |
|---|---|
| Versión del sistema de auditoría | 1.3 |
| Fecha | 2026-10-07 |
| Responsable | Responsable de Calidad |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Garantizar que ningún proyecto se considere finalizado sin verificar el cumplimiento completo de objetivos, requisitos, criterios de ingeniería, entregables y trazabilidad, mediante un proceso formal, repetible y basado en evidencia.

## 2. Alcance

Cinco auditorías integradas:

| Código | Auditoría | Pregunta que responde |
|---|---|---|
| **A1** | Documental | ¿Existe, está bien nombrado, versionado y es consistente cada documento? |
| **A2** | De requisitos | ¿Se cumplió cada requisito del cliente y hay evidencia? |
| **A3** | De ingeniería | ¿Cumple normas, criterios y decisiones, y es técnicamente consistente? |
| **A4** | De entregables | ¿Existen todos los entregables requeridos, completos y vigentes? |
| **A5** | De trazabilidad | ¿Cada objetivo llega a un entregable pasando por requisito, criterio, documento y plano? |

Aplica a las auditorías de **emisión** (antes de cada ifa —una por fase de ingeniería contratada: Conceptual, Básica, Detalle y Ejecutiva— y antes de la ifc; **cada emisión tiene su auditoría propia**, una sola por emisión), de **re-entrega** (tras cambios) y de **cierre** (antes de `CLOSED`). La revisión interna por paquete (ifr) la hace el usuario y no es una auditoría.

## 3. Forma de utilización

### 3.1 Disparadores

| Disparador | Tipo | Acción |
|---|---|---|
| `project-status.md` = `FOR_AUDIT` | ENTREGA / RE-ENTREGA / CIERRE (según bloque B de `project-status.md`) | Auditoría completa automática |
| Comentarios del cliente al ifa anterior cerrados (`REV-nnn` resueltos) y paquetes afectados `REVIEWED` de nuevo, o `cliente aprueba` y paquetes de la fase siguiente `REVIEWED` | ENTREGA (ifa o ifc) | Auditoría **propia** de la emisión siguiente: alcance = lo nuevo y lo modificado; verifica además que los comentarios del cliente al ifa anterior estén cerrados (A2-12) y que la madurez de los entregables corresponda a la fase (A1-18) |
| Cambio posterior a una auditoría sobre documentos auditados | RE-ENTREGA | Re-auditar el alcance afectado y sus dependencias |
| Comando **`auditar`** (alias `auditar proyecto`) | Completa (o según alcance indicado) | Igual que con el estado `FOR_AUDIT`: auditoría completa automática |
| Pedido explícito del usuario | Parcial o completa | Ejecutar según alcance indicado |
| Cierre de proyecto (`as-built → CLOSED`) | CIERRE | Auditoría completa con foco en as-built y trazabilidad al 100 % |
| Comando **`estado del proyecto`** o **`informe de avance`**, o cierre de un paquete de revisión que el usuario pida medir | AVANCE | Informe de avance del auditor (sección 3.4); no emite veredicto ni cambia el estado |

### 3.2 Procedimiento

| Paso | Actividad |
|---|---|
| 1 | **Congelar el alcance:** precondición: **todos los paquetes de la entrega están REVISADOS (`REVIEWED`)**, ninguno `REABIERTO` ni en `FOR_REVIEW` / `INTERNAL_REVIEW`; desde el segundo ifa de una fase, además, los **comentarios del cliente al ifa anterior están cerrados** (A2-12). El alcance de cada ifa es lo **nuevo y lo modificado desde la auditoría anterior** (documentos con revisión nueva —`00.0.c` o `00.n`—, paquetes nuevos y sus dependencias) **más todo documento que comparta un dato con ellos** (por ejemplo, la capacidad de una termomagnética cambiada en el unifilar se contrasta con el multifilar, el pliego, los listados y los cálculos: la inconsistencia se reporta aunque el otro documento no haya cambiado). La **ifc** audita el conjunto completo con consistencia cruzada de todos los documentos. Listar los paquetes y los documentos auditados con código y revisión interna; verificar el bloque B de `project-status.md`. La auditoría se ejecuta **una sola vez por emisión**, sobre el conjunto de paquetes; no se audita paquete por paquete (por paquete, Claude hace solo la auto-verificación ligera de `CLAUDE.md`, 8.3, punto 7). |
| 2 | **Cargar contexto:** leer `goals.md`, `project-information.md`, `client-requirements.md`, `assumptions-and-decisions.md`, `engineering-standards.md`, `DESIGN_RULES.md`, `DOCUMENT_RULES.md`, `CAD_standards.md`, `deliverables.md`, `traceability-matrix.md`, `folder-templates.md`, **`drawing-status.md`** (estado de los planos y diagramas, anotado por el usuario; el auditor lo lee, no lo modifica) y, si el proyecto tiene pliego, `TECHNICAL_SPECIFICATIONS_GUIDE.md`. |
| 3 | **Ejecutar A1 a A5** (secciones 4.1 a 4.5) con **mentalidad adversarial**: buscar activamente lo que falta, no confirmar lo que está. |
| 4 | **Contraste cruzado** de parámetros (sección 5): comparar cada valor entre documentos, planos, listados y fuente maestra. |
| 5 | **Clasificar hallazgos** (sección 6) y calcular el veredicto (sección 7). |
| 6 | **Emitir el informe** en el formato simple de la sección 8 (resultado, observaciones y anexos de respaldo) como `04-audit/audit-reports/AUD-nn_YYYYMMDD.md`. El informe debe responder en dos minutos: *¿qué tengo que corregir para poder entregar?* |
| 7 | **Entregar el informe y proponer** el estado resultante según la sección 7 (`AUDITED` si corresponde, **que se registra recién cuando el usuario dice `aprobar auditoría`**; si no, `ENGINEERING` o la permanencia en `FOR_AUDIT`). El auditor **escribe un único archivo: el informe** (`AUD-nn_YYYYMMDD.md` o `progress-nn_YYYYMMDD.md`); no modifica los documentos auditados ni los archivos de gestión, solo **propone** los cambios. Quien actúa como gestor del proyecto (Claude en el rol de Project Manager, tras recibir el informe) **registra** el informe en `90-management/audit-register.md` y actualiza `project-status.md`, `traceability-matrix.md` y `deliverables.md`. Esto preserva la independencia del auditor. |
| 8 | **Seguimiento:** cerrar cada hallazgo con evidencia; el auditor verifica el cierre. |
| 9 | **Re-auditar** los puntos corregidos, comprobando que la corrección no introdujo nuevas inconsistencias. |

### 3.3 Principios de la auditoría

1. **Evidencia o nada:** conformidad = referencia identificable (código, revisión, sección, tabla o registro). "Se entiende que cumple" no es evidencia.
2. **Ausencia de evidencia = hallazgo.** Si algo no puede verificarse con la documentación disponible, se reporta como `NO VERIFICABLE` y cuenta como hallazgo MAJOR, salvo el caso de un pendiente aceptado y declarado, cuya severidad depende de la entrega objetivo (sección 6.1). Nunca se asume conformidad: lo no verificado figura en el informe aunque no bloquee.
3. **Independencia:** el auditor no aprueba su propio trabajo; se ejecuta una pasada separada de la redacción.
4. **Alcance completo:** se auditan todos los elementos del alcance, no una muestra, salvo acuerdo explícito y registrado.
5. **Límites de la auditoría documental:** Claude audita lo que está documentado. No verifica ejecución física en obra: para las fases `CONSTRUCTION`, `PRECOMMISSIONING`, `COMMISSIONING` y `as-built`, exige evidencia (protocolos firmados, registros, redlines, certificados). La **aprobación final y la firma profesional son humanas**.
6. **Reportar siempre** omisiones, riesgos, inconsistencias, entregables, requisitos e información faltantes, pero **sin repetirlos**: cada hecho es **un solo hallazgo** (un ID) y se cita desde donde haga falta; no se reescribe en otras secciones.
7. **Auditar no es diseñar:** el hallazgo declara únicamente que *no existe evidencia que demuestre el cumplimiento* de algo identificado. La *Acción requerida* dice qué hay que lograr, no cómo diseñarlo; el auditor no sustituye al diseñador ni decide la solución.
8. **Primero lo accionable:** el cuerpo del informe lleva solo lo que hay que cerrar; las listas A1 a A5 son herramienta de trabajo y el respaldo va en anexos breves.

### 3.4 Informe de avance (a cargo del auditor)

El **avance del proyecto lo reporta el auditor**, no quien desarrolla, para que la medición sea independiente. El informe es de solo lectura: no modifica documentos ni archivos de gestión, no emite veredicto y no cambia el estado.

**Formato:** Markdown compatible con Pandoc (`DOCUMENT_RULES.md`, RG-20 y 7.1): bloque YAML de portada (`code` = `progress-nn`), un solo `#` (*Informe de avance progress-nn*) y las secciones de la tabla como títulos `##` **sin número**, en este orden. Empieza con una sección **Resumen** de una página (estado, avance global, bloqueos, semáforo del buffer y 3 próximos pasos), sigue con las diez secciones de detalle y la evidencia por entregable va en un anexo al final. Mismo principio que el informe de auditoría: primero lo accionable. En esta guía las secciones se citan por su nombre.

**Contenido mínimo** (`90-management/progress/progress-nn_YYYYMMDD.md`; numeración correlativa propia, independiente de la de `AUD-nn`), en este orden:

| Sección (título `##`, sin número) | Contenido |
|---|---|
| Estado y fecha | Estado del proyecto, fase, hitos contractuales y fechas de entrega |
| Avance por entregable | Cada `ENT-nnn` con estado y revisión **verificados contra la carpeta** (no contra lo declarado), y porcentaje con la base de cálculo |
| Avance global | **Único cálculo del proyecto:** promedio ponderado del avance de los entregables aplicables, con el avance de cada `ENT-nnn` medido por hitos (generado, revisado, auditado, entregado) y los pesos definidos en `schedule-ccpm.md`, sección D. Además: generados y en revisión; bloqueados. Este valor es el que se copia a `project-status.md`, sección A; no existe otro cálculo de avance global |
| Cobertura de trazabilidad | Conteo por categoría y estado de `traceability-matrix.md` |
| Bloqueos e información pendiente | `BLQ-nnn`, `INF-nnn` vencidas o próximas a vencer y su impacto en fechas |
| Revisión y auditoría | Paquetes `REVIEWED` / pendientes / `REABIERTO`, paquete en `FOR_REVIEW`, comentarios `REV-nnn` abiertos, hallazgos `HAL-nn-nnn` abiertos |
| Cambios | `rfc-nnn` abiertas, antigüedad y sin decisión, impacto en el buffer, y comentarios del cliente a la última entrega (abiertos / cerrados) |
| Cronograma y buffers (solo con gestión del proyecto; en modo solo ingeniería se omite) | Avance de la cadena crítica, consumo del buffer de proyecto, zona (VERDE / AMARILLO / ROJO) según los umbrales de `schedule-ccpm.md`, sección D, buffers de alimentación y entregables en riesgo. Si el buffer no cabe, se informa el retraso proyectado en días hábiles frente al límite |
| Planos | Estado de cada plano o diagrama **tal como lo anotó el usuario en `drawing-status.md`** (`PLANNED`, `CAD_INPUT`, `DRAWN`, `REVIEWED`, `ENTREGADO`), con la fecha de la última anotación; el auditor no lo puede verificar contra el DWG |
| Riesgos y próximos pasos propuestos | Riesgos abiertos y acciones sugeridas |

Después del informe, Claude (gestor del proyecto) lo registra en `audit-register.md`, actualiza `project-status.md` y la sección D de `schedule-ccpm.md` con esos datos y cita el número de informe.

## 4. Estructura recomendada — listas de verificación

Resultado de cada ítem: `OK` (con evidencia citada), `NO OK` (hallazgo), `N/A` (con justificación) o `NO VERIFICABLE` (hallazgo).

### 4.1 A1 — Auditoría documental

| ID | Verificación | Fuente de contraste |
|---|---|---|
| A1-01 | **Existencia:** cada documento aplicable de `deliverables.md` existe en la ruta prevista (de un plano en `CAD_INPUT` se verifica el documento de insumos; ver la nota de 4.4). | LME vs carpetas |
| A1-02 | **Nomenclatura:** códigos y nombres de archivo cumplen `DOCUMENT_RULES.md`, sección 8 (o la codificación del cliente con su tabla de correspondencia). | `DOCUMENT_RULES.md` |
| A1-03 | **Versionado:** revisión **interna** de portada = revisión del archivo = revisión de la LME (`00.R.C.FF`, por ejemplo `00.0.0.IB`, `00.2.34.ID`, o `01`+ tras el as-built; herramienta: `document_verifier.py`, que se cita en el Anexo C). Cada revisión `00.n` (n ≥ 1) cita en el control de revisiones la `rfc-00n` que la originó; cada unidad del último dígito corresponde a un comentario `REV-nnn` incorporado (o a un avance de fase, que cambia solo el sufijo), y las revisiones superadas están en `ARCHIVE` con su nombre. El sufijo de fase coincide con la fase del documento en la LME. En las copias de `06-deliverables` el rótulo es `Rev 00`. | Documento, LME, `change-requests.md` |
| A1-04 | Control de revisiones completo, con descripciones específicas. *Revisó* lo completa Claude con el nombre del usuario al registrar la revisión aprobada del paquete; *Aprobó* solo es exigible en las filas de entrega (`00`, `01` y `02`+), no en las revisiones internas (`00.0.c`, `00.n`). | `DOCUMENT_RULES.md`, 10 |
| A1-05 | **Duplicados:** no hay dos documentos con mismo propósito o código; no hay revisiones superadas en carpetas activas (las carpetas de entrega de `06-deliverables` conservan lo ya entregado y no cuentan como duplicado). | Carpetas, LME |
| A1-06 | **Estados coherentes** entre `project-status.md`, LME y documentos, según la tabla 4.3 de `project-status.md`. | Archivos de gestión |
| A1-07 | Estructura estándar y reglas por tipo de documento cumplidas. | `DOCUMENT_RULES.md`, 6 y 7 |
| A1-08 | **Consistencia:** referencias cruzadas válidas. En documentos `00.n` basta que citen «revisión vigente» de un código existente en la LME; **al entregar** (`Rev 00` al cliente) toda referencia de las copias de `06-deliverables` debe citar la revisión exacta del juego entregado (`Rev 00`, con la correspondencia interna en el transmittal), y esto se verifica en ese momento (antes de la entrega es `N/A` y no genera hallazgo). | Documentos, LME |
| A1-09 | Sin marcas `[DEFINIR]`, `[VERIFICAR]`, `[PENDIENTE]` ni `SUP-` abiertos sin justificación aceptada: la aceptación debe constar en la tabla de pendientes aceptados (`PA-nnn`, con fecha y firmante) del bloque B de `project-status.md`. La severidad se fija según 6.1. | Búsqueda en documentos, `project-status.md` (B) |
| A1-10 | Redacción conforme a RG-01 a RG-19 (sin marketing, sin redundancia, lenguaje contractual correcto); el formato Markdown/Pandoc (RG-20) se audita aparte en A1-17. | `DOCUMENT_RULES.md`, 5 y 11 |
| A1-11 | Estructura de carpetas conforme a la plantilla seleccionada (DEC-001). | `folder-templates.md` |
| A1-12 | Cada entrega tiene transmittal registrado, con el rótulo al cliente (`Rev 00`), la revisión interna enviada de cada documento (`00.R.C.FF`), la fase y la confirmación del envío (`entrega enviada TR-nnn`) (se verifica al entregar; antes de la entrega es N/A y no genera hallazgo). | `90-management/Governance/Communications`, `project-status.md` (N) |
| A1-13 | Planos conformes a `CAD_standards.md` (capas, rótulo, xrefs, impresión). **`N/A` hasta que el plano esté `DRAWN`** en `drawing-status.md` (ver la nota de 4.4). Para cada plano `DRAWN` o posterior: el PDF de revisión y el DWG existen en las rutas de la tabla, la columna *Verificación de Claude* tiene resultado (`OK` u observaciones `rfc/REV-nnn` cerradas) y la revisión del rótulo coincide con la *Rev interna* de `drawing-status.md` y con la LME. | `CAD_standards.md`, 11; `drawing-status.md` |
| A1-14 | **Revisión previa:** los comentarios de revisión (`REV-nnn`) están cerrados y el usuario aprobó cada paquete de la entrega (`revisión aprobada` en la última hoja de cada paquete); ningún documento auditado permanece en `FOR_REVIEW`, `INTERNAL_REVIEW` ni `REABIERTO`. | `project-status.md` (secciones L y M), hojas de revisión |
| A1-15 | **Lecciones aprendidas:** `lessons-learned.md` no contiene lecciones ya extraídas (tras la extracción queda en blanco y el contenido está en `02-engineering/ARCHIVE`); en la auditoría de cierre, todas las lecciones están extraídas o descartadas con motivo. | `lessons-learned.md`, `02-engineering/ARCHIVE` |
| A1-16 | **Carpeta de entrega:** el contenido de `06-deliverables/<tipo>/<YYYYMMDD_TR-nnn_Rev00>` coincide con lo editable aprobado de `02-engineering` (mismos códigos y contenido; la revisión interna `00.R.C.FF` figura en el transmittal y el rótulo es `Rev 00`; coherente con la LME); está depurado según la lista de «depuración de entrega» (DE-01 a DE-10: documentos sin comentarios, marcas internas ni metadatos de trabajo; DWG con `PURGE`, `AUDIT`, `RECOVER` y xrefs resueltas; PDF de verificación contra el DWG); no fue editado después de entregado (solo lectura). Se verifica al entregar; antes de la entrega es `N/A` y no genera hallazgo. | `06-deliverables`, `02-engineering`, `folder-templates.md` (4.5), `DOCUMENT_RULES.md` (RG-17) |
| A1-17 | **Formato Markdown/Pandoc (RG-20):** los documentos que genera el proyecto (pliegos, memorias, especificaciones, síntesis, listados en `.md`, actas, informes y hojas de revisión) tienen los títulos sin numeración manual, un solo `#` por archivo sin saltos de nivel, viñetas con `-` (nunca `*` ni `+`), referencias cruzadas por nombre y no por número, y bloque YAML de portada (o la tabla de portada que el usuario haya fijado). Se apoya en `document_verifier.py` (CAL-010) y `specification_verifier.py` (CAL-011), cuyos errores de formato (título numerado, viñeta `*` o `+`) y avisos (varios `#`, saltos de nivel, referencias numéricas, lista sin línea en blanco) se citan en el Anexo C; los archivos del framework no se auditan en este ítem (conservan su numeración interna). **Severidad: `MINOR`**, nunca bloqueante; sube a **`MAJOR`** solo por reincidencia: si **más de un tercio** de los documentos del alcance de la auditoría lo incumple (con error de formato), el hallazgo es único y bloquea hasta corregirse. | `DOCUMENT_RULES.md` (RG-20 y 7.1), `document_verifier.py`, `specification_verifier.py`, documentos del alcance |
| A1-18 | **Madurez documental por fase:** cada entregable aplicable de la emisión alcanza el nivel de madurez que la matriz de `deliverables.md` (sección 10) exige para la fase, **sobre el mismo archivo** (no copiado de otra fase) y con la revisión continuada. Un entregable por debajo del nivel de la fase es `OBSERVATION` en un ifa y `MAJOR` en la ifc (la ifc solo libera entregables en nivel Final). | `deliverables.md` (10), LME |
| A1-19 | **Confidencialidad económica (RG-21):** ningún documento, registro ni archivo de gestión contiene costos, presupuestos, precios, montos ni condiciones comerciales del cliente, salvo una `DEC-nnn` que lo autorice. Se verifica con `document_verifier.py` (CAL-010, categoría `confidencialidad_economica`; la excepción se marca en la línea con `[ECON-AUTORIZADO DEC-nnn]`) y se complementa con lectura. | MAJOR |
| A1-20 | **Estado por ubicación:** `check-state.py` sin errores: cada paquete está en una sola etapa, los hashes de `03-review`, `04-audit` y `05-released` coinciden con el manifiesto (nada se editó fuera de `02-engineering`), no hay copias sueltas en `02-engineering` ni archivos faltantes en `06-deliverables`, y todo el conjunto de la emisión está en `04-audit`. Se verifica con `check-state.py`; un paquete modificado o inconsistente es bloqueante. | MAJOR |

### 4.2 A2 — Auditoría de requisitos

| ID | Verificación | Fuente de contraste |
|---|---|---|
| A2-01 | **Todos** los requisitos `CR-` del cliente tienen al menos una fila en la matriz. | `client-requirements.md`, matriz |
| A2-02 | Cada requisito tiene fuente identificable (documento, revisión, cláusula). | `client-requirements.md` |
| A2-03 | **Evidencia documental** localizable (documento + sección) para cada requisito `IMPLEMENTED` o `VERIFIED`. | Matriz, documentos |
| A2-04 | **Requisitos pendientes** (`PENDING`, `IN_progress`): listados con causa, responsable y fecha. | Matriz, `project-status.md` |
| A2-05 | **Requisitos contradictorios:** conflictos entre requisitos, con normas obligatorias o con decisiones; todos registrados y gestionados. | Sección K de `client-requirements.md` |
| A2-06 | `NOT_APPLICABLE` con justificación y `DEC-nnn`. | Matriz, decisiones |
| A2-07 | `NON_COMPLIANT` con plan de acción o desvío aprobado. | Matriz, decisiones |
| A2-08 | Requisitos ambiguos o no verificables identificados para reformulación. | `client-requirements.md` |
| A2-09 | Requisitos de normas obligatorias y reglamentos locales incorporados. | `project-information.md` (NOR) |
| A2-10 | Cambios del cliente posteriores (sección M) reflejados en la matriz. | `client-requirements.md` |
| A2-11 | **Cambios con evidencia:** todo cambio recibido tiene `REV-nnn` y, si modifica línea base, alcance, requisitos, parámetros maestros, filosofía de operación, criterios de diseño, potencias, equipos aprobados o decisiones registradas, una `rfc-nnn` con evidencia archivada, evaluación de impacto, decisión (`DEC-nnn`) y estado; las aprobadas están reflejadas en los documentos y en la matriz, y las cerradas tienen verificación. Ningún documento cambió de revisión sin un `REV-nnn` o una `rfc` aprobada que lo justifique (n de la `Rev 00.n` = número de la rfc); una rfc aplicada a algo que era una corrección documental (o al revés) es `MINOR`. | `change-requests.md`, `90-management/rfc` |
| A2-12 | **Comentarios del cliente al ifa anterior cerrados** (aplica desde el segundo ifa de una fase y a la ifc; `N/A` en el primer ifa): cada comentario del cliente tiene su `REV-nnn` (origen CLIENTE), clasificado (rfc o corrección documental) y cerrado: incorporado en el documento con la revisión que lo refleja, o `REJECTED` / `DEFERRED` con `DEC` y comunicación al cliente. Los documentos modificados volvieron a revisión interna (ifr) antes de reemitirse: sin excepciones. Si la fase se dio por aprobada (`cliente aprueba`), existe la `DEC` con su evidencia (aprobación expresa o constancia de la llamada telefónica al cliente). Un comentario sin `REV-nnn` o sin cierre = `MAJOR`. | `change-requests.md`, `project-status.md` (M y N), transmittal de la emisión anterior |

### 4.3 A3 — Auditoría de ingeniería

| ID | Verificación | Fuente de contraste |
|---|---|---|
| A3-01 | **Cumplimiento normativo:** normas aplicables listadas con edición y vigencia verificada; sin normas citadas que no figuren en el proyecto. Se contrastan los `NOR-nnn` del proyecto con los `NRM-nnn` de la biblioteca mediante la columna de correspondencia de `project-information.md`, sección G. | `project-information.md`, documentos, `standards-index.md` |
| A3-02 | Cada criterio `ENG-` con `Aplica = SÍ / PARCIAL` tiene evidencia en un documento. | `engineering-standards.md` |
| A3-03 | Criterios con `Aplica = NO` tienen motivo y decisión. | `engineering-standards.md`, decisiones |
| A3-04 | **Parámetros maestros:** valores coinciden con `project-information.md` en todos los documentos (sección 5). | `project-information.md` |
| A3-05 | **Decisiones:** todas las `APPROVED` reflejadas; ninguna contradicha; ninguna `SUPERSEDED` o `REJECTED` en uso. | `assumptions-and-decisions.md` |
| A3-06 | **Supuestos** `OPEN` identificados, con impacto evaluado; ninguno tratado como hecho. | `assumptions-and-decisions.md` |
| A3-07 | **Consistencia técnica** entre cálculo, especificación, plano y listado (secciones de cable, potencia de transformador, nivel de cortocircuito vs. poder de corte, ajustes de protección, ratings de tableros). | Cálculos, especificaciones, planos, listados |
| A3-08 | Cálculos **reproducibles:** datos de entrada con fuente, método, resultado comparado con el criterio, conclusión. Cada síntesis de cálculo (`SM`) se contrasta con su memoria: no contiene valores, hipótesis ni conclusiones que la memoria no tenga (una diferencia es una inconsistencia `MAJOR`). | Memorias de cálculo, síntesis |
| A3-09 | Coherencia entre unifilares, lista de cables, lista de equipos, implantación y cómputos. | Diagramas, listados, planos |
| A3-10 | **Seguridad:** protección contra contactos, arco, enclavamientos, bloqueo y etiquetado, vías de evacuación y señalización contempladas. | `ENG-SEG-nnn`, `CR-SEG-nnn` |
| A3-11 | Interfaces con otras disciplinas (civil, estructuras, mecánica, instrumentación, telecom) identificadas y coordinadas. | Planos, documentos de interfaz |
| A3-12 | **Operabilidad y mantenibilidad:** accesos, reservas, espacios de trabajo, repuestos. | Planos, especificaciones |
| A3-13 | Los protocolos de pre-commissioning y commissioning cubren los criterios `ENG-PRE` y `ENG-COM` aplicables. | Protocolos, `engineering-standards.md` |
| A3-14 | Coherencia con proyectos históricos del cliente o desviaciones justificadas. | Matriz de herencia (Plantilla E) |
| A3-15 | **Línea base:** ningún documento contradice la línea base (`project-charter.md`, sección 9) sin decisión registrada; alcance por disciplina (ALD-nnn) y criterios de aceptación (`CAC-nnn`) reflejados en los documentos y en la matriz. | `project-charter.md`, `project-scope.md`, decisiones |
| A3-16 | **Disciplinas e interfaces:** para cada disciplina involucrada se aplicaron los criterios de su biblioteca; las interfaces (`ENG-INT-nnn`) están coordinadas y sin interferencias abiertas. | `engineering-standards.md`, planos, matriz de interfaces |
| A3-17 | **Reglas generales de diseño:** el diseño cumple las reglas aplicables de `DESIGN_RULES.md` (alturas de montaje, niveles por tipo de área, etc.) o el desvío tiene decisión registrada. | Planos, memorias, `DESIGN_RULES.md` |
| A3-18 | **Normas y equipos:** los valores normativos citados están verificados contra el archivo de la biblioteca cuando existe (edición y sección; si la norma está `SIN ARCHIVO`, el valor debe estar marcado `[VERIFICAR]` y registrado como pendiente aceptado, ver 6.1); se consultaron solo las normas relevantes al tema; los equipos especificados coinciden con `equipment-catalog.md`, con la lista del cliente o con una decisión registrada; los cálculos citan el `CAL-nnn` y su versión. | `standards-index.md`, `equipment-catalog.md`, `calc-library.md` |
| A3-19 | **Charter técnico = charter ejecutivo:** `project-charter.md` y `project-charter-executive.md` dicen lo mismo con otras palabras. Lo mecánico lo comprueba `document_verifier.py` (misma versión, fecha y estado; mismos `ALD`, `EXC`, `CAC`, `SUP`, `RIE` y `PQ`; mismo nivel de cada riesgo; mismo orden y dependencias de paquetes; mismas fechas de hitos; costo `[DEFINIR]` ⇔ «A definir por el cliente.»): cero ERROR. Lo humano: cada caja del lienzo resume fielmente su sección del charter técnico, sin agregar, quitar ni cambiar el sentido de cifras, plazos, exclusiones o riesgos. | `project-charter.md`, `project-charter-executive.md`, informe de `document_verifier.py` |
| A3-20 | **PDF del charter ejecutivo vigente:** `PROJECT_charter_EXECUTIVE.pdf` existe y lleva el sello `sha256` del `.md` actual (`charter_exporter.py --verificar`); el PDF tiene una sola página y se generó sin avisos de texto sobrante (`sobrantes` vacío en el informe del exportador). | `PROJECT_charter_EXECUTIVE.pdf`, informe de `charter_exporter.py` |

### 4.4 A4 — Auditoría de entregables

| ID | Verificación | Fuente de contraste |
|---|---|---|
| A4-01 | Todo entregable aplicable **incluido en la entrega objetivo** pertenece a un paquete `REVIEWED` completo (nunca solo parte de un paquete), existe, con estado y revisión correctos; los no incluidos figuran como planificados con su paquete, fecha (copiada de `schedule-ccpm.md`) y, si corresponde, `BLQ-nnn`. Un plano en `CAD_INPUT` no puede figurar incluido en la entrega. | `deliverables.md`, `drawing-status.md` |
| A4-02 | **Planos:** `drawing-status.md` es coherente con la LME y con las carpetas: toda fila de plano o diagrama dibujado de la LME figura en `drawing-status.md` (y a la inversa); los planos en `CAD_INPUT` tienen sus insumos entregados; los `DRAWN` o posteriores tienen DWG y PDF de revisión en las rutas indicadas, con rótulo, revisión interna y *Verificación de Claude*; **ningún plano figura en una entrega si no está `REVIEWED` en `drawing-status.md`**, y los planos ya entregados figuran `ENTREGADO`. Un estado que el auditor no puede contrastar con el archivo se informa como declarado por el usuario. | `drawing-status.md`, LME, carpeta de planos e insumos |
| A4-03 | **Memorias:** descriptivas y de cálculo completas, sin pendientes injustificados. | LME, documentos |
| A4-04 | **Especificaciones:** completas, con criterios de aceptación y documentación exigida al proveedor. | LME, documentos |
| A4-05 | **Cálculos:** el conjunto exigido por el alcance está entregado. | LME, `deliverables.md` |
| A4-06 | **Listados:** completos y consistentes con planos y diagramas. | Listados, planos |
| A4-07 | Entregables `NO` aplicables con decisión registrada. | `deliverables.md`, decisiones |
| A4-08 | **Protocolos** completos, firmados, con instrumentos identificados y calibrados (fases PRE y COM). | Protocolos |
| A4-09 | **As-Built** (auditoría de cierre): cada plano y listado actualizado o confirmado sin cambios; informe de modificaciones respecto de ifc; redlines incorporados; manuales; data book. | Redlines, as-built |
| A4-10 | Formatos y medios de entrega conformes al requisito del cliente (nativo y PDF) (se verifica al entregar; antes de la entrega es N/A y no genera hallazgo). | `client-requirements.md` |
| A4-11 | Capacitación entregada y registrada según plan. | Registros de capacitación |
| A4-12 | **Cronograma** (solo con gestión del proyecto; en modo solo ingeniería no aplica)**:** `schedule-ccpm.md` está calculado con la herramienta, recalculado tras cada cambio aprobado o bloqueo, y la fecha de fin con buffer cumple el límite contractual o el déficit está informado. | `schedule-ccpm.md` |
| A4-13 | **Redacción del pliego** (aplicable solo si el proyecto tiene pliego `PG`; `N/A` si no): cada capítulo de `02-engineering/TECHNICAL_SPECS` responde su única pregunta; las obligaciones del Contratista están en los capítulos 04 y 10 y no en 01, 02, 03, 05 ni 09; no hay normativa repetida fuera del 03 (se cita el `NOR-nnn`); no hay referencias hacia adelante ni repeticiones entre capítulos; la numeración es contigua y estable; los capítulos que no aplican conservan su número con «No aplica a este proyecto (DEC-nnn)»; el consolidado de `06-deliverables` coincide con `TECHNICAL_SPECS` (orden, texto y revisión; se verifica al entregar, antes es `N/A`). Severidad: texto ubicado en el capítulo equivocado = `MINOR`; obligación contractual contradictoria o duplicada entre capítulos con efecto contractual = `MAJOR`. Puede apoyarse en `specification_verifier.py` (CAL-011, Anexo C), pero **el juicio de si un texto responde otra pregunta es del auditor**. | `TECHNICAL_SPECIFICATIONS_GUIDE.md` (4.4 a 4.8), `DOCUMENT_RULES.md` (RG-18), `TECHNICAL_SPECS`, `06-deliverables` |
| A4-14 | **Secuencia por paquetes:** ningún documento fue desarrollado antes que los paquetes de los que depende (la columna *Depende de* de la LME se respetó: cada paquete se empezó con sus dependencias `REVIEWED`; por ejemplo, ningún capítulo de pliego se redactó antes que los paquetes de cálculo que cita); cada paquete tiene su hoja de revisión con veredicto del usuario; no hay dos paquetes en `FOR_REVIEW` simultáneos salvo autorización registrada en una `DEC`. Evidencia: fechas de las hojas (`REVIEW-nn_YYYYMMDD_PQ-nn.md`), historial de estados y LME. Un documento desarrollado antes que su dependencia = `MAJOR` (salvo `[DEFINIR]` justificado en una `DEC`); un paquete sin hoja con veredicto = `MAJOR`. Para los planos y diagramas: el plano no se dibuja antes de que el paquete de sus insumos esté `REVIEWED` (se contrastan la *Fecha del estado* `DRAWN` de `drawing-status.md` y la fecha de la hoja de revisión de los insumos). | LME, `03-review/review-sheets`, `project-status.md` (C y L), `assumptions-and-decisions.md` |

**Planos y diagramas en `CAD_INPUT`.** El usuario dibuja los planos después de recibir los insumos y es quien anota su estado en `drawing-status.md`, de modo que en una auditoría anterior al dibujo el plano existe solo como insumos. Tratamiento: A1-13 es `N/A` hasta `DRAWN`; A4-02 verifica los insumos entregados (existen, su revisión coincide con la LME y no tienen datos pendientes injustificados); un plano en `CAD_INPUT` **no genera MAJOR por inexistente**, pero **sí impide la entrega del plano mismo**: la columna «Incluido en la entrega» de la LME debe mostrarlo fuera de la entrega (`Fuera de la entrega (PQ-nn)`, paquete posterior). Si un plano en `CAD_INPUT` figura incluido en la entrega objetivo, es un hallazgo MAJOR de alcance de entrega (`A4-01`).

### 4.5 A5 — Auditoría de trazabilidad

Se verifica la cadena **Objetivo → Requisito → Criterio de Ingeniería → Documento → Plano → Entregable**.

| ID | Verificación | Fuente de contraste |
|---|---|---|
| A5-01 | Cada objetivo `OBJ-` deriva en al menos un requisito. | `goals.md`, matriz |
| A5-02 | Cada requisito tiene fuente. | Matriz (Fuente) |
| A5-03 | Cada requisito tiene criterio de ingeniería aplicable, o justificación de ausencia. | Matriz (tabla B) |
| A5-04 | Cada requisito tiene documento; plano cuando corresponda. | Matriz |
| A5-05 | Cada requisito tiene entregable. | Matriz |
| A5-06 | Cada requisito `IMPLEMENTED` o `VERIFIED` tiene evidencia (tabla B completa). | Matriz (tabla B) |
| A5-07 | **Sin huérfanos:** ningún documento, plano o entregable sin requisito asociado. | LME, matriz |
| A5-08 | Sin IDs duplicados ni referencias inexistentes. | Todos los archivos |
| A5-09 | Estados coherentes con las reglas de la matriz (4.3). | Matriz |
| A5-10 | Verificación independiente de los requisitos críticos (seguridad y normativos obligatorios). | Tabla B |
| A5-11 | Cobertura: 100 % de los requisitos con estado definido; control de cobertura actualizado. | Matriz (sección C) |

## 5. Contraste cruzado obligatorio de parámetros

Para detectar **contradicciones**, se construye en cada auditoría una tabla de contraste con, como mínimo:

| Parámetro | Fuente maestra | Se contrasta en |
|---|---|---|
| Tensiones nominales (MT, BT) | `PAR-nnn` | Memorias, unifilares, especificaciones, listas de equipos, planos |
| Frecuencia, régimen de neutro | `PAR-nnn` | Memorias, cálculos de protección y puesta a tierra, unifilares |
| Potencias de transformadores y cargas | `PAR-nnn`, balance de cargas | Unifilares, listas de equipos, especificaciones |
| Niveles de cortocircuito | `PAR-nnn`, memoria de cortocircuito | Especificación de celdas y tableros, coordinación de protecciones |
| Secciones y tipos de cable | Memoria de conductores | Lista de cables, unifilares, planos, cómputos |
| Identificadores (TAG) | Lista de equipos / cables | Unifilares, planos, protocolos, tableros |
| Ajustes de protección | Planilla de ajustes | Estudio de coordinación, protocolos, as-built |
| Grados IP y ambiente | `PAR-nnn` | Especificaciones, hojas de datos |
| Cantidades | Cómputos | Planos, listados, órdenes de compra |
| Normas y ediciones citadas | `NOR-nnn` | Todos los documentos |
| Revisiones citadas | LME | Referencias cruzadas (al entregar: revisión exacta, `Rev 00`; en los documentos de trabajo: «revisión vigente») |

Toda diferencia es una **inconsistencia** y se reporta con ID, ubicación de ambas fuentes y propuesta de resolución.

## 6. Clasificación de hallazgos

| Severidad | Criterio | Efecto |
|---|---|---|
| `CRITICAL` | Riesgo de seguridad de personas; incumplimiento de norma o reglamento obligatorio; contradicción en dato maestro con impacto en el diseño; entregable contractual inexistente; requisito contractual no implementado. | Bloquea toda entrega y exige acción inmediata. |
| `MAJOR` | Requisito o criterio aplicable sin evidencia; inconsistencia entre documentos; error de cálculo con impacto; ítem `NO VERIFICABLE`; trazabilidad rota. | Bloquea la entrega hasta su cierre. |
| `MINOR` | Nomenclatura, formato, redacción, referencia imprecisa, sin efecto técnico. | No bloquea si tiene acción, responsable y fecha anterior a la próxima entrega o a ifc. |
| `OBSERVATION` | Oportunidad de mejora. | No bloquea. |

ID de hallazgo: `HAL-<nn auditoría>-<nnn>` (ej.: `EJ-HAL-01-007`; el prefijo `EJ-` solo se usa en los ejemplos de esta guía).

Cada hallazgo declara su severidad y si **bloquea la entrega** (`SÍ` para todo `CRITICAL` y `MAJOR`; `NO` para un `MINOR`, salvo que impida entregar un entregable incluido en la entrega) y quién debe actuar (`CLIENTE`, `INGENIERÍA` o `DOCUMENTAL`). No se exigen más campos de clasificación.

**Regla de no repetición:** un mismo hecho visto desde varias listas (A1…A5, contraste, entregables, requisitos) es **un solo hallazgo**; las demás listas lo referencian por ID.

### 6.1 Pendientes aceptados y fase de la entrega

La ausencia de una norma archivada en la biblioteca no bloquea por sí sola una emisión ifa si lo no verificado está declarado y aceptado. Severidad según la entrega objetivo:

| Situación | ifa | ifc o posterior |
|---|---|---|
| Valor normativo cuya norma está `SIN ARCHIVO`, marcado `[VERIFICAR]` y registrado como **pendiente aceptado** (`PA-nnn`: ID, fecha y firmante, en `project-status.md`, bloque B) | `OBSERVATION` | `MAJOR` |
| Otra marca abierta (`[DEFINIR]`, `[VERIFICAR]`, `INF-nnn`) registrada como pendiente aceptado | `OBSERVATION` | `MAJOR` |
| Marca abierta que **no** está registrada como pendiente aceptado | `MAJOR` (`NO VERIFICABLE`) | `MAJOR` |
| Valor normativo usado **sin marca ni fuente** | `MAJOR` | `MAJOR` |

El principio «nunca asumir conformidad» se mantiene: el informe lista todos los pendientes aceptados en la sección Pendientes aceptados del cuerpo, como **no verificados**, y la aceptación no los convierte en cumplidos.

## 7. Veredicto

| Veredicto | Condición | Efecto sobre el estado del proyecto |
|---|---|---|
| `APPROVED` | Sin hallazgos `CRITICAL`, `MAJOR` ni `MINOR` abiertos (solo `OBSERVATION`). | Puede pasar a `AUDITED` cuando el usuario dice `aprobar auditoría` |
| `APPROVED_WITH_comments` | Sin `CRITICAL` ni `MAJOR`; `MINOR` con acción comprometida (responsable y fecha). | Puede pasar a `AUDITED` cuando el usuario dice `aprobar auditoría`; los `MINOR` se verifican antes de ifc o en la siguiente auditoría de entrega |
| `NOT_APPROVED` | Al menos un `CRITICAL` o `MAJOR` abierto. | Con hallazgos que exigen trabajo de ingeniería: vuelve a `ENGINEERING`; se corrige y se re-audita. Sin ellos: el proyecto permanece en `FOR_AUDIT`; se cierran los ítems y se re-audita solo cada uno (regla 4) |

Reglas:

1. La auditoría solo se considera **completa** si se ejecutaron A1 a A5 sobre todo el alcance. Si no pudo ejecutarse alguna (por falta de información), el informe lo declara y el veredicto **no puede ser APPROVED**.
2. El veredicto emitido por Claude es una **auditoría técnica asistida**; la aprobación formal (firma) corresponde a la persona responsable (campo *Aprobación humana* del informe).
3. Una auditoría aprobada pierde validez para todo documento que se modifique después (siempre por rfc). Cada emisión (el ifa de cada fase y la ifc) tiene su propia auditoría: la aprobada para el ifa de una fase no habilita el de la siguiente ni la ifc.
3b. **Aprobación humana:** el estado `AUDITED` se registra recién cuando el usuario dice `aprobar auditoría`; el veredicto de Claude es una propuesta.
4. **Hallazgos con y sin trabajo de ingeniería.** *Trabajo de ingeniería* es todo el que modifica el contenido de un documento, cálculo o insumo (cambia su revisión). Un hallazgo sin ese trabajo (decisión del usuario, dato del cliente que aún no se volcó, definición del alcance de la entrega, actualización de registros de gestión) se cierra sin pasar por `ENGINEERING`. Estado del proyecto resultante: (a) solo hallazgos sin trabajo de ingeniería: permanece `FOR_AUDIT`; (b) algún hallazgo con trabajo de ingeniería: vuelve a `ENGINEERING` para esos ítems y, en paralelo, se cierran los otros; (c) cerrados todos los ítems, se re-audita solo lo corregido y sus dependencias como `AUD-nn+1` (re-auditoría parcial, que cita el informe de origen) y, sin bloqueantes abiertos, el proyecto pasa a `AUDITED`.

## 8. Plantilla de informe de auditoría

El informe es **simple y directo**: una sola página de lectura que responde *¿puedo entregar? Si no, ¿qué corrijo?*. Las listas de verificación A1 a A5 y el contraste de parámetros son **herramientas de trabajo del auditor**: el informe no las reproduce, solo reporta lo que no cumple. No se generan matrices ni tablas que no aporten una decisión. Se guarda como `AUD-nn_YYYYMMDD.md`.

### 8.1 Cuerpo (en este orden)

El informe es un documento del proyecto: Markdown compatible con Pandoc (`DOCUMENT_RULES.md`, RG-20 y 7.1). Lleva el bloque YAML de portada, un solo `#`, **títulos `##` sin numeración** y viñetas con `-`. Las secciones se citan por su nombre. Claude copia este esqueleto:

```markdown
---
title: "Informe de auditoría AUD-nn"
subtitle: "<Proyecto> — <Cliente>"
code: "AUD-nn"
revision: ""
status: "<APPROVED | APPROVED_WITH_comments | NOT_APPROVED>"
date: "AAAA-MM-DD"
---

# Informe de auditoría AUD-nn

## Identificación

Proyecto y cliente, fecha, tipo (ENTREGA / RE-ENTREGA / CIERRE), emisión objetivo y fase (ifa IC / IB / ID / IE, ifc, CIERRE), auditor y documentos auditados (código y revisión).

Líneas de lectura automática (cada una sola en su renglón; las leen `approve-audit.py` y `check-state.py`):

- `Emisión: ifa` (o `ifc`, `as-built`).
- `Paquetes: PQ-01, PQ-02` — **todo el conjunto de la emisión** (la auditoría es una sola por emisión; debe coincidir con los paquetes que están en `04-audit/audit-packages`).
- `Resultado: APPROVED` (o `APPROVED_WITH_comments`, `REJECTED`, `REJECTED_WITH_comments`). **Solo `APPROVED` permite pasar a `05-released`**; cualquier otro resultado devuelve a `02-engineering` los paquetes con hallazgos y la auditoría del conjunto se repite completa. `NOT_APPROVED` del veredicto histórico equivale a `REJECTED`.

## Resultado

- **Veredicto:** APPROVED / APPROVED_WITH_comments / NOT_APPROVED.
- **En una frase:** qué hay que corregir para poder entregar, o «sin observaciones relevantes».
- **Observaciones:** total, y cuántas son CRITICAL / MAJOR / MINOR / OBSERVATION. Bloquean la entrega las CRITICAL y MAJOR.

## Observaciones

Una por bloque, de mayor a menor severidad. Si no hay: «Ninguna detectada».

### HAL-nn-nnn — título corto

- **Documento:** código, revisión y sección.
- **Severidad:** CRITICAL / MAJOR / MINOR / OBSERVATION. Bloquea: SÍ / NO.
- **Problema:** el hecho, con la evidencia de ambas fuentes si es una contradicción («la memoria dice 240 mm²; el pliego dice 185 mm²»). Se declara que falta evidencia o que hay una contradicción; no se propone diseño.
- **Impacto:** qué consecuencia técnica, contractual o documental tiene.
- **Acción requerida:** qué hay que lograr (por ejemplo, «unificar el criterio en toda la documentación») y de quién (CLIENTE / INGENIERÍA / DOCUMENTAL).

## Pendientes aceptados

Solo si existen: lista de `PA-nnn` como **no verificados**, con la severidad que les corresponde (6.1).

## Para poder entregar

Si el veredicto no es APPROVED: los IDs bloqueantes en el orden sugerido de cierre, con responsable y fecha, y el estado resultante del proyecto (sección 7, regla 4). Si es APPROVED: «Sin bloqueantes: se puede entregar».

## Aprobación humana

Nombre, cargo, fecha y firma.

## Resultados por criterio (Anexo A)

Conteo OK / NO OK / N/A / NO VERIFICABLE de A1 a A5, y detalle solo de los ítems que no son OK.

## Contraste de parámetros (Anexo B)

Solo las excepciones (`Difiere` / `Pendiente`), con ambas fuentes. Los `Coincide` se resumen en un conteo.

## Verificaciones y herramientas (Anexo C)

Cálculos recomputados, scripts (`document_verifier.py`, `specification_verifier.py`, `ccpm.py`) y sus resultados.
```

### 8.2 Reglas del informe

1. Un hecho, un hallazgo, un ID: no se repite en otra sección (se referencia por ID).
2. Cada observación lleva siempre los cinco campos: documento, severidad, problema, impacto y acción requerida.
3. El cuerpo no lleva explicaciones largas: lo extenso va en los Anexos A a C, solo si hace falta.
4. Los riesgos que no son hallazgos se anotan en una línea en *Para poder entregar* o se envían al registro `RSK-`; no tienen sección propia.
5. Un informe `APPROVED` puede omitir las secciones sin contenido salvo Identificación, Resultado y Aprobación humana, y conserva el Anexo A.
6. Meta de longitud: cuerpo de una a dos páginas; informe completo de tres a seis.

## 9. Auditoría según la fase del proyecto

| Fase / estado objetivo | Foco adicional |
|---|---|
| ifa de cada fase (IC, IB, ID, IE) | Coherencia de datos maestros; supuestos abiertos; cobertura de requisitos del cliente; trazabilidad hasta documento y plano; planos incluidos `REVIEWED` en `drawing-status.md`; **madurez de cada entregable según la fase (A1-18)**. Los pendientes aceptados declarados se reportan como `OBSERVATION` (6.1). En el segundo ifa de la fase y siguientes: **alcance = lo nuevo y lo modificado**, con **A2-12** (comentarios del cliente cerrados, cada uno rastreado hasta la revisión que lo resuelve) y ningún documento cambiado sin `REV-nnn` o rfc. En el primer ifa de la fase, A2-12 es `N/A`. |
| ifc (al terminar la Ejecutiva, tras `cliente aprueba`) | Todo `MINOR` y `MAJOR` cerrados; entregables completos y en nivel Final (A1-18); listado de planos vigente (`drawing-status.md`); sin `[DEFINIR]`; los pendientes aceptados con norma sin archivo ya no se aceptan (6.1). Alcance: el conjunto completo, con consistencia cruzada entre todos los documentos; **A2-12 sobre los comentarios del cliente al último ifa**. |
| CONSTRUCTION | Correspondencia obra–ifc (evidencia de inspecciones y registros); gestión de cambios; redlines. |
| PRECOMMISSIONING / COMMISSIONING | Protocolos completos y firmados; criterios `ENG-PRE` / `ENG-COM`; lista de pendientes categorizada y cerrada según corresponda. |
| as-built → CLOSED (cierre) | Cada plano y listado actualizado o confirmado; informe de modificaciones vs. ifc; data book; trazabilidad al 100 %; ningún `NON_COMPLIANT` abierto; capacitación registrada. |

## 10. Ejemplo de uso (ilustrativo)

Al abrir la sesión se lee `project-status.md`: `Estado actual: FOR_AUDIT`, emisión objetivo ifa (fase IB). Claude congela el alcance (todos los paquetes de la entrega `REVIEWED`; 12 documentos, con revisiones), ejecuta A1 a A5 y detecta, entre otros:

- `EJ-HAL-01-003 — MAJOR — A3-07`: la memoria de cortocircuito (`ACM01-E-MC-002` Rev 00.0) usa 25 kA; la especificación de celdas (`ACM01-E-ET-001` Rev 00.0) exige 16 kA de poder de corte. Contradicción entre cálculo y especificación.
- `EJ-HAL-01-005 — MAJOR — A5-04`: el requisito `EJ-REQ-SEG-001` no tiene plano asociado.
- `EJ-HAL-01-009 — MINOR — A1-03`: la portada de `ACM01-E-MD-001` indica Rev 00.0 y el nombre de archivo Rev 00.1 (sin `rfc-001` que lo justifique).

Veredicto: `NOT_APPROVED`. El estado vuelve a `ENGINEERING`. El informe abre con el resultado («3 bloqueantes: EJ-HAL-01-003, EJ-HAL-01-005, EJ-HAL-01-011»), describe cada observación con documento, problema, impacto y acción requerida, indica el orden de cierre y deja el respaldo en anexos breves.

## 11. Buenas prácticas

- Auditar con la lista completa, no de memoria.
- Citar evidencia por código, revisión y sección.
- Verificar las correcciones de hallazgos, no solo el compromiso de corregirlos.
- No dejar `NO VERIFICABLE` sin plan de obtención de evidencia.
- Mantener la tabla de contraste de parámetros actualizada entre auditorías.
- Auditar temprano y parcialmente durante la ingeniería: la auditoría formal no debe ser la primera vez que se ven los problemas.
- Mantener el tono del informe en hechos y evidencia, sin juicios sobre personas.

---

# REGISTROS DE AUDITORÍA Y AVANCE

Los registros de informes de avance, de auditorías y de hallazgos abiertos **no viven en este archivo** (que es una guía y no se edita): están en `90-management/audit-register.md`. Lo completa el gestor del proyecto al recibir cada informe (sección 3.2, paso 7).
