# Módulo M1 — Glosario, revisiones, fases y emisiones

> Módulo de `CLAUDE.md` (secciones 4.2 y 4.3). Tiene la **misma autoridad** que `CLAUDE.md`: el texto se movió aquí, sin cambios de fondo, para que `CLAUDE.md` se lea corto en cada sesión. La numeración de las secciones se conserva, de modo que las referencias «`CLAUDE.md`, 8.1» y similares siguen valiendo. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica.

---

### 4.2 Glosario: entrega, entregable y revisiones

Se conservan los códigos **ifr / ifa / ifc** porque son los que usan los clientes y los transmittals, pero siempre con su nombre en español. Son **emisiones documentales** asociadas al nivel de madurez de la ingeniería (sección 4.3), no estados sucesivos del proyecto: **ifr es una emisión interna**; ifa e ifc se envían al cliente. Las siglas **rfc** (Solicitud de Cambio) y **rfi** (consulta de información, `INF-nnn`) no deben confundirse.

| Término | Significado |
|---|---|
| **Entrega** | Acto de enviar al cliente un conjunto de documentos y planos (emisión **ifa** o **ifc**), con su transmittal; se compone de paquetes de revisión `REVIEWED` y auditados. Reemplaza al término «emisión». No confundir con el paquete de revisión, que es interno. |
| **Entregable** | Cada ítem de la Lista Maestra de Entregables (LME, `deliverables.md`), identificado como `ENT-nnn`. No es lo mismo que una entrega: una entrega incluye varios entregables. |
| **Paquete de revisión** | `PQ-nn`: unidad mínima de trabajo y de revisión; un documento o un grupo pequeño (normalmente de 1 a 3) de documentos que van de la mano (p. ej. una memoria de cálculo y su síntesis). Se define en la LME (columnas *Paquete* y *Depende de*). Claude desarrolla y entrega **uno por vez**, y no se empieza uno hasta que los paquetes de los que depende estén `REVIEWED` (`deliverables.md`, 4.1). |
| **ifr** | *Issued For Review*, Emitido para Revisión: emisión **interna**. Todo documento que debe evaluarse internamente (desde que Claude entrega la hoja de revisión hasta `AUDITED`) está en ifr. Puede ocurrir muchas veces en un proyecto (`Rev 00.0`, `00.0.1`, `00.1`…) y todas siguen siendo ifr. No se envía al cliente. |
| **ifa** | *Issued For Approval*, Emitido para Aprobación: se envía al cliente un conjunto ya aprobado internamente (`AUDITED`). El cliente puede aprobar, aprobar con observaciones o rechazar. Se repite hasta que el cliente aprueba (`cliente aprueba`); toda observación del cliente vuelve primero a revisión interna (ifr) y a una auditoría de lo cambiado antes de reenviarse. |
| **ifc** | *Issued For CONSTRUCTION*, Emitido para Construcción: documentación liberada para comprar, fabricar, montar, construir y comisionar. No representa una aprobación documental sino que la documentación tiene el nivel de definición necesario (Ingeniería Ejecutiva). Pasa por su propia revisión interna y auditoría. |
| **Fase de ingeniería** | Nivel de madurez de la ingeniería: `IC` Conceptual, `IB` Base, `ID` Detalle, `IE` Ejecutiva y `ASB` Conforme a obra. Un mismo documento atraviesa varias fases: conserva su código y aumenta su definición (sección 4.3). |
| **Comentario (`REV-nnn`)** | Observación sobre un documento, venga de la revisión interna (usuario o superior), del cliente o de la auditoría. Cada comentario incorporado suma 1 al último dígito de la revisión del documento (`00.0.1`, `00.0.2`…), lo que deja la trazabilidad de comentarios. Se trata como rfc o como corrección documental (4.3). |
| **Transmittal** | Documento que acompaña cada entrega (`TR-nnn`): qué se entrega, con qué rótulo al cliente (`Rev 00`), con qué revisión interna (`00.n`) y a quién. |
| **rfc** | *Request for Change* / Solicitud de Cambio (`rfc-nnn`, `change-requests.md`). Se abre **solo** cuando una observación modifica la línea base, el alcance, los requisitos del cliente, los parámetros maestros, la filosofía de operación, los criterios de diseño, las potencias, el equipamiento aprobado o una decisión registrada (4.3). La `rfc-n` fija el dígito intermedio de la revisión interna de cada documento afectado (`Rev 00.n`). |
| **Rev 00.0.0.FF / 00.0.c / 00.n / 00 / 01 / 02…** | Revisión interna `00.R.C.FF` (`FF` = fase: `IC` Conceptual, `IB` Base, `ID` Detalle, `IE` Ejecutiva; al pasar de fase cambia solo el sufijo; ejemplo `00.2.34.IB`; el as-built no lleva sufijo): `00.0.0` línea base interna (todo documento nace aquí); `C` (último dígito) suma 1 por **cada comentario** incorporado, sea de la revisión interna, del cliente o de la auditoría (`00.0.1`, `00.0.2`…); `R` (dígito intermedio) es el número de la `rfc-n` que lo originó y pone `C` en cero (`00.1`, luego `00.1.1`…); `00` es lo que **siempre** ve el cliente en toda entrega de desarrollo; `01` es el as-built de todo el proyecto; `02`, `03`, `04`… son las modificaciones posteriores, del proyecto completo, siempre por rfc (`DOCUMENT_RULES.md`, sección 9). |
| **DRAWING_STATUS** | Listado de planos y diagramas que dibuja el usuario, con su estado (`PLANNED`, `CAD_INPUT`, `DRAWN`, `REVIEWED`, `ENTREGADO`). Lo actualiza el usuario a mano y es la **fuente única** del estado de los planos. |
| **Frase fija** | Texto exacto que el usuario le dice a Claude, de dos tipos: *comando* (inicia trabajo de Claude) y *decisión* (respuesta del usuario en un punto de control). El estándar único está en `COMMANDS.md`. |
| **Editable** | Archivo de trabajo que se modifica; vive solo en `02-engineering`. |
| **Entregable limpio (carpeta de entrega)** | Copia depurada de lo editable aprobado, que se guarda en `06-deliverables` y es de solo lectura (`folder-templates.md`, 4.5). |
| **As-built** | Documentación conforme a obra, actualizada con lo realmente construido (Rev 01). |
| **Pliego** | Documento técnico contractual (`PG`) que fija qué se ejecuta, bajo qué normas, cómo, cómo debe quedar, cómo se verifica y de qué responde el Contratista. Es **un solo documento** con un código y una revisión, redactado en capítulos numerados (`TECHNICAL_SPECIFICATIONS_GUIDE.md`). |
| **Capítulo (de pliego)** | Cada segmento del pliego, en su propio archivo Markdown numerado (`01_Scope.md`, `02_Descriptive_Report.md`…) en `02-engineering/TECHNICAL_SPECS`. Responde una única pregunta, no tiene código ni revisión propios (lleva los del pliego) y no se entrega suelto: al entregar se consolida con los demás en orden numérico. |

### 4.3 Fases de ingeniería y emisiones documentales

Un proyecto no pasa directamente de la ingeniería a ifc: la ingeniería madura por fases, y cada fase aumenta el nivel de definición de los documentos. El mismo documento (mismo código) puede existir en varias fases; **no se copia, evoluciona**: cada fase agrega información y nunca elimina la definición obtenida en una fase anterior.

| Código | Fase | Pregunta que responde | Qué se define |
|---|---|---|---|
| `IC` | Ingeniería Conceptual | ¿Qué se quiere hacer? | Objetivo, alcance general, filosofía de operación, alternativas técnicas, arquitectura general y estimaciones preliminares. Sin cálculos completos ni detalles constructivos |
| `IB` | Ingeniería Base | ¿Cuál es la solución seleccionada? | Solución elegida, dimensionamientos preliminares, potencias, capacidades, equipos principales y arquitectura validada. Alcanza para validar la solución, todavía no para construirla |
| `ID` | Ingeniería de Detalle | ¿Cómo debe diseñarse? | Memorias de cálculo, protecciones, selección técnica de equipos, diagramas, planos de ingeniería, especificaciones y pliegos. La solución queda completamente definida desde lo técnico; puede faltar información para construcción, compras y montaje |
| `IE` | Ingeniería Ejecutiva | ¿Cómo se construye exactamente? | Codificación definitiva, lista final de materiales, hojas de datos finales, numeración de cables e instrumentos, lista I/O, planos de montaje, borneras, conexionados, interconexiones y detalles constructivos. Ya sirve para compras, fabricación, construcción, montaje y puesta en marcha |
| `ASB` | Conforme a obra (As-Built) | ¿Qué se construyó realmente? | Planos, diagramas, listados, hojas de datos y equipamiento actualizados con los cambios de obra, redlines y sustituciones de equipos. Representa lo ejecutado en campo |

Ejemplo de cómo crece un mismo dato (interruptor general): en Base, `400 A`; en Detalle, `400 A`, `50 kA`, curva electrónica; en Ejecutiva, el modelo y su código (por ejemplo ABB XT5N 400), `400 A`, `50 kA`, código interno, ubicación y detalle de montaje; en As-Built, lo instalado (por ejemplo Schneider NSX400F), el motivo (indisponibilidad del equipo especificado) y el acta de cambio (`rfc-nnn`, o el número del acta del cliente).

La matriz que indica en qué fases aparece cada entregable está en `deliverables.md`, sección 10. La fase en que se encuentra cada documento figura en la LME (columna *Fase*) y en el sufijo de su revisión (`.IC`, `.IB`, `.ID`, `.IE`).

**Secuencia de cada fase.** Las fases `IC`, `IB` y `ID` siguen la misma secuencia, y la aprobación del ifa de una fase es el disparador de la siguiente:

```text
IC: paquetes (ifr) → auditoría → AUDITED → ifa → cliente aprueba ─► dispara IB
IB: paquetes (ifr) → auditoría → AUDITED → ifa → cliente aprueba ─► dispara ID
ID: paquetes (ifr) → auditoría → AUDITED → ifa → cliente aprueba ─► dispara IE
IE: paquetes (ifr) → auditoría → AUDITED → ifc ─► CONSTRUCTION
     (la Ejecutiva se actualiza constantemente durante la obra) ─► dispara ASB (Rev 01)
```

- **ifr (emisión interna)** puede repetirse cuantas veces haga falta. Antes de enviar algo al cliente, el conjunto debe estar **aprobado internamente**: paquetes `REVIEWED` y auditoría aprobada (`AUDITED`).
- **ifa** va al cliente, que aprueba, aprueba con observaciones o rechaza. Las observaciones del cliente **siempre** vuelven primero a revisión interna (ifr) y a auditoría de lo cambiado antes de reenviarse. Sin excepciones.
- **ifc** libera la documentación para construir; no es una aprobación documental.
- **Fases no contratadas.** El contrato puede cubrir solo algunas fases (por ejemplo, arrancar en Detalle). Las fases contratadas y la fase de inicio se registran en `project-information.md`; omitir una fase o su ifa es una `DEC`. Si el contrato no incluye Ejecutiva, el ifc se prepara tras `cliente aprueba` de la última fase, con una auditoría **completa de consistencia entre todos los documentos** (no solo "que nada cambió"): por ejemplo, si cambió la capacidad de un interruptor en el unifilar y no en el multifilar ni en el pliego, el auditor debe reportarlo. Lo que el usuario no ve, Claude lo ve.

**Observación del cliente o de la revisión interna: ¿rfc o corrección documental?** No toda observación genera una rfc.

- **Generan rfc** las que modifican: la línea base, el alcance, los requisitos del cliente, los parámetros maestros, la filosofía de operación, los criterios de diseño, las potencias, el equipamiento aprobado o las decisiones registradas. Ejemplos: agregar un tablero, agregar un generador, modificar la potencia instalada.
- **No generan rfc** las que corrigen errores documentales, omisiones, inconsistencias, problemas de representación o información ya definida pero mal reflejada. Ejemplo: el circuito AA-03 existe pero no aparece en el unifilar. No modifica la línea base: corrige la documentación.

Claude propone la clasificación de cada comentario y el usuario la confirma (`confirmar clasificación`). En ambos casos el comentario queda registrado como `REV-nnn` y suma a la revisión del documento (`DOCUMENT_RULES.md`, sección 9).
