# project-status.md — Estado del Proyecto

> **REGLA OBLIGATORIA:** cuando el campo *Estado actual* de este archivo sea `FOR_AUDIT`, Claude ejecuta automáticamente la auditoría completa definida en `project-audit.md`, con toda la documentación disponible, antes de cualquier otra tarea. Nunca se asume conformidad; siempre se exige evidencia.

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Registrar en un único lugar en qué fase está el proyecto, qué se completó, qué está en curso, qué está pendiente o bloqueado y cuáles son los próximos pasos. Es el **punto de entrada de cada sesión de trabajo** y el **disparador del sistema de auditoría**.

## 2. Alcance

Estado del proyecto y de sus documentos. No registra decisiones técnicas (ver `assumptions-and-decisions.md`) ni resultados de auditoría detallados (ver `project-audit.md`).

## 3. Forma de utilización

1. Actualizar al terminar cada sesión de trabajo y en cada cambio de estado.
2. Cambiar de estado solo si se cumplen las **condiciones de salida** de la tabla 4.1.
3. Para pedir auditoría: con **todos los paquetes de la entrega objetivo en `REVIEWED`** (y, desde el segundo ifa de una fase, los comentarios del cliente al ifa anterior cerrados), cambiar el estado a `FOR_AUDIT` (el usuario lo confirma con `auditar`) y completar el bloque *Solicitud de auditoría*. El paso a `AUDITED` exige además `aprobar auditoría` del usuario.
4. El trabajo avanza **por paquete de revisión** (`PQ-nn`, `deliverables.md`, 4.1): este archivo informa en la sección A el paquete actual, cuántos paquetes están revisados y cuál se propone después.
5. El estado individual de cada documento **no se repite aquí**: se deriva del `ledger` (ubicación del paquete) y de `deliverables.md`. Los riesgos tampoco se repiten: viven en el registro `RIE-nnn` de `assumptions-and-decisions.md` y se resumen en el informe de estado. El estado de **cada plano o diagrama dibujado por el usuario no se repite aquí**: vive solo en `drawing-status.md` (esta sección lo referencia y, a lo sumo, informa conteos por estado).
6. Cada bloqueo y pendiente tiene responsable y fecha.

## 4. Estructura recomendada

> **Nota:** `FOR_REVIEW` (PARA REVISAR) se agrega a la lista de estados originales como señal explícita de que el usuario debe revisar la documentación generada. Desde la versión 1.2 el ciclo `ENGINEERING ⇄ FOR_REVIEW ⇄ INTERNAL_REVIEW` ocurre **por paquete de revisión**: `FOR_REVIEW` significa que **un** paquete espera al usuario (nunca más de uno, salvo autorización registrada en una `DEC`), no que todo el proyecto está en revisión.

### 4.1 Estados permitidos y condiciones

| Estado | Significado | Condición de entrada | Condición de salida |
|---|---|---|---|
| `planning` | Definición de alcance, información y plan | Proyecto iniciado | `goals.md`, `project-information.md` y plantilla de carpetas definidos |
| `ENGINEERING` | Desarrollo de ingeniería, **un paquete por vez**; también el estado entre un paquete `REVIEWED` y el siguiente | Datos de entrada mínimos disponibles; paquete a desarrollar con sus dependencias `REVIEWED` | Paquete generado y su autocontrol realizado (incluido el verificador), o todos los paquetes de la entrega objetivo `REVIEWED` y auditoría pedida |
| `FOR_REVIEW` | **PARA REVISAR:** Claude terminó de generar **un paquete**; **el usuario debe revisarlo** (solo hay un paquete en este estado) | Paquete generado, autocontrol del paquete realizado y hoja de revisión del paquete entregada (sección L) | El usuario inicia su revisión (devuelve la hoja con su primera respuesta o dice `empezar revisión`) o rechaza el paquete |
| `INTERNAL_REVIEW` | Revisión del usuario en curso sobre **el paquete** (comentarios `REV-nnn`) | El usuario inició la revisión (primera respuesta en la hoja o `empezar revisión`) | `revisión aprobada`: el paquete queda `REVIEWED` y el proyecto vuelve a `ENGINEERING`; o Claude procesa los comentarios y entrega una nueva hoja **del mismo paquete** (vuelve a `FOR_REVIEW`); o `rehacer` (vuelve a `ENGINEERING`) |
| `FOR_AUDIT` | Auditoría solicitada, **dispara auditoría automática** (una vez por emisión —ifa o ifc— de cada fase, sobre el conjunto de paquetes `REVIEWED` nuevos o modificados) | **Todos** los paquetes de la emisión objetivo `REVIEWED` (ninguno `REABIERTO`), comentarios `REV-nnn` del cliente al ifa anterior cerrados y confirmación del usuario (`auditar`) | Informe de auditoría emitido |
| `AUDITED` | Auditoría **de esa emisión** aprobada: equivale a **aprobado internamente** | Veredicto APPROVED o APPROVED_WITH_comments, sin CRITICAL/MAJOR abiertos, y `aprobar auditoría` del usuario | `entregar ifa` / `ifc` (Claude arma el paquete y el transmittal borrador) y `entrega enviada TR-nnn` (el usuario confirma el envío) |
| `ifa` | Emisión para Aprobación **enviada**; *esperando comentarios o aprobación del cliente*. La fase de ingeniería (IC / IB / ID / IE) es un atributo del proyecto (sección A) | Solo desde `AUDITED`, con `entrega enviada TR-nnn` | `cliente aprueba` (dispara la fase siguiente, o la ifc si la fase era IE) o comentarios del cliente (`REV-nnn`): los documentos afectados vuelven a ifr interna y siguen un nuevo ifa con su auditoría |
| `ifc` | Emisión para Construcción **enviada** (liberación para construir de la Ejecutiva aprobada internamente; no es una aprobación documental) | Solo desde `AUDITED` de la fase IE, con `entrega enviada TR-nnn` | `pasar a CONSTRUCTION` (inicio de obra) |
| `CONSTRUCTION` | Ejecución de obra | Entrega para Construcción (ifc) realizada | Obra terminada y mecánicamente completa |
| `PRECOMMISSIONING` | Verificaciones sin energía y sin carga | Completitud mecánica | Protocolos de pre-commissioning aprobados |
| `COMMISSIONING` | Energización, pruebas funcionales y de puesta en marcha | Pre-commissioning aprobado | Protocolos de commissioning aprobados y entrega operativa |
| `as-built` | Elaboración de documentación final conforme a obra | COMMISSIONING concluido | Documentación as-built entregada y auditada |
| `CLOSED` | Proyecto cerrado | Auditoría de cierre aprobada | — |

### 4.2 Flujo y retrocesos

```text
planning → ENGINEERING → FOR_REVIEW → INTERNAL_REVIEW → FOR_AUDIT → AUDITED → ifa → ifc
        → CONSTRUCTION → PRECOMMISSIONING → COMMISSIONING → as-built → CLOSED

Por cada fase de ingeniería (IC → IB → ID → IE) se repite la misma secuencia (ifr es la revisión interna por paquete, no un estado del proyecto):

ENGINEERING ⇄ FOR_REVIEW ⇄ INTERNAL_REVIEW (ifr, por paquete) ─► FOR_AUDIT ─► AUDITED ─ entregar ifa ─ entrega enviada TR-nnn ─► ifa (espera al cliente)
   ifa ─ comentarios del cliente (REV-nnn: rfc o corrección documental) ─► ENGINEERING (lo afectado vuelve a ifr) ─► … ─► nuevo ifa  (siempre, sin excepciones)
   ifa ─ cliente aprueba ─► ENGINEERING de la fase siguiente (plan de paquetes de esa fase)
   IE: AUDITED ─ entregar ifc ─ entrega enviada TR-nnn ─► ifc ─► CONSTRUCTION ─► … ─► as-built (parte de la Ejecutiva actualizada)
```

- **Solo el usuario saca al proyecto de `FOR_REVIEW`.** Claude nunca avanza más allá de ese estado por sí mismo y no desarrolla otro paquete mientras el actual espera su respuesta.
- **Ciclo por paquete.** `ENGINEERING` (desarrolla el paquete) → `FOR_REVIEW` (hoja del paquete) → `INTERNAL_REVIEW` (el usuario revisa) → con `revisión aprobada`, el paquete queda `REVIEWED` y el proyecto vuelve a `ENGINEERING` para el paquete siguiente (o a `planning` si no queda ninguno por desarrollar y falta definir el plan, por ejemplo por bloqueos). Se repite hasta que todos los paquetes de la entrega objetivo estén `REVIEWED`; entonces Claude propone `FOR_AUDIT` y el usuario lo confirma con `auditar`.
- Retrocesos permitidos: `FOR_REVIEW → ENGINEERING` y `INTERNAL_REVIEW → ENGINEERING` (el usuario rechaza el paquete o pide rehacer; vuelve solo ese paquete); `FOR_AUDIT → ENGINEERING` (veredicto NOT_APPROVED con al menos un hallazgo abierto que exige trabajo de ingeniería; el hallazgo se tramita como rfc; si los hallazgos abiertos no exigen ese trabajo, el proyecto **permanece en `FOR_AUDIT`** mientras se cierran y se re-auditan solo esos ítems, ver `project-audit.md`, sección 7); `ifa/ifc → ENGINEERING` (comentarios del cliente tratados como rfc o corrección documental, o paquetes de la fase siguiente tras `cliente aprueba`); `INTERNAL_REVIEW → FOR_REVIEW` (Claude procesó los comentarios del paquete y entrega el paquete con las revisiones incrementadas —cada comentario suma 1 al último dígito— y una nueva hoja del mismo paquete). Todo documento modificado vuelve a pasar por `FOR_REVIEW`, `INTERNAL_REVIEW`, `REVIEWED` y `FOR_AUDIT`.
- **Entrega y espera del cliente.** `AUDITED` no pasa a `ifa`/`ifc` por el solo hecho de armar la carpeta: el estado cambia cuando el usuario confirma el envío con `entrega enviada TR-nnn`. En `ifa` el proyecto queda *esperando al cliente*; los comentarios vuelven siempre a revisión interna (ifr) antes de reemitir. El silencio no cierra la instancia: solo `cliente aprueba` (con `DEC` y evidencia) la cierra y dispara la fase siguiente.
- **Cambio aguas arriba:** si un paquete `REVIEWED` cambia (siempre por `rfc-nnn`: comentario posterior, pedido del cliente o hallazgo de auditoría), los paquetes dependientes `REVIEWED` que usan el dato modificado quedan `REABIERTO` y vuelven a `FOR_REVIEW` de a uno, con una hoja corta de impacto («qué cambió / por qué afecta», `review-sheet.md`, 7.1); los que solo citan al documento modificado no cambian.
- Saltos **prohibidos**: ninguna emisión (`ifa`, `ifc`) sin pasar por `AUDITED` **de esa emisión**; ninguna fase sin el `cliente aprueba` de la anterior (salvo `DEC` `[VERIFICAR]`); ninguna ifc antes de terminar la Ejecutiva; ningún `CLOSED` sin auditoría de cierre.
- Un cambio posterior a la auditoría sobre documentos auditados invalida su auditoría.
- Los estados de documentos individuales usan el mismo vocabulario cuando corresponde (ver `DOCUMENT_RULES.md`).
- `INTERNAL_REVIEW → FOR_REVIEW`: ocurre cuando Claude entrega las nuevas revisiones y la hoja siguiente **del mismo paquete**. Las hojas 2 y siguientes de un paquete se entregan en `FOR_REVIEW` y el estado vuelve a `INTERNAL_REVIEW` cuando el usuario las responde. En el historial se anota un solo asiento por sesión y paquete (`PQ-nn`), no los estados intermedios.

### 4.3 Estado del proyecto y estado de sus documentos

Cuándo cambia cada estado y quién actualiza la cabecera del documento, la LME y este archivo. Los tres deben ser coherentes (`project-audit.md`, A1-06).

| Estado del proyecto | Estado de los documentos | Quién actualiza cabecera, LME y `project-status.md` |
|---|---|---|
| `ENGINEERING` | `DRAFT` los del paquete en desarrollo (nuevos o en corrección); los de paquetes `REVIEWED` conservan `REVIEWED` y los demás su estado | Claude (gestor) |
| `FOR_REVIEW` | `FOR_REVIEW` los del paquete que espera al usuario (insumos de planos incluidos; el plano en la LME sigue `CAD_INPUT`); los demás paquetes no cambian | Claude (gestor) |
| `INTERNAL_REVIEW` | `INTERNAL_REVIEW` los de la hoja del paquete en revisión | Claude (gestor), al registrar la respuesta del usuario |
| `ENGINEERING` tras `revisión aprobada` de un paquete | `REVIEWED` los del paquete aprobado (columna *Revisó* con el nombre del usuario) | Claude (gestor), al recibir `revisión aprobada` |
| `FOR_AUDIT` | `FOR_AUDIT` los de todos los paquetes de la entrega objetivo (antes `REVIEWED`) | Claude (gestor) al recibir `auditar` |
| `AUDITED` (veredicto APPROVED / APPROVED_WITH_comments y `aprobar auditoría`) | `AUDITED` | Claude (gestor), tras recibir el informe del auditor y la aprobación del usuario |
| `FOR_AUDIT` tras NOT_APPROVED sin trabajo de ingeniería | Se mantienen `FOR_AUDIT`; se re-auditan solo los ítems abiertos | Claude (gestor) |
| `ENGINEERING` tras NOT_APPROVED con trabajo de ingeniería | Los documentos con hallazgos abiertos pasan a `DRAFT` al corregirse, con la `rfc-nnn` del hallazgo aprobada (nueva revisión `00.n`, n = número de la rfc) o la corrección documental confirmada (`00.R.C+1`); los demás se mantienen `FOR_AUDIT` | Claude (gestor) |
| `ifa` / `ifc` | `ifa` / `ifc` con la revisión entregada (rotulada `Rev 00`; el transmittal registra la revisión interna `00.R.C.FF`) | Claude (gestor), al recibir `entrega enviada TR-nnn` y registrar el transmittal como emitido |

El auditor no modifica estados ni cabeceras: los propone en su informe. `FOR_AUDIT` y `ENGINEERING` son estados del proyecto; el documento usa `FOR_AUDIT` y `DRAFT`. `REVIEWED` es solo estado documental (y de paquete): el proyecto está en `ENGINEERING` mientras haya paquetes por desarrollar, aunque algunos ya estén `REVIEWED`.

## 5. Ejemplos (ilustrativos, no vinculantes)

**Cambio a auditoría:**

```text
Estado actual: FOR_AUDIT
Estado previo: ENGINEERING (último paquete de la entrega, EJ-PQ-12, pasó a REVIEWED; el usuario dijo «auditar»)
Entrega objetivo: ifa (fase IB)
Alcance: los paquetes EJ-PQ-01 a EJ-PQ-12 (todos REVIEWED) de Ingeniería Básica listados en deliverables.md
```

**Bloqueo:**

| ID | Bloqueo | Impacto | Responsable | Fecha límite |
|---|---|---|---|---|
| EJ-BLQ-001 | Falta nivel de cortocircuito de la distribuidora (EJ-INF-002) | No se puede cerrar la memoria de cálculo de cortocircuito | Líder Técnico | 2026-11-01 |

## 6. Buenas prácticas

- Fechar siempre cada actualización.
- Describir bloqueos por su **causa** y su **consecuencia**.
- Los próximos pasos deben ser accionables, con responsable y fecha.
- No declarar un porcentaje de avance sin base de cálculo: el único cálculo válido es el definido en `project-audit.md`, sección 3.4, y se copia del último `progress-nn`.
- Si el estado real no coincide con el declarado, corregir el estado: este archivo no es aspiracional.

---

# REGISTRO DEL PROYECTO (completar)

## A. Estado actual

| Campo | Valor |
|---|---|
| **Estado actual** | `planning` |
| Fecha de último cambio de estado | `[DEFINIR]` |
| Estado previo | — |
| Fase contractual | `[DEFINIR]` (Licitación / Ingeniería Básica / Ingeniería de Detalle / Construcción / Pre-COMMISSIONING / COMMISSIONING / As-Built) |
| **Fase de ingeniería** (`IC` / `IB` / `ID` / `IE` / `ASB`) y emisión pendiente de cierre (ifa / ifc de esa fase, con `TR-nnn`) | `[DEFINIR]` |
| Responsable del estado | `[DEFINIR]` |
| Avance global (**fuente única: último informe de avance del auditor, `progress-nn`; cálculo definido en `project-audit.md`, sección 3.4**) | 0 % |
| **Paquete actual** (`PQ-nn`, nombre y estado: en desarrollo / `FOR_REVIEW` / `INTERNAL_REVIEW`) | — |
| **Paquetes** (n `REVIEWED` / n pendientes / n `REABIERTO`; total) | 0 / 0 / 0 (0) |
| **Próximo paquete propuesto** (según el grafo de la LME; el usuario confirma o reordena) | `[DEFINIR]` |
| **Qué se espera del usuario** (una línea: revisar la hoja del paquete / confirmar el siguiente / nada) | — |
| **Documentos en `FOR_REVIEW` (los del paquete que espera al usuario; ninguno si no hay paquete en revisión)** | 0 |
| Archivos nuevos sin analizar en `01-input` | 0 |
| rfc sin cerrar (`change-requests.md`) | 0 |
| **Entrega en curso** (`TR-nnn`, tipo ifa / ifc y situación: preparada sin enviar / enviada, *esperando comentarios del cliente* / comentarios en tratamiento / cerrada) | — |
| Comentarios del cliente de la entrega anterior (abiertos / cerrados; rfc abiertas) | — |
| Planos y diagramas por estado (**solo conteos**; el detalle y el estado de cada plano viven en `drawing-status.md`): `PLANNED` / `CAD_INPUT` / `DRAWN` / `REVIEWED` / `ENTREGADO`, y fecha de la última anotación del usuario | 0 / 0 / 0 / 0 / 0 |
| Zona del buffer de proyecto (solo con gestión del proyecto; último informe de avance) | `[DEFINIR]` (VERDE / AMARILLO / ROJO) |

## B. Solicitud de auditoría (completar solo si el estado es `FOR_AUDIT`)

| Campo | Valor |
|---|---|
| Fecha de solicitud | |
| Tipo de auditoría (ENTREGA / RE-ENTREGA / CIERRE). Cada emisión ifa o ifc de cada fase tiene la suya | |
| Emisión objetivo (ifa / ifc / CIERRE) y fase de ingeniería (`IC` / `IB` / `ID` / `IE`) | |
| Comentarios del cliente a la entrega anterior (`REV-nnn` cerrados: rfc `CLOSED`, `REJECTED` o `DEFERRED` con `DEC`, o corrección documental incorporada; desde el segundo ifa de la fase) | |
| Paquetes de la entrega (`PQ-nn`; todos deben estar `REVIEWED`, ninguno `REABIERTO`) | |
| Alcance de la entrega (IDs `ENT-nnn` incluidos en esta entrega, que son los de esos paquetes; los demás quedan fuera con motivo) | |
| Alcance (códigos de documentos o "completo" = todos los de la LME marcados «Emisión objetivo») | |
| Solicitante | |

**Pendientes aceptados.** Una marca `[DEFINIR]` o `[VERIFICAR]` abierta solo puede ir a `FOR_AUDIT` si figura aquí. La aceptación es del usuario (en la hoja de revisión con `ACEPTO PENDIENTE`, o por escrito). Un pendiente aceptado no equivale a conformidad: el auditor lo lista como no verificado, con severidad `OBSERVATION` para una emisión ifa y `MAJOR` para ifc o posterior si se trata de un valor normativo (`project-audit.md`, sección 6).

| ID | Marca o ID pendiente (`[VERIFICAR]` / `[DEFINIR]` / `INF-nnn`) | Documento (código) | Qué queda sin verificar y por qué | Vale hasta (ifa / ifc) | Fecha de aceptación | Firmante (usuario) |
|---|---|---|---|---|---|---|
| PA-001 | | | | | | |

## C. Historial de estados

| Fecha | De | A | Motivo / evidencia (informe de auditoría, aprobación, etc.) | Responsable |
|---|---|---|---|---|
| | | `planning` | Inicio del proyecto | |

## F. Pendiente

| ID | Elemento | Prioridad (Alta / Media / Baja) | Responsable | Fecha prevista |
|---|---|---|---|---|
| PND-001 | | | | |

## G. Bloqueado

| ID | Bloqueo | Causa | Impacto | Responsable de resolverlo | Fecha límite |
|---|---|---|---|---|---|
| BLQ-001 | | | | | |

## H. Próximos pasos

| N.º | Acción | Responsable | Fecha | Dependencia |
|---|---|---|---|---|
| 1 | | | | |

## K. Información pendiente del cliente / terceros

| ID | Información requerida | Destinatario (Cliente / Ingeniería) | Parámetro o documento que bloquea | Fecha de solicitud | Estado |
|---|---|---|---|---|---|
| INF-001 | | | | | |

## L. Paquete en revisión (se completa al pasar a `FOR_REVIEW`; se reemplaza en cada paquete)

> La hoja que el usuario completa es `03-review/review-sheets/REVIEW-nn_YYYYMMDD_PQ-nn.md` (plantilla en `review-sheet.md`) y es la **fuente única** del contenido de la revisión de ese paquete. Esta sección registra solo su ruta, su fecha y los conteos; **no se repiten aquí listas de documentos, supuestos ni checklists**. Hay **un solo paquete** en esta sección (el que espera al usuario); los paquetes ya cerrados quedan en la tabla de historial de abajo.

| Campo | Contenido |
|---|---|
| Paquete en revisión (`PQ-nn` y nombre corto) | `[DEFINIR]` |
| Tipo de hoja (primera / reentrega / impacto) | |
| Hoja vigente (ruta) | `[DEFINIR]` |
| Fecha de entrega al usuario | |
| Documentos a revisar (cantidad, de 1 a 3) | |
| Filas de la parte B por tipo (`SUP` / `DEC` / `INF` / `rfc` / marcas) | |
| Entregables del paquete `BLOCKED` | |

**Historial de paquetes** (una fila por paquete; ruta de la última hoja y fecha del OK del usuario):

| Paquete | Estado | Última hoja (ruta) | Fecha de `revisión aprobada` | Observaciones (`REABIERTO` por `PQ-nn`, etc.) |
|---|---|---|---|---|
| PQ-01 | | | | |

## M. Registro de comentarios de revisión

| ID | Fecha | Origen (INTERNO / CLIENTE / AUDITORÍA) | Documento (código, rev.) | Sección | Comentario | Severidad (Crítico / Mayor / Menor / Sugerencia) | Tratamiento (rfc-nnn / corrección documental) | Revisión resultante (`00.R.C.FF`) | Estado (OPEN / RESOLVED / REJECTED / VERIFIED) |
|---|---|---|---|---|---|---|---|---|---|
| REV-001 | | | | | | | | | |

> Todo comentario (del cliente, del jefe, del usuario o del auditor) recibe un `REV-nnn` y suma 1 al último dígito de la revisión del documento: así queda la trazabilidad de comentarios y rfc. La clasificación rfc / corrección documental la propone Claude y la confirma el usuario (`confirmar clasificación`).

## N. Entregas al cliente y revisión del cliente

> Una fila por entrega (`TR-nnn`). La entrega se registra como enviada cuando el usuario dice `entrega enviada TR-nnn`; la instancia de revisión del cliente se cierra cuando todos sus comentarios están cerrados (o con `cliente aprueba`, con su `DEC`).

| Entrega (`TR-nnn`) | Tipo (ifa / ifc / AS-BUILT) y fase (`IC` / `IB` / `ID` / `IE`) | Auditoría (`AUD-nn`) | Fecha de envío | Rótulo al cliente / revisiones internas enviadas | Plazo de respuesta del cliente | Comentarios recibidos (fecha) | rfc abiertas por esta entrega | Instancia de revisión (abierta / cerrada) y `DEC` de cierre |
|---|---|---|---|---|---|---|---|---|
| | | | | `Rev 00` / `00.R.C.FF` por documento | | | | |

