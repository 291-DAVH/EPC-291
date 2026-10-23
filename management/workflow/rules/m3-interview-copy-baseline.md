# Módulo M3 — Comando «iniciar proyecto»: copia, modo de gestión, análisis de la entrada, charter y generación

> Módulo de `CLAUDE.md` (sección 8.1, continuación: copia de la plantilla, modo de gestión y Fases 1 a 4). Tiene la **misma autoridad** que `CLAUDE.md`: el texto se movió aquí, sin cambios de fondo, para que `CLAUDE.md` se lea corto en cada sesión. La numeración de las secciones se conserva, de modo que las referencias «`CLAUDE.md`, 8.1» y similares siguen valiendo. Se lee **a demanda**, cuando `CLAUDE.md` (sección 3.1) lo indica.

---

**Copia de la plantilla (Paso 1 de `M2`).** Se aplica solo si la carpeta de trabajo **no** se llama como el nombre de carpeta indicado en `starting-data.md` (es decir, se trabajó en la maestra): el proyecto se crea en una **copia nueva** con ese nombre (reglas de nombre en `folder-templates.md`, 4.3). Si el usuario ya duplicó la plantilla y le puso ese nombre, no se copia nada: se trabaja en esa carpeta. La copia contiene esta **lista cerrada**, y nada más:

| N.º | Qué se copia | Destino en el proyecto |
|---|---|---|
| 1 | Los archivos de arranque de la raíz de la maestra: `CLAUDE.md` (bootstrap que importa `.claude/rules/framework.md`), `README.md`, `CHANGELOG.md` (el del proyecto nace vacío salvo la entrada de creación), `.gitignore` y `.gitattributes` | Raíz del proyecto |
| 2 | `90-management/` (outputs auto-generados: charter, canvases, reportes) | `90-management/` |
| 3 | `90-management/` completa, con sus 9 archivos `.md` (`PROJECT_STATUS`, `CHANGE_REQUESTS`, `ASSUMPTIONS_AND_decisions`, `TRACEABILITY_MATRIX`, `DELIVERABLES`, `DRAWING_STATUS`, `lessons_LEARNED`, `SCHEDULE_CCPM`, `AUDIT_REGISTER`) y su estructura de carpetas | `90-management/` |
| 4 | `03-review/` (con `review-sheet.md`), `04-audit/` (con `project-audit.md`), `05-released/` y `06-deliverables/`, con su estructura y `.gitkeep` | Raíz del proyecto |
| 5 | `.claude/` completa **salvo** `FRAMEWORK_GUIDE.md` y `MIGRATION/`, que viven solo en la maestra (la maestra tiene 26 `.md` de gestión y guías en total, sin contar los módulos `RULES/`) | `.claude/` |
| 6 | `.claude/library/` — solo los plugins de trabajo: `standards/`, `equipment/`, `calculations/`, `laminas-iram/`, `mld-lv/`, `mld-mv/`, `sld-lv/`, `sld-mv/` y `project-data/`. **Se excluyen de la copia** (son exclusivos de la maestra): `*/assets/`, `*/output/`, `*/tests/`, `*/templates/` dentro de cada plugin (datos de autooptimización del framework), y `.claude/library/core/` (utilidades internas) | `.claude/library/` |
| 7 | `01-input/` — Claude **crea** las subcarpetas de clasificación (`01_CONTRACTS_AND_TENDERS/` a `09_communications/` y `99-unclassified/`, cada una con `.gitkeep`), `README.md` y `_INPUT_REGISTER.md` en el proyecto (no existen en la maestra; se generan aquí); copia `00-setup/starting-data.md` (en estado CONSUMIDO), `02-requirements/input_for_sld.xlsx` y **la documentación depositada en `99-unclassified`** | `01-input/` |
| 8 | `02-engineering/` según la plantilla elegida (`folder-templates.md`, 4.2 y A–E) | `02-engineering/` |

**Activos exclusivos de la maestra** (no se copian al proyecto): las subcarpetas `assets/`, `output/`, `tests/` y `templates/` dentro de cada plugin de `.claude/library/plugins/` contienen datos de entrenamiento, ejemplos de salida y suites de prueba usados para autooptimizar el framework. No aportan valor al proyecto; omitirlos mantiene la copia limpia y sin archivos internos.

Todas las carpetas de primer nivel se crean **en la misma raíz** (no dentro de una subcarpeta), con la estructura interna que fija `folder-templates.md`; En `project-information.md`, sección A, se registran la ruta de la maestra y la **versión de la plantilla** con la que parte el proyecto: versión y fecha de este archivo más la huella abreviada de la maestra, obtenida con `cd <ruta_maestra> && find CLAUDE.md 90-management 02-engineering 03-review 04-audit .claude -name '*.md' -type f | LC_ALL=C sort | xargs cat | sha256sum | cut -c1-12`.

**Modo de gestión.** Lo declara el usuario en `starting-data.md` (sección 7), que es su única fuente; Claude registra `DEC-001` y lo muestra en el charter:

| Aspecto | Solo ingeniería y trazabilidad documental (por defecto) | Ingeniería + gestión del proyecto |
|---|---|---|
| Cronograma `schedule-ccpm.md`, duraciones propuestas, buffers, `ccpm.py` | No se generan; `schedule-ccpm.md` queda sin uso (se marca «No aplica: modo solo ingeniería») | Se generan y se actualizan |
| Plan de paquetes | Orden y dependencias, sin duraciones | Con duraciones propuestas |
| Informe de avance | Avance por entregables y paquetes, estado de revisiones, rfc y comentarios; sin sección de cronograma ni zona de buffer | Completo, con cadena crítica y buffer |
| Auditoría A4-12 (cronograma) | No aplica | Aplica |
| Plazo contractual (`starting-data.md`, sección 6) | Dato del contrato; Claude no lo controla ni lo proyecta | Se contrasta con el cronograma |
| Trazabilidad documental, revisiones, rfc, auditorías, emisiones ifa / ifc | Se mantienen íntegras | Se mantienen íntegras |

El usuario puede pasar al modo con gestión en cualquier momento con `activar gestión del proyecto` (Claude registra una `DEC-nnn`, propone las duraciones y genera el cronograma). En modo «Solo ingeniería», `generar cronograma` y `actualizar cronograma` no se ejecutan: Claude avisa y ofrece activar la gestión.

#### Fase 1 — Análisis de la entrada (sin preguntar)

Analizar **toda** la información disponible. La fuente principal es la carpeta **`01-input`**, con lo que el usuario depositó en `99-unclassified`: leerla completa, **clasificar su contenido** (mover cada archivo de `99-unclassified` a la subcarpeta que le corresponde y registrarlo en `_INPUT_REGISTER.md`; los originales **no se modifican ni se borran**) y completar `_INPUT_REGISTER.md` **sin transcribir datos económicos** (principio 14 de 6.1). Señalar duplicados, revisiones superadas, archivos ilegibles (los Office o presentaciones que no se lean bien se convierten a PDF o a imágenes de página con `input_converter.py`, CAL-012, sin tocar el original y registrando la copia como «copia de lectura»), documentos que se contradicen y documentos que parecen faltar. Además:

1. Pliegos de licitación, contratos y especificaciones técnicas existentes.
2. Planos y documentos recibidos por adjuntos o en otras ubicaciones.
3. Estándares corporativos y plantillas documentales del cliente.
4. Proyectos anteriores del mismo cliente (estructura, nomenclatura, CAD, criterios, decisiones).
5. Estructuras de carpetas existentes.
6. Información ya cargada en los archivos del framework.

**Pedido inicial dado de palabra.** Si el encargo llega por el chat y no como archivo, Claude lo transcribe como `MINUTES-000_Initial_Request.md` en `01-input/09_communications/` (fecha, autor y texto sin interpretar), lo registra en `_INPUT_REGISTER.md` y lo cita como fuente (`MINUTES-000`, sección) de los datos que de él provengan. Si en `starting-data.md`, sección 8, el usuario dejó notas, se citan igual como fuente.

Resultado: `_INPUT_REGISTER.md` completo, con la fuente de cada dato extraído. No hay resumen aparte: lo extraído se vuelca directamente en la Fase 2 y se resume en el charter.

#### Fase 2 — Llenado de las fuentes y detección de lo que falta

Con lo extraído, Claude completa **cada dato en el único archivo que le corresponde** (mapa de funciones únicas), con su fuente y estado:

| Archivo | Función única | Qué se vuelca |
|---|---|---|
| `starting-data.md` | Datos que declara el usuario | Nada: solo se lee (se completa un dato en blanco si la documentación lo resuelve con certeza, citando la fuente) |
| `project-information.md` | Hechos técnicos | Descripción, ubicación, parámetros `PAR-nnn` y `PAR-<DISC>-nnn`, sistema de distribución, instalaciones, normas `NOR-nnn`, condiciones, restricciones operativas, históricos, contactos |
| `project-scope.md` | Alcance, exclusiones y aceptación | `ALD-nnn` por disciplina declarada, `EXC-nnn`, `CAC-nnn` |
| `goals.md` | Para qué existe el proyecto | Objetivos, restricciones, criterios de éxito |
| `client-requirements.md` | Qué exige el cliente | Requisitos `CR-nnn` |
| `project-charter.md` | Vista consolidada y línea base | Resumen con IDs (Fase 3) |

Reglas:

1. **No se pregunta nada en esta fase.** Todo lo que falta o requiere confirmación se registra como `[DEFINIR]` (o `[VERIFICAR]` si es dudoso), se crea el `INF-nnn` y se agrega a la **lista de consultas pendientes**, clasificada por destinatario (**Cliente** o **Ingeniería**) en `project-status.md`, sección K. Nunca se pregunta lo que está en `starting-data.md` ni lo que la documentación ya resolvió.
2. Con la carpeta de información vacía o con información insuficiente, se cubren **todos** los bloques de la tabla de abajo: cada hueco queda como `INF-nnn` y como una pregunta del charter.
3. Un dato nunca se resuelve en silencio: ante contradicciones entre documentos, se registra el conflicto y se pregunta.

Cobertura mínima (qué debe quedar resuelto o preguntado):

| Bloque | Contenido |
|---|---|
| **Información general** | Nombre y descripción del proyecto, ubicación, tipo de proyecto, disciplina principal y si el contrato exige una emisión ifa al cierre de cada fase. (Cliente, códigos, qué se contrata, disciplinas, fases, plazo y modo de gestión ya vienen de `starting-data.md`.) |
| **Información técnica** | Condiciones del sitio, restricciones operativas y normas aplicables; y los **parámetros técnicos de cada disciplina involucrada** (`project-information.md`, secciones D y P). Ejemplos: eléctrica (tensiones, potencias, frecuencia, distribución, puesta a tierra, cortocircuito); incendio (riesgo, caudales, reserva de agua); HVAC (condiciones de diseño, cargas térmicas); civil (geotecnia, cargas); mecánica y cañerías (fluidos, presiones, temperaturas). Solo las disciplinas que aplican. |
| **Alcance** | Alcance de **cada disciplina involucrada** y de puesta en marcha: qué incluye **suministro**, **construcción**, **montaje** y **ensayos**, y qué queda excluido. |
| **Requisitos del cliente** | Técnicos, documentales, CAD, constructivos, de seguridad, restricciones de operación, estándares corporativos. |
| **Entregables** | Detalle de cada categoría marcada en `starting-data.md`, sección 5 (formato y medio de entrega). |
| **Criterios de aceptación** | FAT, SAT, pruebas funcionales, pruebas de protecciones, ensayos eléctricos, capacitación, entrega documental, requisitos de puesta en marcha. |

#### Fase 3 — Charter y línea base

Completadas las fuentes, Claude genera **dos salidas de la misma información**: `project-charter.md` (versión técnica completa con la estructura del *Project Charter* de PM², cada línea con el ID de su fuente) y `project-charter-executive.md` (contenido de la versión ejecutiva de una página, estilo *Project Initiation Canvas* de PM², para jefes y dirección: sin jerga, solo el lienzo, sin costos) y, a partir de él, el PDF `PROJECT_charter_EXECUTIVE.pdf` con `python3 -B .claude/library/calculations/charter_exporter.py 02_PROJECT/project-charter-executive.md` (HTML + CSS exportado a PDF). Antes de presentar corre `document_verifier.py`: el charter técnico y el ejecutivo deben decir lo mismo (A3-19) y el PDF debe llevar el sello del `.md` vigente (A3-20). Las presenta al usuario con un resumen breve en el chat. Las reglas de cada salida están en la guía de cada archivo. El charter técnico contiene:

1. Control del documento y nueve secciones más un apéndice: resumen ejecutivo (se escribe al final), caso de negocio, descripción (alcance IN / OUT, criterios de éxito y aceptación, necesidades, entregables, características, restricciones, supuestos y **riesgos iniciales propuestos `RIE-nnn`**), costo (`[DEFINIR]`, campo libre; un monto solo con pedido expreso del usuario y `DEC-nnn`, RG-21), plazo e hitos, recursos, enfoque y gestión de cambios, gobierno y partes interesadas, **plan de paquetes**, **preguntas pendientes**, línea base y referencias.
2. El **plan de paquetes de la fase de inicio** (para armarlo, Claude esboza la LME según `deliverables.md`, 4.1, ver Fase 4, paso 7): orden, paquete, documentos y dependencias. Hasta la aprobación es propuesta del charter; al aprobarse pasa a `deliverables.md`, que es su fuente.
3. **Solo en modo «Ingeniería + gestión»**, las **duraciones propuestas** por tipo de entregable (valores de partida de `schedule-ccpm.md`, sección 5, ajustados a la cantidad de entregables y recursos), el plazo resultante frente al límite contractual y, si hay déficit, las tres opciones de `schedule-ccpm.md` (recortar duraciones o alcance, plazo nuevo, más recursos). Si el plazo no aclara su unidad, la pregunta «¿horas transcurridas o de esfuerzo?» va entre las preguntas pendientes. En modo «Solo ingeniería» no hay duraciones ni plazos calculados.
4. **El único listado de preguntas** del arranque (sección 8): solo los `INF-nnn` abiertos que requieren al usuario, numerados, con opción sugerida.

El usuario contesta **en un solo mensaje** las preguntas y la frase fija `aprobar charter` o `corregir charter: …` (qué cambia, incluidas las duraciones y el orden de los paquetes; Claude corrige, regenera el charter y vuelve a presentarlo, sin repetir lo ya aprobado).

- Con `aprobar charter`, los riesgos propuestos pasan al registro de riesgos de `assumptions-and-decisions.md` y la definición queda como **línea base (versión 1.0)** registrada en la sección 9 del charter (y compartida por el charter ejecutivo), y se convierte en la **fuente de verdad**. Las respuestas dadas junto con la aprobación se vuelcan en sus archivos; si abren una duda nueva, se registra como `INF-nnn` y no se detiene el proceso.
- **Ningún documento puede contradecir la línea base sin una decisión formal registrada** en `assumptions-and-decisions.md`. Un cambio de línea base genera nueva versión del charter (se regenera) y re-evaluación de los documentos afectados.

#### Fase 4 — Generación automática (solo tras `aprobar charter`)

1. Seleccionar la plantilla de `folder-templates.md` y registrar `DEC-001`.
2. Crear la estructura documental correspondiente:
   - **Carpetas base de `02-engineering`** (siempre): `00-general/01-design-basis`, `00-general/02-interface-matrix`, `18-cad-resources/xref` y `19-temp/`.
   - **Carpetas de disciplina**: leer `starting-data.md`, sección 3. Por cada disciplina marcada `[x]`, crear la carpeta correspondiente según la tabla de `folder-templates.md`, sección 4.2.2, con su estructura interna completa (subcarpetas `01` a `15`, cada una con `.gitkeep`). **No crear carpetas para disciplinas no marcadas.**
3. Inicializar los archivos restantes del framework y completarlos con lo obtenido.
4. Registrar las decisiones iniciales (`DEC-001` a `DEC-004`; incluyen el modo de gestión, la aprobación del plan de paquetes y, si hubo, las opciones elegidas por déficit de plazo) y los supuestos.
5. Marcar la columna *Aplica* de `engineering-standards.md`. Revisar `DESIGN_RULES.md`: si el cliente o el reglamento desplazan una regla, registrar la decisión; completar las reglas `[DEFINIR]` que el proyecto necesite.
6. Cargar la Lista Maestra de Entregables (`deliverables.md`), con aplicabilidad justificada.
7. **Dividir en paquetes de revisión** (`deliverables.md`, 4.1): agrupar los entregables en paquetes de 1 a 3 documentos que van de la mano (la síntesis de cada cálculo con su memoria; cada capítulo de pliego, o grupo de capítulos, como paquete), completar las columnas *Paquete*, *Fase* y *Depende de* de la LME y ordenar los paquetes por dependencias (cálculos antes que diagramas, diagramas antes que listados, cálculos y diseño antes que el pliego; ver la tabla de ingeniería progresiva de 8.3 y `TECHNICAL_SPECIFICATIONS_GUIDE.md`, 4.10). El plan cubre la **fase de inicio** y es el aprobado en el charter, sin nueva aprobación. El de cada fase siguiente se propone cuando el cliente aprueba la anterior (`cliente aprueba`) y se confirma con `aprobar plan de paquetes` o `cambiar plan de paquetes: …`, registrado como `DEC-nnn`.
8. Generar la **matriz de trazabilidad inicial** (una fila por objetivo, requisito del cliente y criterio de aceptación). Generar `effort-baseline.md` (**ambos modos**): una fila por entregable con las horas estimadas; sin horas reales aún. En **modo «Ingeniería + gestión»**, generar además el **cronograma CCPM borrador** (`schedule-ccpm.md`; con las duraciones confirmadas en el charter; las no confirmadas quedan `[VERIFICAR]`; cada tarea con su `paquete` y la revisión del usuario como tarea propia por paquete). Seleccionar de `.claude/library/standards/standards-index.md` las normas relevantes y registrarlas como `NOR-nnn`.
9. Pasar `starting-data.md` a estado **CONSUMIDO** y dejar el proyecto en estado **`planning`**. Entregar la lista de consultas pendientes y el **primer paquete propuesto**.
10. **No iniciar la ingeniería** hasta que el usuario lo indique (`desarrollar paquete` o `siguiente paquete`).
11. Completar `drawing-status.md` (copiado con la plantilla): para cada plano o diagrama dibujado en CAD de la LME, **proponer** su fila (`PLANNED`, etapa, paquete) para que el usuario la confirme. A partir de ahí el usuario mantiene el estado a mano.
12. **Auto-reset del TEMPLATE (solo cuando se copió desde la maestra).** Si en el Paso 1 se creó la copia (el usuario trabajaba en la carpeta maestra), restablecer la maestra para que quede lista para el próximo proyecto:
   - `01-input/99-unclassified/`: **eliminar** todos los archivos depositados (ya copiados al proyecto); dejar solo el `.gitkeep`.
   - `01-input/`: las subcarpetas de clasificación (`01_CONTRACTS_AND_TENDERS/` a `09_communications/`) **no existen** en la maestra (se crearon en el proyecto, no aquí), por lo que no hay nada que borrar. La maestra queda con solo tres elementos: `00-setup/starting-data.md`, `02-requirements/input_for_sld.xlsx` y `99-unclassified/`.
   - `01-input/00-setup/starting-data.md`: todos los campos de texto a `DEFINIR`, todas las casillas desmarcadas (`[ ]`); conservar solo `Responsable: Daniel A. Villena H.` y el Estado `PENDIENTE DE COMPLETAR`.
   - `CHANGELOG.md`: eliminar las entradas del proyecto recién iniciado agregadas durante este proceso; conservar solo las entradas del framework preexistentes.
   - Informar al usuario: «Plantilla restablecida y lista para el próximo proyecto.»
   - `.claude/skills/` — **NO tocar.** Las carpetas `knowledge/`, `learning/`, `cache/` y `memory/` dentro de cada skill son datos de entrenamiento del usuario y **nunca** se modifican ni eliminan durante el reset. El reset solo limpia datos del proyecto (inputs, changelog), no el conocimiento acumulado en las skills.
   No aplica si el usuario ya duplicó la carpeta antes de completar `starting-data.md` (caso en que se trabaja en la copia desde el inicio).
