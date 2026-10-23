# review-sheet.md — Hoja de Revisión del Usuario

| Campo | Valor |
|---|---|
| Versión | 1.4 |
| Fecha | 2026-10-07 |
| Responsable | Project Engineer |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Que el usuario sepa **qué revisar, dónde mirarlo, dónde responder y cómo termina la revisión**, sin buscar en varios archivos y **sin recibir más de lo que puede verificar de una vez**. La revisión es **secuencial, por paquete**: un paquete de revisión (`PQ-nn`) es un documento o un grupo pequeño (normalmente de 1 a 3) de documentos que van de la mano (`deliverables.md`, 4.1). Claude desarrolla un paquete, lo entrega con **una hoja de revisión que contiene solo ese paquete** (`REVIEW-nn_YYYYMMDD_PQ-nn.md`, a partir de la plantilla de la sección «PLANTILLA» de este archivo) y se detiene. El usuario lo verifica y responde (OK o comentarios); recién entonces se sigue con el paquete siguiente. La hoja es el **único lugar** donde el usuario responde y la **fuente única** del contenido de esa revisión (`project-status.md`, sección L, solo registra su ruta, fecha y conteos). Claude la transcribe después a `REV-nnn` (`project-status.md`, sección M), `DEC-nnn` e `INF-nnn`.

## 2. Alcance

Toda revisión del usuario sobre documentos generados por Claude (revisión interna, ifr), un paquete por vez. Cada comentario del usuario es un `REV-nnn` (origen INTERNO) y, al incorporarlo, **suma 1 al último dígito de la revisión** (`00.0` → `00.0.1`); si cambia línea base, alcance, requisito o dato maestro se tramita además como rfc (`change-requests.md`). No reemplaza la auditoría (`project-audit.md`), que es posterior, independiente y se ejecuta **una sola vez por emisión (ifa o ifc)**, sobre el conjunto de paquetes `REVIEWED`: la **revisión es del usuario** (¿esto es lo que quiero y es técnicamente correcto?); la **auditoría es de Claude en rol de auditor** (¿está demostrado y es coherente?).

## 3. Forma de utilización (lo que hace el usuario, en 4 pasos)

1. **Abrir** la hoja `03-review/review-sheets/REVIEW-nn_YYYYMMDD_PQ-nn.md` (Claude informa su ruta al terminar el paquete). Contiene **solo ese paquete**; no hay nada más que revisar hasta que usted responda.
2. **Revisar los documentos del paquete** (de 1 a 3), en el orden de la hoja (prioridad Alta primero). Cada fila indica el archivo, qué mirar y los puntos de mayor riesgo. Se anota en la columna *Comentario* y se elige *Veredicto*: `OK`, `CON COMENTARIOS` o `RECHAZAR`.
3. **Responder la parte B** (aceptar, cambiar, rechazar o diferir cada supuesto, decisión, solicitud de cambio o dato pendiente **de este paquete**), con las respuestas de la sección 5.
4. **Cerrar** con una frase al chat (tabla de la sección 7): `revisión aprobada` (todo `OK`: el paquete queda `REVIEWED`), `procesar comentarios de revisión` (hay comentarios; Claude los resuelve y entrega una nueva hoja del **mismo** paquete, solo con lo cambiado) o `rehacer` (el paquete vuelve a `ENGINEERING`).

**Cuándo empieza la revisión.** El proyecto pasa de `FOR_REVIEW` a `INTERNAL_REVIEW` cuando el usuario devuelve la hoja con su primera respuesta o frase de cierre, o cuando dice **`empezar revisión`**. No hace falta avisar de otro modo.

**Qué pasa después.** Con `revisión aprobada` Claude cierra el paquete y **propone el siguiente** según el grafo de dependencias de la LME (usted confirma o lo reordena con una frase). No se desarrolla ningún paquete que dependa de uno que todavía no esté `REVIEWED`: por ejemplo, no se redacta un capítulo de pliego antes de que el dimensionamiento de cables esté revisado. Claude no entrega dos paquetes a la vez, salvo que usted lo autorice de forma explícita (`desarrollar paquetes [PQ-nn] y [PQ-nn]`).

**Otras formas de revisar (equivalentes):**
- **Revisión guiada:** el usuario dice `guiar revisión` y Claude recorre la hoja **un documento por vez en el chat** (resumen, qué mirar, pregunta «¿OK, comentarios o rechazar?»); Claude completa la hoja con lo dictado.
- **Comentarios sueltos:** el usuario puede escribir o dictar comentarios en el chat o marcarlos en una copia del archivo; Claude los transcribe a la hoja citando la fuente.

## 4. Qué significa cada veredicto

| Veredicto | Significado | Efecto |
|---|---|---|
| `OK` | Lo revisé y no tengo comentarios | El documento queda sin comentarios abiertos. El paquete se cierra (`REVIEWED`) cuando **todos** sus documentos están `OK` y se dice `revisión aprobada` |
| `CON COMENTARIOS` | Lo revisé; hay cosas para corregir | Cada comentario pasa a `REV-nnn`; Claude lo incorpora, suma 1 a la revisión (`00.0` → `00.0.1`), archiva la revisión superada y devuelve el documento con una **nueva hoja del mismo paquete** que contiene solo lo cambiado |
| `RECHAZAR` | No sirve como base; hay que rehacerlo | **Ese paquete** (y solo ese) vuelve a `ENGINEERING`; se rehace lo rechazado y lo que depende de ello dentro del paquete, y se entrega una hoja nueva del mismo paquete |
| *(vacío)* | No revisado | El paquete **no se puede aprobar** con documentos sin veredicto |

**Resultado de la hoja.** La hoja lleva en su cierre una línea `Resultado:` con uno de cuatro valores, que Claude escribe **solo cuando usted dicta su decisión**: `APPROVED` (todo `OK`, `revisión aprobada`) · `APPROVED_WITH_comments` (`procesar comentarios de revisión`) · `REJECTED` o `REJECTED_WITH_comments` (`rehacer`). **Solo `APPROVED` permite que el paquete avance a auditoría**; los otros tres lo devuelven a `02-engineering` y, después de incorporar los cambios, se entrega una hoja nueva y el paquete se revisa de nuevo desde el principio. La hoja que vale es la de la ronda vigente.

**Pliegos técnicos.** Un pliego es un solo documento, pero su fila de la parte A se desdobla en **una fila por capítulo**, con la pregunta que responde el capítulo como «qué mirar» (`TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.9); el veredicto y los comentarios son por capítulo y la revisión que se sube es la del conjunto.

Un documento sin revisar **no se da por aprobado**. «Revisado» lo marca el usuario, nunca Claude. Un documento de **insumos de dibujo** de un plano se revisa como cualquier otro documento (el plano queda `CAD_INPUT` hasta que el usuario lo dibuje).

## 5. Respuestas de la parte B y qué hace Claude con cada una

Las respuestas de esta sección son **códigos de respuesta de la hoja** (se escriben en mayúsculas dentro de sus tablas); las frases que se dicen en el chat (`revisión aprobada`, `procesar comentarios de revisión`, `rehacer`…) son frases fijas definidas en `COMMANDS.md`.

Claude marca en cada fila de la parte B el **riesgo** (`Bajo` / `Medio` / `Alto`) para que el usuario dedique su atención a lo que importa. **Bajo:** afecta a un solo documento, es reversible, tiene base del valor documentada y no toca la seguridad ni un parámetro crítico. **Medio:** afecta a más de un documento o a un dato de diseño relevante. **Alto:** afecta a la seguridad de las personas, a un parámetro crítico, a la línea base o al plazo.

| Respuesta | Se usa en | Efecto |
|---|---|---|
| `ACEPTO` | `SUP`, `DEC` propuesta, dato propuesto | `SUP`: se acepta usarlo y queda `OPEN` con la aceptación fechada hasta tener el dato real. `DEC`: pasa de `PROPOSED` a `APPROVED`. Dato propuesto: queda `CONFIRMED`. |
| `CAMBIO: …` | `SUP`, `DEC` | Claude crea una **`DEC` nueva** con el valor indicado que **reemplaza** al `SUP` (queda `CLOSED`) o a la `DEC` anterior (`SUPERSEDED`); se propaga a los documentos. |
| `RECHAZO` | `SUP`, `DEC` | `SUP` pasa a `INVALIDATED` y se registra la decisión correctiva; `DEC` pasa a `REJECTED`. |
| `ACEPTO` / `RECHAZO` / `DIFERIR` | `rfc` | La solicitud de cambio pasa a `APPROVED` / `REJECTED` / `DEFERRED` (`change-requests.md`) y se registra como `DEC`. |
| un dato | `INF`, `[DEFINIR]` | La `INF` se cierra y el valor se vuelca en `project-information.md`. |
| `NO SÉ / PENDIENTE` | `INF`, `[DEFINIR]`, `SUP`, `DEC` | Queda una `INF-nnn` abierta con responsable y fecha (propuesta por Claude, ajustable), y Claude propone el siguiente paso: **A** esperar la `INF`, **B** autorizar un `SUP` con base del valor y `[VERIFICAR]`, o **C** dejar el documento `BLOCKED` (misma lógica que la puerta de preparación, `CLAUDE.md`, 8.3). |
| `ACEPTO PENDIENTE` | `[DEFINIR]`, `[VERIFICAR]` | La marca se registra como **pendiente aceptado** (`PA-nnn`, fecha y firmante) en la tabla del bloque B de `project-status.md`. No equivale a conformidad: la auditoría lo lista como no verificado. |
| `ACEPTO TODOS LOS BAJOS` | Parte C | Acepta en bloque todas las filas `SUP` y `DEC` de riesgo `Bajo` **de la hoja de este paquete** que no tengan respuesta propia. **Nunca** alcanza a filas de riesgo `Medio` o `Alto`, a parámetros críticos, a valores normativos `[VERIFICAR]` ni a filas de otros paquetes. |

Cada `rfc` nueva se presenta en la parte B para que el usuario la resuelva (también puede hacerlo con `aprobar rfc [rfc-nnn]`, `rechazar rfc [rfc-nnn]` o `diferir rfc [rfc-nnn]`). Mientras no responda, el documento afectado no se modifica por esa rfc.

## 6. Qué hace Claude al recibir la hoja

1. Verifica que todos los documentos del paquete tengan veredicto; si falta alguno, lo señala y no avanza.
2. Transcribe cada comentario a `REV-nnn` (sección M) con documento, sección, severidad propuesta y la fila de la hoja como evidencia; cada decisión a `DEC-nnn`; cada dato entregado a `INF-nnn` cerrado; cada `NO SÉ` a `INF-nnn` abierta.
3. Si un comentario cambia alcance, requisito, dato maestro u otro punto de la lista de rfc (`CLAUDE.md`, 4.3), Claude propone abrir una `rfc-nnn` (`change-requests.md`) y el usuario confirma la clasificación (`confirmar clasificación`). Hasta que la `rfc` esté `APPROVED`, ese comentario queda `OPEN` y el documento no cambia por él. La decisión del usuario sobre la `rfc` va en la parte B de la hoja siguiente.
4. Incorpora los comentarios en los documentos afectados y en los que **usan un dato modificado**: cada `REV-nnn` incorporado suma 1 al último dígito (`00.0` → `00.0.1`); la revisión superada se archiva en `02-engineering/ARCHIVE/<código>/` con su nombre de revisión (estado `SUPERSEDED`) y se registra en el control de revisiones con los `REV-nnn` en *Origen*; los que solo citan al documento modificado **no** cambian por actualizar la referencia (`DOCUMENT_RULES.md`, sección 9). Conserva la hoja anterior en `02-engineering/ARCHIVE/review-sheets` y entrega una **hoja nueva del mismo paquete** solo con lo que cambió técnicamente, indicando por cada `REV-nnn` cómo se resolvió, para que el usuario verifique la resolución (`VERIFIED`). Antes de entregarla repite el autocontrol del paquete (`CLAUDE.md`, 8.3, punto 7).
5. Con `revisión aprobada`: registra la aprobación del paquete (fecha y hoja), pasa sus documentos a `REVIEWED`, completa la columna *Revisó* con el nombre del usuario, anota el paso por `INTERNAL_REVIEW` en el historial si no se había iniciado antes, deja el proyecto en `ENGINEERING` y **propone el paquete siguiente** (o, si era el último de la entrega objetivo, propone la auditoría; la confirma el usuario con `auditar`). No pasa a `FOR_AUDIT` por sí misma.
6. Con `rehacer`: devuelve **solo ese paquete** a `ENGINEERING`, rehace lo rechazado y entrega una hoja nueva del mismo paquete.
7. Si el cambio resuelto en este paquete modifica un dato que usan paquetes dependientes ya `REVIEWED`, aplica la sección 7.1.

## 7. Qué hace cada frase y en qué estado queda el proyecto

| Frase del usuario | Qué significa | Efecto en el paquete | Estado del proyecto |
|---|---|---|---|
| (devuelve la hoja con su primera respuesta) · `empezar revisión` · `guiar revisión` | Empieza a revisar el paquete | Sus documentos pasan a `INTERNAL_REVIEW` | `INTERNAL_REVIEW` |
| `revisión aprobada` | **OK del paquete** (no del proyecto): todos los documentos `OK` | Sus documentos pasan a `REVIEWED` | `ENGINEERING` (para el paquete siguiente), o `planning` si no queda nada por desarrollar |
| `procesar comentarios de revisión` | Hay comentarios en el paquete | Claude los procesa y entrega una **nueva hoja del mismo paquete**, solo con lo cambiado; documentos en `FOR_REVIEW` | `FOR_REVIEW` |
| `rehacer` | Rechaza el paquete (o lo rechazado en él) | Solo ese paquete vuelve a `DRAFT` | `ENGINEERING` |
| `siguiente paquete` | Pide el paquete que sigue (el proyecto debe estar en `ENGINEERING` y el paquete anterior `REVIEWED`); también sirve `siguiente paquete [PQ-nn]` para reordenar sin violar dependencias, o `desarrollar paquetes [PQ-nn] y [PQ-nn]` para autorizar dos paquetes independientes | Claude desarrolla el paquete pedido y lo entrega con su hoja | `ENGINEERING` mientras trabaja; `FOR_REVIEW` al entregar |
| `auditar` (equivale a `auditar proyecto`) | Pide la auditoría de la entrega: se ejecuta una vez, sobre todos los paquetes `REVIEWED` de la entrega objetivo | Sus documentos pasan a `FOR_AUDIT` (con todos los paquetes de la entrega `REVIEWED` y ninguno `REABIERTO`) | `FOR_AUDIT` |

**Última hoja de la entrega.** Cuando el paquete es el último de la entrega objetivo, la parte C de su hoja incluye la pregunta «¿Auditar la entrega?» (`SÍ` / `NO, sigo con otro paquete`). Si el usuario responde `SÍ` junto con `revisión aprobada`, ese asiento cuenta como confirmación del paso a `FOR_AUDIT`; si no, Claude lo propone y espera `auditar`.

### 7.1 Cambio aguas arriba: hoja corta de impacto

Si un paquete que ya estaba `REVIEWED` cambia (siempre por una `rfc-nnn`: comentario posterior del usuario, pedido del cliente o hallazgo de auditoría), Claude revisa el grafo:

1. Los paquetes dependientes que solo **citan** al documento modificado no cambian de estado ni de revisión (citan la «revisión vigente»).
2. Los paquetes dependientes `REVIEWED` que **usan un dato que cambió** quedan marcados `REABIERTO` y vuelven a `FOR_REVIEW` **de a uno, en el orden del grafo**, cada uno con una **hoja corta de impacto** (`REVIEW-nn_YYYYMMDD_PQ-nn.md`, bloque «Impacto aguas arriba» de la plantilla), que indica *qué cambió* (dato, valor anterior y nuevo, paquete y revisión de origen) y *por qué afecta* a este paquete (secciones afectadas). Cada paquete reabierto pasa a la revisión que corresponda al mismo origen (`00.n` si es rfc, o +1 si es comentario) (`DOCUMENT_RULES.md`, sección 9). Como en los documentos de trabajo se cita la «revisión vigente», el efecto suele ser mínimo: la hoja es corta y el usuario revisa solo lo señalado.
3. El paquete que originó el cambio se revisa primero. Los dependientes se entregan cuando el origen vuelve a `REVIEWED`. Mientras haya un paquete `REABIERTO`, la entrega a auditoría no se propone.
4. Un paquete ya incluido en una entrega auditada que cambia **invalida** su auditoría (`CLAUDE.md`, 11.1).

## 8. Glosario de los prefijos de ID que aparecen en la hoja

| Prefijo | Significa |
|---|---|
| `SUP-nnn` | Supuesto: valor adoptado provisoriamente por falta de información |
| `DEC-nnn` | Decisión registrada (propuesta o aprobada) |
| `INF-nnn` | Información pendiente de un tercero o del usuario (rfi) |
| `REV-nnn` | Comentario del usuario sobre un documento |
| `rfc-nnn` | Solicitud de Cambio, *Request for Change* (alcance, requisito o dato maestro; genera la `Rev 00.n`) |
| `ENT-nnn` | Entregable de la lista maestra (cada documento a revisar) |
| `PQ-nn` | Paquete de revisión: documento o grupo pequeño de documentos que se revisan juntos (`deliverables.md`, 4.1) |
| `REQ-…` / `CR-…` | Requisito de la matriz de trazabilidad / requisito del cliente |
| `PAR-nnn` | Parámetro maestro (tensión, potencia, etc.) de `project-information.md` |
| `HAL-nn-nnn` | Hallazgo de una auditoría (`AUD-nn`) |
| `BLQ-nnn` / `PND-nnn` / `PA-nnn` | Bloqueo / pendiente / pendiente aceptado |

Términos de entrega que aparecen en la hoja (versión resumida; glosario completo en `CLAUDE.md`, 4.2):

| Término | Significa |
|---|---|
| Entrega | Envío de un conjunto de documentos y planos al cliente, con su transmittal (se compone de paquetes de revisión ya `REVIEWED` y auditados) |
| ifr / ifa / ifc | ifr: emisión interna para revisión del usuario (se repite); ifa: emitido al cliente para aprobación (siempre tras aprobación interna); ifc: liberado para construcción |
| `00.0` / `00.0.c` / `00.n` / `00` / `01` | Línea base de la fase / más un comentario incorporado por cada `c` / fijada por la `rfc-n` / lo que **siempre** ve el cliente / as-built (`DOCUMENT_RULES.md`, sección 9) |
| rfc | Solicitud de Cambio (*Request for Change*): cambio de línea base, alcance, requisitos, parámetros maestros, filosofía de operación, criterios de diseño, potencias o equipos aprobados; la `rfc-n` fija la revisión `00.n` |
| Editable | Archivo de trabajo en `02-engineering`; es el que se revisa. Lo de `06-deliverables` es copia limpia de solo lectura y no se revisa ni se edita |
| `REVIEWED` | Estado «revisado»: el usuario dio el OK a su paquete (`revisión aprobada`); pendiente de auditoría y de entrega |
| `REABIERTO` | Paquete `REVIEWED` que debe volver a revisión porque cambió un dato del que depende (7.1) |

## 9. Estructura recomendada de los comentarios

Un comentario bueno dice **dónde** (sección o tabla, por su nombre: Word renumera los títulos), **qué** está mal o falta y, si se sabe, **cómo** debería ser. Ejemplo: «ET-001, sección Luminarias de depósito: la luminaria debe ser IP65, no IP54». Un comentario sin sección se acepta, pero Claude puede pedir precisión.

## 10. Ejemplos (ilustrativos)

- La hoja `REVIEW-04_20261110_EJ-PQ-03.md` contiene solo dos documentos: la memoria de cálculo del dimensionamiento de cables de baja tensión (`EJ-MC-003`, prioridad Alta, mirar «caída de tensión del circuito más largo» y «factor de agrupamiento») y su síntesis (`EJ-SM-003`, mirar que cada valor coincida con la memoria). El usuario revisa, anota «ΔU máx. debería ser ≤ 3 %» en la memoria y marca `CON COMENTARIOS`; la síntesis la deja en `OK`. Dice `procesar comentarios de revisión`: Claude entrega `REVIEW-05_20261113_EJ-PQ-03.md` solo con lo cambiado, el usuario responde `OK` en ambas filas y dice `revisión aprobada`: el paquete queda `REVIEWED` y Claude propone `EJ-PQ-04`.
- En la parte B, ante `EJ-SUP-003` (luminaria de referencia de 120 lm/W), responde `CAMBIO: usar 110 lm/W`; Claude crea una decisión nueva que reemplaza al supuesto y recalcula.
- Ante cinco supuestos de riesgo `Bajo` de la hoja de ese paquete, con base documentada, el usuario escribe `ACEPTO TODOS LOS BAJOS` en la parte C y responde solo las filas `Medio` y `Alto`.

## 11. Buenas prácticas

- Revisar primero los documentos de prioridad Alta y las filas de riesgo `Alto` de la parte B: ahí está el mayor riesgo.
- Un paquete por vez: si la hoja le parece demasiado grande, dígalo; Claude vuelve a dividir el paquete en el plan (`deliverables.md`, 4.1).
- Una fila de comentario por tema, no un párrafo con tres temas.
- No hace falta revisar «todo el texto»: la hoja señala qué mirar; si el usuario quiere más profundidad en algo, lo anota.
- Si algo no se entiende, escribir `NO ENTIENDO` en el comentario: Claude lo explica o lo reescribe; no cuenta como error del usuario.
- Revisar con la hoja abierta, no de memoria.
- Lista de control general de la revisión:
  - [ ] Los datos de entrada coinciden con la línea base y los documentos del cliente.
  - [ ] Los criterios y normas aplicados son los correctos para el proyecto.
  - [ ] Los resultados de cálculo son razonables y verificables.
  - [ ] Los alcances y exclusiones coinciden con lo acordado.
  - [ ] Los supuestos y decisiones propuestas son aceptables.
  - [ ] Los documentos no se contradicen entre sí ni repiten contenido.

---

# PLANTILLA (Claude copia esto a `REVIEW-nn_YYYYMMDD_PQ-nn.md` y lo completa; una hoja por paquete)

Claude copia el bloque siguiente a `REVIEW-nn_YYYYMMDD_PQ-nn.md` y lo completa (una hoja por paquete). La hoja es un documento del proyecto y sigue `DOCUMENT_RULES.md`, RG-20 y 7.1: bloque YAML de portada (`code` = `REVIEW-nn`, `revision` vacía), un solo `#`, títulos **sin numeración** (la «Parte A» a «Parte D» va como texto entre paréntesis en el título, para poder nombrarla en el chat) y viñetas con `-`.

```markdown
---
title: "Hoja de revisión del paquete <PQ-nn>"
subtitle: "<Proyecto>"
code: "REVIEW-nn"
revision: ""
status: "FOR_REVIEW"
date: "AAAA-MM-DD"
---

# Hoja de revisión del paquete <PQ-nn> — <nombre del paquete>

## Encabezado

Tabla: Encabezado de la hoja

| Campo | Contenido |
|---|---|
| Proyecto | |
| Hoja N.º / fecha de entrega | |
| Paquete (`PQ-nn`) y nombre | |
| Tipo de hoja | Primera entrega · Reentrega (solo lo cambiado, tras comentarios) · Impacto aguas arriba (hoja corta) |
| Depende de (todos `REVIEWED`) | |
| Estado del proyecto | `FOR_REVIEW` (pasa a `INTERNAL_REVIEW` cuando usted devuelve la hoja) |
| Documentos del paquete (1 a 3) | |
| Fuera de este paquete | Esta hoja contiene solo este paquete. Siguiente paquete propuesto (informativo; no se desarrolla hasta que este quede `REVIEWED`): `PQ-nn` |
| Qué debe hacer usted (resumen en una línea) | Revisar los documentos de la parte A, responder la parte B y decirle a Claude: `revisión aprobada`, `procesar comentarios de revisión` o `rehacer`. |

## Documentos del paquete (Parte A)

Completar las dos últimas columnas.

Tabla: Documentos del paquete

| N.º | Código | Título | Revisión (`00.0`, `00.0.1`…) | Archivo (ruta) | Prioridad | Qué mirar (3 a 5 puntos concretos) | Veredicto (`OK` / `CON COMENTARIOS` / `RECHAZAR`) | Comentario (dónde / qué / cómo) |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | Alta | | | |

## Decisiones y datos de este paquete que necesito de usted (Parte B)

Solo figuran los supuestos, decisiones, solicitudes de cambio, datos y marcas que afectan a **este** paquete. Respuestas posibles: `ACEPTO` · `CAMBIO: …` · `RECHAZO` · `DIFERIR` (solo `rfc`) · un dato · `NO SÉ / PENDIENTE` · `ACEPTO PENDIENTE` (solo marcas). Claude completa la columna *Riesgo*.

Tabla: Decisiones y datos del paquete

| N.º | Tipo (`SUP` / `DEC` / `INF` / `rfc` / `[DEFINIR]` / `[VERIFICAR]`) | ID | Qué se decidió o se necesita | Dónde afecta | Riesgo (`Bajo` / `Medio` / `Alto`) | Respuesta |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

## Cierre (Parte C)

Tabla: Cierre de la revisión

| Pregunta | Respuesta |
|---|---|
| ¿Todos los documentos de la parte A tienen veredicto? | |
| ¿Todas las filas de la parte B tienen respuesta? | |
| ¿Acepto en bloque los supuestos y decisiones de riesgo `Bajo` de esta hoja sin respuesta propia? (`ACEPTO TODOS LOS BAJOS` / no) | |
| Solo si es el último paquete de la entrega: ¿auditar la entrega? (`SÍ` / `NO, sigo con otro paquete`) | |
| Decisión final (`revisión aprobada` / `procesar comentarios de revisión` / `rehacer`) | |
| Fecha y firma del revisor (usuario) | |

Línea de resultado (la escribe Claude, sola en su renglón, cuando recibe la decisión del usuario; solo `APPROVED` avanza; la leen los scripts de `99_core/SCRIPTS/`):

Resultado:

**Estado en que queda el proyecto tras mi frase de cierre:** `revisión aprobada` → el paquete queda `REVIEWED` y el proyecto vuelve a `ENGINEERING` para el paquete siguiente (la auditoría se pide aparte con `auditar`) · `procesar comentarios de revisión` → `FOR_REVIEW` con una nueva hoja del mismo paquete, solo con lo cambiado · `rehacer` → `ENGINEERING` (solo este paquete). Mientras no haya frase de cierre, el proyecto queda en `INTERNAL_REVIEW` desde la primera respuesta.

**Glosario de prefijos de ID:** `PQ` paquete de revisión · `SUP` supuesto · `DEC` decisión · `INF` información pendiente · `REV` comentario de revisión · `rfc` solicitud de cambio · `ENT` entregable · `REQ` / `CR` requisito · `PAR` parámetro maestro · `HAL` hallazgo de auditoría · `BLQ` / `PND` / `PA` bloqueo / pendiente / pendiente aceptado (ver `review-sheet.md`, glosario de los prefijos de ID).

## Impacto aguas arriba

Bloque solo para las hojas de tipo *Impacto*; reemplaza a la parte A completa.

Se usa cuando este paquete ya estaba `REVIEWED` y vuelve a revisión porque cambió un dato del que depende (ver el apartado «Cambio aguas arriba: hoja corta de impacto» de `review-sheet.md`). La hoja es corta: el usuario revisa solo lo señalado.

Tabla: Impacto aguas arriba

| N.º | Paquete y revisión de origen del cambio | Qué cambió (dato, valor anterior → valor nuevo, `REV-nnn` / `rfc-nnn` / `HAL-` que lo originó) | Por qué afecta a este paquete (documento y sección que usan el dato) | Qué se modificó en este paquete (documento y revisión nueva; «sin cambio de contenido» si solo se confirma) | Veredicto (`OK` / `CON COMENTARIOS` / `RECHAZAR`) | Comentario |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

Las partes B y C de la hoja se mantienen (normalmente la parte B queda vacía: «Sin decisiones nuevas»).

## Resolución (Parte D)

La completa Claude en la hoja siguiente del mismo paquete.

Tabla: Resolución de comentarios y decisiones

| `REV-nnn` / `DEC-nnn` / `rfc-nnn` | Origen (fila de la hoja) | Cómo se resolvió | Documento y revisión nueva | Verificado por el usuario (sí / no) |
|---|---|---|---|---|
| | | | | |
```
