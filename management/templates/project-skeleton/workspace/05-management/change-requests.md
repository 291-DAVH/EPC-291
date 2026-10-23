# change-requests.md — Registro de rfc (Solicitudes de Cambio)

| Campo | Valor |
|---|---|
| Proyecto | `[DEFINIR]` |
| Versión | 1.2 |
| Fecha | 2026-10-07 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Garantizar que **todo cambio** (de alcance, requisito, dato de entrada, diseño, plazo o documento) se solicite, se registre con **evidencia**, se evalúe, se **resuelva** (aprobado, rechazado o diferido) y se cierre con verificación. Un cambio sin solicitud registrada no se implementa.

La solicitud se llama **rfc** (*Request for Change* / Solicitud de Cambio) y se identifica `rfc-nnn`. La rfc se reserva para cambios que modifican **línea base, alcance, requisitos del cliente, parámetros maestros, filosofía de operación, criterios de diseño, potencias, equipamiento aprobado o decisiones registradas**; un error documental, una omisión o un problema de representación es una **corrección documental** que no genera rfc. En ambos casos el comentario se registra como `REV-nnn` (con su origen: INTERNO, CLIENTE o AUDITORÍA) y suma a la revisión del documento. **La `rfc-n` fija el dígito central de la revisión: `00.n`** (`rfc-001` → `00.1`, `rfc-002` → `00.2`) y reinicia el último dígito; cada comentario posterior suma 1 (`00.1.1`, `00.1.2`…). Esa numeración es interna y el cliente siempre ve `Rev 00` (`DOCUMENT_RULES.md`, sección 9).

## 2. Alcance

Aplica a cambios originados por el cliente, el usuario, la auditoría, la obra, los proveedores o la propia ingeniería, en cualquier estado del proyecto, incluso después de la construcción (cuando el cambio modifica lo construido, ver `DOCUMENT_RULES.md`, sección 9). **No reemplaza** al registro de comentarios (`REV-nnn`) ni a los hallazgos de auditoría (`HAL-`): todo comentario, del cliente, del jefe, del usuario o del auditor, se registra como `REV-nnn` y Claude propone si es **rfc** o **corrección documental**; el usuario lo confirma con `confirmar clasificación`. Las rfc se tramitan con este archivo; las correcciones documentales se incorporan directamente, suman 1 a la revisión y vuelven a revisión interna (ifr) antes de reemitirse al cliente, sin excepciones.

## 3. Forma de utilización

1. **Recepción:** cuando llegue un pedido de cambio (correo, acta, comentario del cliente, instrucción de obra, decisión del usuario), Claude abre `rfc-nnn` en la sección A el mismo día y **guarda la evidencia** en `90-management/rfc/rfc-nnn/` (en la plantilla C: `90-management/rfc/rfc-nnn/`): el archivo original sin modificar, con nombre `YYYYMMDD_origen_descripcion`. Si el pedido fue verbal, el usuario lo confirma y Claude lo transcribe como acta con fecha y autor.
2. **Evaluación de impacto:** Claude completa la sección B: alcance (`ALD-`, `EXC-`), requisitos (`CR-`, `REQ-`), documentos y planos afectados (códigos de la LME), criterios `ENG-`, supuestos y decisiones, cronograma (consumo del buffer de proyecto, ver `schedule-ccpm.md`), riesgos y costo si el contrato lo exige. El costo y las condiciones comerciales no se tratan en documentos de ingeniería (`RG-05`); solo se indica «tiene impacto comercial: sí/no».
3. **Resolución:** el usuario decide con una frase fija: `aprobar rfc [rfc-nnn]` (`APPROVED`), `rechazar rfc [rfc-nnn]` (`REJECTED`) o `diferir rfc [rfc-nnn]` (`DEFERRED`); la decisión también puede darse en la **parte B de la hoja de revisión** (tipo `rfc`, respuestas `ACEPTO` / `RECHAZO` / `DIFERIR`, ver `review-sheet.md`) o por escrito. Hasta que responda, **los documentos afectados no se modifican por esa rfc** (el `REV-nnn` queda `OPEN`). La decisión se registra como `DEC-nnn` en `assumptions-and-decisions.md` con la `rfc-nnn` como origen. Un rechazo se comunica con su motivo y queda con evidencia (carta o correo). Si el cambio modifica la línea base, se actualiza `project-information.md`, sección O.
4. **Implementación:** con la `rfc` en `APPROVED`, Claude actualiza los datos maestros, genera la **`Rev 00.n` (n = número de la rfc; el último dígito vuelve a 0)** de cada documento afectado (y de los que usan el dato modificado), con la `rfc-00n` citada en su control de revisiones, archiva la revisión superada, entrega insumos actualizados para los planos (los dibuja el usuario), recorre la **lista de propagación** (punto 8), y deja el paquete afectado en `FOR_REVIEW` (los paquetes dependientes `REVIEWED` que usan el dato modificado se reabren de a uno con una hoja corta de impacto, `review-sheet.md`, 7.1).
5. **Verificación y cierre:** la auditoría verifica que cada documento afectado refleja el cambio y que no quedaron inconsistencias; recién entonces la `rfc` pasa a `CLOSED` con la evidencia de implementación (códigos y revisiones) y de verificación (`AUD-nn` o `REV-nnn` verificado).
6. **Cambios posteriores a la entrega o a la obra.** Los **comentarios del cliente** a una emisión (`comentarios del cliente recibidos`) se registran como `REV-nnn` y se clasifican (`confirmar clasificación`): cada tema que cumple los criterios de rfc abre una rfc. Mientras haya comentarios abiertos no se prepara la emisión siguiente (`CLAUDE.md`, sección 11); los documentos afectados vuelven siempre a revisión interna (ifr) y a auditoría de lo cambiado antes del nuevo ifa. Si el documento ya fue entregado, la modificación sigue `DOCUMENT_RULES.md`, sección 9, y se reentrega rotulado `Rev 00` con otro `TR-nnn`. Si ya se construyó y el cambio es físico (por ejemplo un tablero nuevo), el cambio queda registrado en la Ejecutiva actualizada y, en el as-built, como instalado / motivo / acta de cambio; el proyecto completo pasa a la siguiente revisión (`Rev 02`, `03`…; secuencial del proyecto) y se vuelve a entregar el juego documental de cierre.
7. Una `rfc` `REJECTED` o `DEFERRED` no se borra: queda en el registro como historia y **no genera revisión** (su `n` queda sin usar en los documentos que habría afectado). Si dos rfc afectan al mismo documento, se aplican en el orden de su número. Si una rfc afecta solo a algunos documentos, el resto conserva su revisión: un documento puede saltar de `00.0.3` a `00.2`.
8. **Lista de propagación de un cambio de alcance.** Al implementar una `rfc` que agrega, quita o modifica alcance, requisito o dato maestro, se revisa y se actualiza cada archivo de esta lista, y la sección C deja constancia de que se recorrió:

   | N.º | Archivo y sección | Qué se revisa |
   |---|---|---|
   | 1 | `goals.md` | Objetivos (`OBJ-`), criterios de éxito (`CRI-`) |
   | 2 | `client-requirements.md` | Requisitos (`CR-`), conflictos (sección K), historial de cambios del cliente (sección M) |
   | 3 | `project-information.md` | Parámetros (`PAR-`) e instalaciones afectadas |
   | 3b | `project-scope.md` y `project-charter.md` | Alcance por disciplina (`ALD-`), exclusiones (`EXC-`), criterios de aceptación (`CAC-`) y línea base (el charter se regenera con nueva versión) |
   | 3c | `starting-data.md` | Datos declarados (fases, entregables, plazo, modo de gestión), si el cambio los toca |
   | 4 | `assumptions-and-decisions.md` | `DEC` de resolución; supuestos afectados |
   | 5 | `traceability-matrix.md` | Tablas A, B y B2, cobertura (C) y huérfanos (D) |
   | 6 | `deliverables.md` | LME (entregables nuevos o dados de baja), entrega incluida, resumen de control |
   | 7 | `schedule-ccpm.md` | Tareas, cadena crítica y buffer (recalcular) |
   | 8 | `engineering-standards.md` | Columna *Aplica* de los criterios afectados |
   | 9 | `project-status.md` | Estado, bloqueos, `INF` y pendientes aceptados |
   | 10 | Documentos y planos afectados | `Rev 00.n` (n = número de la rfc) e insumos actualizados |
| 11 | `drawing-status.md` | Planos afectados: Claude propone una observación o una fila nueva; el estado del plano lo cambia el usuario |

## 4. Estructura recomendada

| Estado | Significado |
|---|---|
| `OPEN` | Registrada, con evidencia; en evaluación |
| `EVALUATED` | Impacto evaluado; pendiente de decisión del usuario |
| `APPROVED` | Aprobada; en implementación |
| `REJECTED` | Rechazada, con motivo y comunicación |
| `DEFERRED` | Diferida a una fecha o hito (se indica cuál) |
| `IMPLEMENTED` | Documentos actualizados, pendientes de verificación |
| `CLOSED` | Verificada por auditoría o revisión |

Origen: `CLIENTE`, `USUARIO`, `AUDITORIA`, `OBRA`, `PROVEEDOR`, `INGENIERIA`. Prioridad: `ALTA`, `MEDIA`, `BAJA`.

## 5. Ejemplos (ilustrativos)

- El cliente pide por correo subir la iluminancia de un depósito de 150 a 200 lx (es la `EJ-rfc-003`): se guarda el correo en `90-management/rfc/EJ-rfc-003/`, se evalúa el impacto (cantidad de luminarias, carga sobre el interruptor, plazo), el usuario dice `aprobar rfc EJ-rfc-003`, se registra `DEC-nnn`, la memoria de iluminación y la especificación pasan de `Rev 00.0` a `Rev 00.3`, se actualizan los insumos de los planos y la auditoría de la entrega siguiente lo verifica. El listado de luminarias, que no depende de ese dato, conserva `Rev 00.0`.
- En obra se instala un tablero adicional no previsto: `rfc-nnn` con origen `OBRA`, foto y orden de trabajo como evidencia; si el proyecto ya está en `Rev 01` (as-built), los documentos afectados pasan a la revisión siguiente del proyecto completo (`Rev 02`), con la rfc citada en el control de revisiones.

## 6. Buenas prácticas

- Registrar el cambio **antes** de trabajar en él, no después.
- Una solicitud, un tema; si un correo trae tres pedidos, se abren tres `rfc`.
- Citar siempre la evidencia por nombre de archivo y fecha.
- Medir el impacto en el buffer de proyecto del cronograma; un cambio que consume buffer se informa al usuario de inmediato.
- Revisar en cada informe de avance las `rfc` abiertas con más de cinco días hábiles sin decisión.

---

# REGISTRO DE rfc (completar)

## A. Registro

| ID | Fecha de recepción | Origen | Solicitante | Descripción del cambio | Evidencia (ruta en `90-management/rfc/rfc-nnn/`) | Prioridad | Estado | Decisión (`DEC-nnn`) | Fecha de resolución |
|---|---|---|---|---|---|---|---|---|---|
| rfc-001 | | | | | | | | | |

## B. Evaluación de impacto

| ID | Alcance / línea base | Requisitos (`CR-`, `REQ-`) | Documentos y planos afectados | Criterios `ENG-` / supuestos | Impacto en cronograma (días de buffer) | Impacto comercial (sí / no) | Riesgos |
|---|---|---|---|---|---|---|---|
| rfc-001 | | | | | | | |

## C. Implementación y verificación

| ID | Documentos actualizados (código y revisión: `Rev 00.n` con `n` = número de la rfc, o `00.n.c` con los comentarios posteriores; `Rev 02` y siguientes tras el as-built) | Lista de propagación recorrida (punto 8; archivos tocados) | Matriz y LME actualizadas | Evidencia de verificación (`AUD-nn` / `REV-nnn`) | Fecha de cierre |
|---|---|---|---|---|---|
| rfc-001 | | | | | |
