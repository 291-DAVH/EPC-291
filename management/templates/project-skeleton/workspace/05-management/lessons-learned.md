# lessons-learned.md — Lecciones Aprendidas (buzón de entrada)

| Campo | Valor |
|---|---|
| Versión | 1.0 |
| Fecha | 2026-10-07 |
| Responsable | Líder Técnico |

---

# GUÍA DEL ARCHIVO (no editar)

## 1. Objetivo

Capturar durante el proyecto lo que conviene **no repetir o repetir siempre**, y trasladarlo a la biblioteca de la oficina (`DESIGN_RULES.md`, `engineering-standards.md`, `98_LIBRARY/`). Este archivo es un **buzón de entrada**: lo que contiene está pendiente de extraer, y **una vez extraído el archivo queda en blanco**.

## 2. Alcance

Lecciones técnicas (reglas de diseño, criterios, cálculos, equipos), de proceso (revisiones, plazos, comunicación con el cliente) y de seguridad. No es un registro histórico: la historia se conserva en `02-engineering/ARCHIVE` (ver sección 3, paso 6).

## 3. Forma de utilización

1. **Captura:** Claude y el usuario agregan `LEC-nnn` en la sección A cuando ocurre algo que enseña (un hallazgo de auditoría repetible, un comentario del cliente, un error de cálculo, una regla que hubo que preguntar dos veces, un equipo que funcionó o no). Cada lección cita su origen (`HAL-`, `REV-`, `rfc-`, `DEC-`, `INC-`, `BLQ-`, `RSK-` o `INF-`). El campo *Destino propuesto* no se completa en la captura: lo completa Claude durante la extracción, al clasificar.
2. **Extracción:** con el comando **«extraer lecciones»**, y de forma obligatoria **antes del cierre del proyecto**, Claude clasifica cada lección por destino:

| Destino | Qué se actualiza |
|---|---|
| Regla general de diseño o montaje | `DESIGN_RULES.md` |
| Criterio de ingeniería | `engineering-standards.md` |
| Cálculo | `98_LIBRARY/calculations/` y `calc-library.md` |
| Equipo o material | `98_LIBRARY/equipment/equipment-catalog.md` |
| Norma a incorporar | `98_LIBRARY/standards/standards-index.md` |
| Proceso | `CLAUDE.md`, `DOCUMENT_RULES.md`, `project-audit.md` u otro archivo del framework |
| Particular del cliente | `client-requirements.md` o la ficha de cliente recurrente (Plantilla E) |
| No generalizable | Se descarta con motivo |

3. **Propuesta:** Claude escribe la tabla *lección → destino → cambio propuesto → aprobación* en `90-management/Historical/Lessons/lessons_PROPOSAL_YYYYMMDD.md` (columnas: `LEC-nnn`, destino, cambio propuesto, aprobación `APROBADO` / `CORREGIDO: …` / `DESCARTADO`, firma y fecha) y la presenta al usuario. **El usuario aprueba o corrige cada fila en ese archivo**, de modo que la aprobación queda registrada. Al generarse la propuesta, las lecciones pasan de `NEW` a `PROPOSED`. Claude no modifica la biblioteca sin esa aprobación.
4. **Aplicación:** Claude aplica los cambios aprobados en los archivos destino de **la plantilla maestra** (ruta indicada en `project-information.md`, sección A). Antes de aplicar compara la **versión de la plantilla** registrada al iniciar el proyecto (versión, fecha y huella, `CLAUDE.md`, 8.1 (copia de la plantilla, `M3`)) con la actual de la maestra; si difieren, lo informa al usuario y aplica cada cambio sobre la versión actual de la maestra, no sobre una copia antigua. Si la maestra no está accesible, Claude genera el **paquete de actualización** (`TEMPLATE_UPDATE_YYYYMMDD.md`, con cada cambio listo para pegar) y lo entrega al usuario.
5. **Registro del cambio de la biblioteca:** cada archivo destino anota el cambio en su historial (fecha, motivo, lección de origen).
6. **Vaciado:** una vez aplicadas (o descartadas con motivo) **todas** las lecciones, Claude copia el contenido extraído a `02-engineering/ARCHIVE/lessons_EXTRACTED_YYYYMMDD.md` y **deja la sección A de este archivo en blanco** (solo la fila vacía de la plantilla). Un archivo con lecciones ya extraídas, no vaciado, es un hallazgo de auditoría.

## 4. Estructura recomendada

Cada lección: ID, fecha, disciplina, tipo, descripción (qué pasó), causa, lección (qué hacer distinto), origen, destino propuesto (se completa en la extracción), estado. Estados: `NEW` (capturada), `PROPOSED` (incluida en la propuesta `lessons_PROPOSAL_YYYYMMDD.md`, pendiente de aprobación), `APPROVED` (aprobada por el usuario), `APPLIED` (aplicada en la maestra) y `DISCARDED` (descartada con motivo).

## 5. Ejemplos (ilustrativos)

- Origen `EJ-HAL-01-003`: se dibujaron luminarias de emergencia sin salida de evacuación conocida. Lección: pedir el plano de arquitectura antes de calcular la emergencia. Destino: `deliverables.md` (matriz de preparación) o `DESIGN_RULES.md`.
- Origen `EJ-REV-002`: el usuario pide no fijar la tensión de alimentación de luminarias. Destino: `DESIGN_RULES.md`.

## 6. Buenas prácticas

- Redactar la lección como acción concreta, no como queja.
- Una lección, un destino principal.
- Extraer en el cierre de cada grupo importante de paquetes (por ejemplo, al cerrar los de cálculo), no solo al final del proyecto.
- No guardar aquí datos del cliente que no sean generalizables.

---

# BUZÓN (completar; se vacía tras la extracción)

## A. Lecciones pendientes de extraer

| ID | Fecha | Disciplina | Tipo | Qué pasó | Causa | Lección | Origen | Destino propuesto | Estado |
|---|---|---|---|---|---|---|---|---|---|
| LEC-001 | | | | | | | | `[se completa en la extracción]` | NEW |
