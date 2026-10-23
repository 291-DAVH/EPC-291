# Módulo M6 — Estados y puertas de calidad

> Módulo de `CLAUDE.md` (secciones 11 y 11.1). Tiene la **misma autoridad** que `CLAUDE.md`: el texto se movió aquí, sin cambios de fondo, para que `CLAUDE.md` se lea corto en cada sesión. La numeración de las secciones se conserva, de modo que las referencias «`CLAUDE.md`, 8.1» y similares siguen valiendo. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica.

---

## 11. Estados y puertas de calidad

> **Desde la reestructuración (WF-001) el estado de un paquete es su ubicación física** y las transiciones de esta sección se ejecutan con los scripts de `.claude/hooks/` (sección 11.2). Si esta sección y 11.2 difieren en el *cómo*, prevalece 11.2; las condiciones de fondo (qué debe cumplirse) son las mismas, con la regla adicional de que **solo `APPROVED` avanza**.

Estados permitidos del proyecto (detalle en `project-status.md`):

`planning → ENGINEERING → FOR_REVIEW → INTERNAL_REVIEW → FOR_AUDIT → AUDITED → ifa → ifc → CONSTRUCTION → PRECOMMISSIONING → COMMISSIONING → as-built → CLOSED`

`ifr` **no es un estado del proyecto**: es la emisión interna de los documentos mientras están en revisión (`FOR_REVIEW` a `AUDITED`). El proyecto tiene además la anotación **fase de ingeniería** (`IC`, `IB`, `ID`, `IE`, `ASB`; `project-status.md`, sección A) y el ciclo «paquetes `REVIEWED` → auditoría → entrega → revisión del cliente» se repite en cada fase (4.3).

Diagrama (cada fase repite el recorrido «paquetes `REVIEWED` → auditoría → entrega al cliente → aprobación»):

```text
planning ─► ENGINEERING ⇄ FOR_REVIEW ⇄ INTERNAL_REVIEW        (ciclo por paquete; documentos en ifr; cada comentario = REV-nnn)
 (fase IC/IB/ID)   │
                      ▼ todos los paquetes de la fase REVIEWED (+ comentarios del cliente al ifa anterior cerrados)
                  FOR_AUDIT ─► AUDITED (aprobado internamente) ─► entregar ifa ─► entrega enviada TR-nnn ─► ifa  (esperando al cliente)
                                                                                     │ comentarios del cliente recibidos → REV-nnn → rfc o corrección documental
                                                                                     │   → ENGINEERING (lo afectado vuelve a ifr) → FOR_AUDIT → AUDITED → nuevo ifa
                                                                                     ▼ cliente aprueba
                                                                         ENGINEERING en la fase siguiente (IC → IB → ID → IE)
 (fase IE)   FOR_AUDIT ─► AUDITED ─► entregar ifc ─► entrega enviada TR-nnn ─► ifc ─► CONSTRUCTION ─► PRECOMMISSIONING
                                                                             ─► COMMISSIONING ─► as-built (Rev 01) ─► CLOSED
```

**El ciclo `ENGINEERING ⇄ FOR_REVIEW (⇄ INTERNAL_REVIEW)` ocurre por paquete de revisión.** `FOR_REVIEW` significa que hay **un** paquete esperando al usuario (nunca dos, salvo autorización explícita registrada en una `DEC`). Al cerrar el paquete (todo `OK`) sus documentos pasan al estado documental `REVIEWED` (revisado: OK del usuario, pendiente de auditoría y de entrega) y el proyecto vuelve a `ENGINEERING` para el paquete siguiente. El estado documental `REVIEWED` no es un estado del proyecto (`project-status.md`, 4.3). El paso a `FOR_AUDIT` ocurre cuando **todos** los paquetes incluidos en la emisión objetivo (ifa o ifc) de la fase están `REVIEWED`.

**Emisiones al cliente (ifa, ifc) y fases.** Cada emisión exige que su alcance esté `AUDITED` (**una auditoría propia por emisión**, no una sola para todo el proyecto): `AUDITED` equivale a **aprobado internamente**. Tras `entrega enviada TR-nnn` el proyecto queda en `ifa` *esperando al cliente*. Los comentarios del cliente se registran como `REV-nnn` y se tratan como rfc o como corrección documental (4.3); en ambos casos los documentos afectados **vuelven a ifr**: revisión interna del paquete por el usuario y auditoría de lo cambiado, y recién entonces un nuevo ifa. Esto ocurre siempre, sin excepciones. Con **`cliente aprueba`** la fase queda aprobada y dispara la siguiente (`IC → IB → ID → IE`): Claude propone su plan de paquetes y el proyecto vuelve a `ENGINEERING`. En `IE` el conjunto aprobado internamente se emite como ifc y el proyecto pasa a `CONSTRUCTION`. Si el cliente no responde, el silencio **no** cierra la instancia por sí solo: la cierra únicamente `cliente aprueba` con una `DEC` y su evidencia (la aprobación expresa o, si el cliente no responde, la constancia de su llamada telefónica al cliente: fecha, persona y lo acordado). El orden de fases solo se altera por una `DEC` `[VERIFICAR]`.

Reglas de puerta:

| Transición | Condición obligatoria |
|---|---|
| ENGINEERING → FOR_REVIEW | **Un** paquete generado según `deliverables.md` (los paquetes de los que depende están `REVIEWED`), autocontrol de cierre documental de cada documento y del paquete completo (8.3, punto 7) realizado y hoja de revisión del paquete entregada. Lo hace Claude, que se detiene. No hay otro paquete en `FOR_REVIEW`. |
| FOR_REVIEW → INTERNAL_REVIEW | **Solo el usuario:** inicia la revisión del paquete. La revisión empieza cuando el usuario devuelve la hoja (primera respuesta o frase de cierre), o cuando dice `empezar revisión`; Claude lo anota en el historial de estados. Los comentarios se registran como `REV-nnn`. |
| INTERNAL_REVIEW → FOR_REVIEW (paquete con comentarios) | Claude procesó los comentarios del paquete (`procesar comentarios de revisión`): cada `REV-nnn` incorporado suma 1 al último dígito de la revisión de los documentos afectados y de los que usan un dato modificado (`00.0` → `00.0.1`; la revisión superada se archiva en `ARCHIVE` con estado `SUPERSEDED`; actualizar solo una referencia cruzada no suma; `DOCUMENT_RULES.md`, sección 9), y entregó una **nueva hoja del mismo paquete** con solo lo cambiado. Lo hace Claude; en el historial se anota un solo asiento por sesión y paquete. |
| FOR_REVIEW / INTERNAL_REVIEW → ENGINEERING (rechazo) | **Solo el usuario:** `rehacer`. Vuelve **solo ese paquete**; se rehace lo rechazado y se entrega una hoja nueva del mismo paquete. |
| INTERNAL_REVIEW → ENGINEERING (paquete cerrado) | **Aprobación del usuario del paquete** (`revisión aprobada`): comentarios `REV-nnn` del paquete cerrados, parte B respondida y trazabilidad del paquete actualizada. Los documentos del paquete pasan a `REVIEWED` (con la revisión que tengan, `00.0` o `00.0.c`, hasta que una rfc o un comentario posterior los cambie) y el proyecto vuelve a `ENGINEERING` para el paquete siguiente (o a `planning` si no queda ningún paquete por desarrollar y hay que definir el plan, p. ej. por bloqueos). Si el usuario aprueba estando en `FOR_REVIEW`, se registra en el historial el paso por `INTERNAL_REVIEW`. Claude propone el paquete siguiente según el grafo; el usuario confirma o reordena con una frase fija. |
| Cambio aguas arriba (paquete `REVIEWED` que cambia) | Desde `REVIEWED`, todo cambio nace de un comentario `REV-nnn` (del usuario, del cliente o de la auditoría) y es una **rfc** o una **corrección documental** (4.3). Con la rfc aprobada, el paquete pasa a `Rev 00.n`; con una corrección documental, a `00.R.C+1`. En ambos casos los paquetes dependientes `REVIEWED` que **usan el dato modificado** quedan `REABIERTO` y vuelven a `FOR_REVIEW` de a uno, en el orden del grafo, mediante una hoja corta que indica «qué cambió / por qué afecta» (`review-sheet.md`, 7.1); también se actualiza su revisión con el mismo origen. Los que solo citan al documento modificado (citan la «revisión vigente») no cambian. |
| ENGINEERING → FOR_AUDIT | **Todos** los paquetes incluidos en la emisión objetivo (ifa o ifc) de la fase están `REVIEWED` (ninguno `REABIERTO`), comentarios `REV-nnn` cerrados, matriz de trazabilidad actualizada y **confirmación del usuario** (`auditar`, o `SÍ` a «¿auditar la entrega?» en la última hoja). Desde el segundo ifa, además, los comentarios del cliente al ifa anterior están cerrados (ver arriba). Claude lo propone al cerrar el último paquete; no lo hace por sí mismo. Al entrar en `FOR_AUDIT`, los documentos del alcance de la auditoría pasan a estado documental `FOR_AUDIT`. |
| FOR_AUDIT → AUDITED | Auditoría completa **de esa emisión**, una sola vez, con veredicto APPROVED o APPROVED_WITH_comments, sin hallazgos CRITICAL/MAJOR abiertos, **y aprobación humana del informe** (`aprobar auditoría`): Claude propone `AUDITED`, pero solo el usuario lo habilita. `AUDITED` es el «aprobado internamente» que habilita enviar al cliente. |
| FOR_AUDIT → ENGINEERING | Veredicto NOT_APPROVED con al menos un hallazgo abierto que exige trabajo de ingeniería (modificar un documento, cálculo o insumo). El hallazgo se trata como `REV-nnn` (origen AUDITORÍA): **rfc** si modifica algo de la lista de 4.3, **corrección documental** si no. Con la rfc aprobada (o la corrección confirmada), el documento cambia de revisión, el paquete que lo contiene vuelve a `DRAFT` y se aplica la regla de cambio aguas arriba a sus dependientes. |
| FOR_AUDIT → FOR_AUDIT (permanece) | Veredicto NOT_APPROVED con hallazgos que **no** exigen trabajo de ingeniería (decisión del usuario, dato del cliente, alcance de la entrega, registros de gestión): se cierran sin pasar por `ENGINEERING` y se re-audita solo cada ítem (`project-audit.md`, sección 7). |
| AUDITED → ifa / ifc | Solo desde `AUDITED`, en dos pasos: `entregar ifa` (o `ifc`): Claude arma el paquete limpio en `06-deliverables` y el transmittal borrador (la depuración de DWG y PDF la hace el usuario; solo entran los planos `REVIEWED` en `drawing-status.md`); y `entrega enviada TR-nnn`: el usuario confirma que lo envió al cliente y **recién entonces** el estado pasa a `ifa` / `ifc`. No existe emisión al cliente sin auditoría. |
| ifa → ENGINEERING | (a) Comentarios del cliente (`comentarios del cliente recibidos`) tratados como rfc aprobadas o correcciones documentales confirmadas: los documentos afectados vuelven a ifr y los paquetes a `ENGINEERING`; o (b) `cliente aprueba`: arranca la fase siguiente. El proyecto conserva la anotación de la emisión pendiente de cierre (`project-status.md`, sección A). |
| ifa → FOR_AUDIT | Comentarios del cliente cerrados (`REV-nnn` resueltos: rfc `CLOSED`, `REJECTED` o `DEFERRED` con `DEC`, o corrección documental incorporada), todos los paquetes afectados `REVIEWED` de nuevo y `auditar`: se audita lo cambiado y se verifica que los comentarios quedaron resueltos. |
| ifc → CONSTRUCTION | `entrega enviada` del ifc y `pasar a CONSTRUCTION`. Un comentario posterior del cliente o de obra a lo emitido en ifc se trata como rfc o corrección documental (origen OBRA, con foto y orden de trabajo), vuelve a ifr y exige reemisión ifc con su propia auditoría; la Ejecutiva se mantiene actualizada hasta `iniciar as-built`. |
| CONSTRUCTION → PRECOMMISSIONING → COMMISSIONING | `pasar a [ESTADO]` con la condición de entrada de `project-status.md`, 4.1. Cada cambio de obra se tramita como rfc (origen `OBRA`). |
| COMMISSIONING → as-built | `iniciar as-built`: la Ejecutiva actualizada con los cambios de obra es la base de la documentación conforme a obra (fase `ASB`): cada documento registra lo instalado, el motivo del cambio y su acta (`rfc-nnn` o acta del cliente). Al completarse, todo el proyecto pasa a `Rev 01` (`entregar as-built` y `entrega enviada TR-nnn`). |
| as-built → CLOSED | Auditoría de cierre aprobada (entregables, as-built, trazabilidad al 100 %) con `aprobar auditoría`, lecciones extraídas y `cerrar proyecto`. |

### 11.1 Estado `FOR_REVIEW` (PARA REVISAR)

`FOR_REVIEW` indica al usuario que **hay un paquete que debe revisar**. Es el estado en que queda el proyecto cada vez que Claude termina de generar un paquete.

Al entrar en `FOR_REVIEW`, Claude ejecuta `send-to-review.py PQ-nn` (mueve el paquete a `03-review/review-packages`, lo congela con su manifiesto de hashes) y luego:

1. Marca cada documento del paquete como `FOR_REVIEW` en `deliverables.md` y `project-status.md`. En un plano, el documento revisable es el de **insumos de dibujo**; el plano queda `CAD_INPUT` en `drawing-status.md` (Claude propone la fila) hasta que el usuario lo dibuje y actualice esa fila a `DRAWN`.
2. Genera la **hoja de revisión del paquete** `03-review/review-sheets/REVIEW-nn_YYYYMMDD_PQ-nn.md` con la plantilla de `review-sheet.md`: parte A (los documentos del paquete —de 1 a 3— con ruta, prioridad y 3 a 5 puntos concretos a mirar), parte B (supuestos, decisiones, datos y marcas `[DEFINIR]` / `[VERIFICAR]` **de ese paquete** que necesitan respuesta del usuario), parte C (cierre). En `project-status.md`, sección L, registra solo la ruta de la hoja, la fecha y los conteos (no repite el contenido de la hoja, que es la fuente única).
3. Informa al usuario con un mensaje corto: qué paquete se generó, qué debe revisar, dónde está la hoja y cuál sería el paquete siguiente (informativo).
4. **Se detiene.** No auto-aprueba, no desarrolla otro paquete (ni siquiera en paralelo), no avanza a `FOR_AUDIT` ni entrega documentos.

El usuario responde **en la hoja de revisión** (o con `guiar revisión` en el chat, o dictando comentarios); al devolver la primera respuesta el proyecto pasa a `INTERNAL_REVIEW`. Claude transcribe los comentarios a `REV-nnn` en la sección M de `project-status.md`. Un documento sin veredicto del usuario no se da por revisado. Con `procesar comentarios de revisión`, Claude los incorpora (cada comentario suma 1 al último dígito de la revisión: `00.0` → `00.0.1`) y devuelve el paquete a `FOR_REVIEW` con una nueva hoja del mismo paquete. Con `revisión aprobada`, el paquete queda `REVIEWED` y el proyecto vuelve a `ENGINEERING` para el siguiente; la auditoría se pide aparte, con `auditar`, cuando están `REVIEWED` todos los paquetes de la entrega.

Cualquier cambio posterior a una auditoría que afecte documentos auditados (siempre con su `REV-nnn`: rfc o corrección documental) **invalida** la auditoría para esos documentos y obliga a re-auditar el alcance afectado.

### 11.2 Flujo por ubicación: el estado es dónde está el paquete

| Ubicación | Estado del paquete | Qué ocurre ahí |
|---|---|---|
| `02-engineering` | `ENGINEERING` (documento `DRAFT` / `REABIERTO`) | Único lugar donde se edita. Todo paquete modificado vuelve aquí |
| `03-review/review-packages/PQ-nn` | `FOR_REVIEW` (`INTERNAL_REVIEW` mientras el usuario responde la hoja) | Congelado: hash SHA-256 registrado. Revisión del usuario con la hoja `REVIEW-nn_YYYYMMDD_PQ-nn.md` |
| `04-audit/audit-packages/PQ-nn` | `FOR_AUDIT` | Congelado. La auditoría se hace **una sola vez por emisión**, con todo el conjunto aquí |
| `05-released/PQ-nn` | `AUDITED` / `RELEASED` | Aprobado internamente por auditoría; listo para emitir. Congelado |
| `06-deliverables/<emisión>/…` | `ifa` / `ifc` / `as-built` (tras `entrega enviada`) | Copia rotulada `Rev 00` (as-built `Rev 01`), solo lectura. No es un movimiento |

**Resultados y avance.** La hoja de revisión y el informe de auditoría llevan un campo `Resultado:` con uno de cuatro valores. **Solo `APPROVED` permite avanzar.** `APPROVED_WITH_comments`, `REJECTED` y `REJECTED_WITH_comments` devuelven el paquete a `02-engineering` (`return-to-engineering.py`), donde se incorporan los cambios, y **el ciclo se reinicia completo**: nueva revisión, nueva auditoría del conjunto. No hay atajos ni excepciones. Todo paquete modificado vuelve a Ingeniería; todo paquete no modificado avanza.

**Quién hace qué.** Claude ejecuta los scripts; no mueve documentos a mano. Escribe el `Resultado:` de la hoja **solo** cuando el usuario dicta su decisión (`revisión aprobada` ⇒ `APPROVED`; `procesar comentarios de revisión` ⇒ `APPROVED_WITH_comments`; `rehacer` ⇒ `REJECTED` o `REJECTED_WITH_comments`). El `Resultado:` del informe de auditoría lo fija la auditoría; el usuario lo hace efectivo con `aprobar auditoría`.

| Frase / momento | Script |
|---|---|
| Paquete desarrollado, con autocontrol hecho | `send-to-review.py PQ-nn` y se entrega la hoja de revisión (Claude se detiene) |
| `revisión aprobada` | Claude anota `Resultado: APPROVED` en la hoja → `send-to-audit.py PQ-nn` |
| `procesar comentarios de revisión` / `rehacer` | Claude anota el `Resultado:` → `return-to-engineering.py PQ-nn --motivo …`; incorpora los cambios; vuelve a `send-to-review.py` |
| `auditar` (todos los paquetes de la emisión en `04-audit`) | Auditoría única del conjunto → informe `AUD-nn` con `Emisión:`, `Paquetes:`, `Resultado:` |
| `aprobar auditoría` | `approve-audit.py --emision X`; si el resultado no era `APPROVED`: `return-to-engineering.py` de los paquetes con hallazgos |
| `entregar ifa` / `entregar ifc` | `release-documents.py --emision X` → `issue-ifa.py` / `issue-ifc.py` (el usuario depura DWG y PDF) |
| `entrega enviada TR-nnn` | `confirm-sent.py TR-nnn` |
| `iniciar as-built` | `start-asbuilt.py` |
| `entregar as-built` | `release-documents.py --emision as-built` → `issue-asbuilt.py` |
| `cerrar proyecto` | `close-project.py` |
| Inicio de sesión y antes de auditar | `check-state.py` (ubicación, hashes, copias sueltas, siguiente paso) |

**Dependencias.** Un paquete no se envía a revisión si alguno de los paquetes de los que depende (*Depende de* en la LME) está en `02-engineering` o su revisión aún no está aprobada (`REVIEWED`). Si un paquete vuelve a Ingeniería, los que dependen de él y usan el dato modificado vuelven también (`--con-dependientes`); los que solo lo citan (revisión vigente) no cambian. Si un paquete ya liberado vuelve a Ingeniería, la auditoría de su emisión queda invalidada y sus hermanos no emitidos regresan a `04-audit`.

**Planos (DWG).** El usuario entrega DWG + xref + PDF; los tres se congelan juntos en el paquete y evitan que alguien modifique el DWG durante la revisión o la auditoría. **Claude revisa y audita el PDF; nunca abre el DWG ni los xref.** Un DWG sin su PDF no entra al paquete. Los insumos de dibujo (`_DIN_`) son internos y no se emiten.

**Información de gestión generada por Claude** (cronograma, planes, informes, lecciones, registros) es **propuesta** hasta que el usuario la valida; Claude no posee autoridad de aprobación.

