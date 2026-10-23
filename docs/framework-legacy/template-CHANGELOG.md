# CHANGELOG

Registra los cambios del framework, los cambios estructurales, los cambios de versión y, en un proyecto, los eventos documentales relevantes generados por scripts. Más reciente primero.


## 2026-10-14 — Auto-reset del TEMPLATE tras `iniciar proyecto`

### Cambios
- **`99_CORE/RULES/M3_interview_copy_and_baseline.md`**: (1) Tabla de copia, fila 7: `01_INPUT/` pasa a generación dinámica — Claude crea las subcarpetas de clasificación, `README.md` y `_INPUT_REGISTER.md` en el **proyecto**, no en la maestra. (2) Paso 12 «Auto-reset del TEMPLATE»: al finalizar la Fase 4, vacía `99_UNCLASSIFIED/`, restablece `STARTING_DATA.md` y limpia `CHANGELOG.md`; las subcarpetas de clasificación no existen en la maestra por lo que no hay nada extra que borrar.
- **`01_INPUT/`**: reestructurado a estado mínimo. Eliminados: `01_CONTRACTS_AND_TENDERS/`, `03_CLIENT_STANDARDS/`, `04_EXISTING_DOCUMENTS/`, `05_SITE_DATA/`, `06_EQUIPMENT_DATA/`, `07_CODES_AND_STANDARDS/`, `08_PREVIOUS_PROJECTS/`, `09_COMMUNICATIONS/`, `README.md`, `_INPUT_REGISTER.md`. La maestra conserva solo tres elementos: `00_SETUP/STARTING_DATA.md`, `02_REQUIREMENTS/input_for_sld.xlsx` y `99_UNCLASSIFIED/` (vacía). Las carpetas de clasificación se crean dinámicamente en el proyecto durante `iniciar proyecto`.
- **`01_INPUT/00_SETUP/STARTING_DATA.md`**: restablecido a estado por defecto: todos los campos a `DEFINIR`, todas las casillas desmarcadas (`[ ]`), solo `Responsable: Daniel A. Villena H.` conservado.
- **`80_DOCS/index.html`** (wiki): descripción de `iniciar proyecto` en la tabla COMMANDS actualizada.


## 2026-10-13 — Tres correcciones estructurales: PROJECT_DATA, 90_MANAGEMENT y wiki 80_DOCS

### 98_LIBRARY/02_PROJECT_DATA → PROJECT_DATA
- Renombrado `98_LIBRARY/02_PROJECT_DATA/` → `98_LIBRARY/PROJECT_DATA/`. El prefijo `02_` era un residuo de la numeración de carpetas visibles del proyecto y generaba confusión.
- Eliminado `STARTING_DATA.md` duplicado (el original está en `01_INPUT/00_SETUP/`).
- Actualizada referencia en `99_CORE/RULES/M3_interview_copy_and_baseline.md`.

### 90_MANAGEMENT/ — archivos .md son documentos de trabajo del usuario
- Los archivos `.md` de `90_MANAGEMENT/` son documentos vivos editables por el usuario (PROJECT_STATUS, AUDIT_REGISTER, PUNCH_LIST, CLOSE_CHECKLIST, REDLINE_LOG). Correctamente ubicados; no se movieron.
- Creado `90_MANAGEMENT/README.md`: tabla de archivos con quién los llena y cuándo.

### Creación de 80_DOCS/ — wiki del framework
- Nueva carpeta `80_DOCS/` como wiki del framework: todo lo que el usuario lee para entender y operar el sistema.
- Movidos desde `99_CORE/` a `80_DOCS/`: `FRAMEWORK_GUIDE.md`, `FRAMEWORK_QUICK.md`, `COMMANDS.md`, `CAD_STANDARDS.md`, `DESIGN_RULES.md`, `DOCUMENT_RULES.md`, `TECHNICAL_SPECIFICATIONS_GUIDE.md`, `MANAGEMENT_TEMPLATES.md`, `FOLDER_TEMPLATES.md`.
- `99_CORE/` queda solo con el motor: `CLAUDE.md`, `RULES/`, `SCRIPTS/`, `MIGRATION/`.
- Creado `80_DOCS/README.md` como índice de la wiki.
- Actualizado árbol en `99_CORE/CLAUDE.md` (section 4) para reflejar la nueva estructura.

## 2026-10-13 — Auditoría y optimización del framework (lazy-load + estructura)

### Motivación
Daniel solicitó: (1) verificar todo el framework y mover lo que debería estar oculto; (2) reducir el peso de CLAUDE.md evitando que cargue todos los plugins siempre.

### Cambios estructurales
- **Backup movido a `.project/`**: `_BACKUP_pre-optimizacion_2026-10-12.tgz` (813 KB) estaba en la raíz visible del repositorio. Movido a `.project/` (carpeta interna oculta).
- **Árbol de section 4 en `CLAUDE.md` corregido**: los archivos `STARTING_DATA.md`, `PROJECT_CHARTER.md`, `GOALS.md`, etc. estaban incorrectamente anidados bajo `02_ENGINEERING/` en el árbol. Corregido: ahora aparecen bajo `90_MANAGEMENT/` donde realmente residen.

### Optimización de carga — módulo M9
- **Nuevo archivo `99_CORE/RULES/M9_engineering_checklist.md`**: consolida el contenido de las secciones 7, 9, 10, 12 y 15 de `CLAUDE.md` (checklists de pre-generación, creación de carpetas, clientes recurrentes, QA, buenas prácticas).
- **`CLAUDE.md` secciones 7, 9, 10, 12, 15 simplificadas**: cada una reemplazada por una línea de referencia a M9. Reducción: 35,136 → 31,724 caracteres (−9%).
- M9 se carga bajo demanda igual que el resto de módulos de `99_CORE/RULES/`.

### Optimización de carga — plugins lazy-load
- **Nueva sección 3.2 en `CLAUDE.md`**: tabla de 7 filas con disparador explícito por plugin (SLD, MLD, LAMINAS_IRAM, CALCULATIONS, EQUIPMENT, MANAGEMENT, STANDARDS). Claude ahora solo carga el plugin cuando el pedido lo requiere explícitamente.

### Archivos modificados
- `CHANGELOG.md` (este archivo)
- `99_CORE/CLAUDE.md` (sección 3.2 añadida, secciones 7/9/10/12/15 simplificadas, árbol section 4 corregido)
- `99_CORE/RULES/M9_engineering_checklist.md` (nuevo)
- `.project/_BACKUP_pre-optimizacion_2026-10-12.tgz` (movido desde raíz)

## 2026-10-13 — Corrección del modo «Solo ingeniería»: coherencia de documentos y puerta

### Cambios
- **`99_CORE/FRAMEWORK_GUIDE.md`**: corregidas las filas de `ISSUE_LOG.md` y `EFFORT_BASELINE.md` (estaban marcadas «solo gestión activo» pero ambas se usan en «Solo ingeniería» también); ajustadas las filas de los documentos de `Governance/` para reflejar que existen en ambos modos (en «Solo ingeniería» las secciones que no aplican se marcan «no aplica»).
- **`99_CORE/RULES/M8_management_documents.md`**: criteria de la puerta «Listo para ejecutar» (section 3) separadas por modo: `RISK_PLAN`, `COMM_PLAN` y `STAKEHOLDERS` completos se exigen solo en «Ingeniería + gestión»; en «Solo ingeniería» basta con charter aprobado, plan aprobado, `EFFORT_BASELINE` y `ISSUE_LOG` sin bloqueos.
- **`99_CORE/RULES/M3_interview_copy_and_baseline.md`**: Fase 4 paso 8 explicitado: `EFFORT_BASELINE.md` se genera en **ambos modos** (no solo en gestión); `SCHEDULE_CCPM.md` solo en «Ingeniería + gestión».


## 2026-10-13 — canvas_exporter.py (CAL-014 v0.1.0) — tres canvas de ciclo de vida

### Cambios
- Creado `98_LIBRARY/PLUGINS/CALCULATIONS/canvas_exporter.py` (CAL-014, v0.1.0): genera Lienzo de Planificación, Lienzo de Cierre de Fase y Lienzo de Cierre del Proyecto.
- Visual idéntico al charter ejecutivo: 1660×1225 px, color #00829b, CSS box/tab.
- Tres plantillas de referencia: `PLANNING_CANVAS_template.md`, `PHASE_CANVAS_template.md`, `CLOSURE_CANVAS_template.md`.
- `COMMANDS.md` actualizado: `aprobar charter` genera el Lienzo de Planificación; `cerrar fase [nombre]` genera el Lienzo de Cierre de Fase; `cerrar proyecto` genera el Lienzo de Cierre del Proyecto.
- `CLAUDE.md` actualizado con referencias a PLANNING_CANVAS.md, PHASE_CANVAS.md y CLOSURE_CANVAS.md.
- Todos los canvas (PDF + Word) salen en `90_MANAGEMENT/CHARTER/` via `_encontrar_raiz()`.



## 2026-10-13 — Segmentación de 01_INPUT en Sección A y B

### Cambios
- Creada `01_INPUT/00_SETUP/` como sección A (usuario llena antes de arrancar).
- `STARTING_DATA.md` movido de `98_LIBRARY/02_PROJECT_DATA/` a `01_INPUT/00_SETUP/STARTING_DATA.md`.
- Las carpetas `01_CONTRACTS_AND_TENDERS/` a `99_UNCLASSIFIED/` forman la sección B (documentación del cliente).
- Actualizado `01_INPUT/README.md`, `99_CORE/CLAUDE.md`, `99_CORE/COMMANDS.md` y `99_CORE/FOLDER_TEMPLATES.md`.


## 2026-10-13 — Reestructuración INPUT/OUTPUT (v3.0)

### Cambios estructurales
- Eliminada la carpeta `02_PROJECT/` del árbol visible. Su contenido se movió a `98_LIBRARY/02_PROJECT_DATA/` (interno, no visible para el usuario).
- Renumeración de carpetas visibles (< 20):
  - `03_ENGINEERING` → `02_ENGINEERING`
  - `04_REVIEW` → `03_REVIEW`
  - `05_AUDIT` → `04_AUDIT`
  - `06_RELEASED` → `05_RELEASED`
  - `07_DELIVERABLES` → `06_DELIVERABLES`
- Nuevo modelo INPUT/OUTPUT: el usuario ve `01_INPUT` (datos), `02_ENGINEERING` (outputs de ingeniería), `90_MANAGEMENT` (outputs de gestión), `98_LIBRARY` (motor), `99_CORE` (reglas).
- Actualizadas referencias en `library.json`, todos los `plugin.json` y documentación de `99_CORE`.


## 2026-10-12 — A8: FRAMEWORK_GUIDE partido en guía rápida + referencia

- Nuevo `99_CORE/FRAMEWORK_QUICK.md` (96 líneas): quién hace qué, recorrido completo, checklist diario, dónde está cada cosa — para consulta mientras trabaja
- `FRAMEWORK_GUIDE.md` v1.3: puntero a FRAMEWORK_QUICK al inicio; conserva las secciones detalladas (paso a paso, ejemplo, glosario)
- `FOLDER_TEMPLATES.md`: `FRAMEWORK_QUICK.md` añadido a la fila de `99_CORE/`

## 2026-10-12 — Implementación de ítems de script diferidos (fwlib v1.1.0)

- **A1** `SEND_TO_REVIEW --permitir-varios`: valida que el DEC exista en `ASSUMPTIONS_AND_DECISIONS.md`
- **A2** `SEND_TO_AUDIT --solo-documental DEC-nnn`: permite avanzar con `APPROVED_WITH_COMMENTS` si comentarios son documentales
- **A4** `CHECK_STATE`: muestra fase PM², emisión activa y próxima puerta en cabecera
- **M2** `SYNC_CCPM.py`: actualiza `inicio_real`/`fin_real` en `ccpm_input.json` desde los LEDGER
- **M3** `PROGRESS_REPORT.py`: genera borrador de reporte de avance en Markdown
- **M4** `states.json`: declaración JSON de la máquina de estados (fuente única, generada por `CHECK_STATE --actualizar-states`)
- **M7** `fwlib.__version__ = 1.1.0`; `CHECK_STATE --actualizar-states` regenera `states.json`; aviso de drift de versión
- **G3** `EFFORT_REPORT.py`: compara horas estimadas vs reales en `EFFORT_BASELINE.md`, calcula SPI de esfuerzo
- **G5** `CHECK_INF.py`: lista incidencias `INF` vencidas o próximas a vencer en `ISSUE_LOG.md`
- **G8** `DASHBOARD.py`: genera dashboard de una página con fase, avance, incidencias y riesgos

## 2026-10-12 — Renombres de frases de control de flujo

- `aprobar plan` → `aprobar inicio` (6 archivos; preserva `aprobar plan de paquetes`)
- `cliente acepta` → `aceptación firmada` (6 archivos)
- Archivos: ACCEPTANCE_TRANSITION_PLAN.md, CLAUDE.md, COMMANDS.md, MANAGEMENT_TEMPLATES.md, M8_management_documents.md, CHANGELOG.md

## 2026-10-12 — Finalización gestión: archivos maestros y tabla de ubicaciones

- `PROJECT_STATUS.md`: se eliminan las secciones D («Completado») y E («En desarrollo»); estos datos se derivan del `LEDGER` y de `DELIVERABLES.md`.
- `FOLDER_TEMPLATES.md` 4.7: tabla de ubicaciones actualizada con `MANAGEMENT_TEMPLATES.md`, `M1…M8`, `ISSUE_LOG.md` y todos los nuevos archivos de `Governance/`, `Planning/` y `Reports/`.
- `FRAMEWORK_GUIDE.md`: referencia `M1…M8`; nuevas filas en «Mapa de archivos de gestión» para los 15 documentos de gestión del modo Ingeniería + gestión del proyecto.

## 2026-10-12 — Gestión completa: documentos, puertas y registros (basado en PM²)

- Nuevo módulo `99_CORE/RULES/M8_management_documents.md`: catálogo D01 a D28, puertas («listo para ejecutar», fin de fase, listo para cerrar), reglas de riesgos, incidencias, esfuerzo, lecciones y revisión liviana.
- Nuevos registros y planes: `Governance/` (manual, interesados, comunicaciones, riesgos, calidad y HSE, adquisiciones, aceptación y transición, NCR, consultas de obra), `Planning/EFFORT_BASELINE.md`, `ISSUE_LOG.md` (reemplaza BLQ / PND / INF / PA conservando los prefijos como tipo), `REDLINE_LOG`, `PUNCH_LIST`, `CLOSE_CHECKLIST`.
- Nuevas plantillas de informes y actas en `99_CORE/MANAGEMENT_TEMPLATES.md` (D10 a D15, D17 a D20, D22, D25, D26, D28).
- `COMMANDS.md` 1.3: frases `aprobar inicio` ●, `cerrar fase` ●, `aceptación firmada` ●, `registrar incidencia`, `registrar reunión`, `registrar consulta de obra`, `registrar visita de obra`, `generar informe de estado | de riesgos | de esfuerzo | de cambios | de cierre`, `tablero`.
- `PROJECT_CHARTER.md`: matriz RASCI de hitos (6.2). `STARTING_DATA.md`: el modo por defecto incluye gestión mínima.
- `PROJECT_STATUS.md`: se eliminan las secciones «Estado por documento» y «Riesgos abiertos» (datos derivados del `LEDGER` y del registro `RIE-nnn`).
- Se elimina la tabla duplicada de frases `M4_fixed_phrases.md`: `COMMANDS.md` es la fuente única.
- Corregidas referencias antiguas (`Cambios/` → `90_MANAGEMENT/RFC/`, «antes SC-nnn»).
- `document_verifier.py`: reconoce los nuevos archivos de gestión como archivos del framework.
- Pendiente de script (definido en M8, sección 5, sin efecto aún): dos paquetes simultáneos (uno en revisión y uno en elaboración), avance con comentarios documentales, estado de una línea, fechas reales en `ccpm.py`, borradores automáticos de informes, tablero generado, aviso de versión del motor.

## 2026-10-09 — Charter ejecutivo en PDF y auditoría de consistencia

- `PROJECT_CHARTER_EXECUTIVE.md` pasa a ser el **contenido** del lienzo (cajas con nombre fijo, tablas, comentarios `<!-- fuente: ID -->`); la salida que se muestra es `PROJECT_CHARTER_EXECUTIVE.pdf`, de una página, igual al *Project Initiation Canvas* de PM² (sin logos). Se eligió HTML + CSS exportado a PDF porque Word no reproduce el lienzo con fidelidad.
- Nuevo `charter_exporter.py` (CAL-013): dibuja el lienzo con Chromium y estampa el `sha256` del `.md` en el pie y en los metadatos del PDF; `--verificar` compara el sello.
- `document_verifier.py` 0.8.0: valida que el charter técnico y el ejecutivo digan lo mismo (versión, fecha, estado, IDs, niveles de riesgo, paquetes, hitos, costo) y que el PDF corresponda al `.md` vigente. `PROJECT_AUDIT.md`: nuevos A3-19 y A3-20. 325 pruebas.

## 2026-10-09 — Charter en dos salidas (técnica PM² y ejecutiva)

- `02_PROJECT/PROJECT_CHARTER.md` pasa a la estructura del *Project Charter* de PM² (control del documento, resumen ejecutivo, caso de negocio, descripción, costo-plazo-recursos, enfoque, gobierno, referencias) más las secciones propias del framework: plan de paquetes (7), preguntas pendientes (8) y línea base (9; antes sección 10).
- Nuevo `02_PROJECT/PROJECT_CHARTER_EXECUTIVE.md`: charter ejecutivo de una página con las cajas del *Project Initiation Canvas* de PM², en Markdown y sin logos, derivado del charter técnico; nuevo comando `charter ejecutivo`.
- Costo: `[DEFINIR]` por defecto; un monto solo con pedido expreso del usuario y `DEC-nnn` (RG-21).
- Nuevo ID `RIE-nnn` y registro de riesgos en `ASSUMPTIONS_AND_DECISIONS.md`; Claude propone los riesgos iniciales en el charter y se aprueban con `aprobar charter`.
- `document_verifier.py` 0.7.1: reconoce `RIE-` y trata el charter ejecutivo como archivo del framework; 306 pruebas.

## 2026-10-09 — Nombres de archivos y carpetas en inglés

- Todos los archivos, carpetas y patrones de archivos generados pasan a inglés (p. ej. `CALCULOS`→`CALCULATIONS`, `Pliegos`→`TECHNICAL_SPECS`, `REVISION-nn`→`REVIEW-nn`, `verificador_documentos.py`→`document_verifier.py`).
- Solo se actualizaron las **referencias** a los nombres; el contenido interno sigue en español.
- Tabla completa de equivalencias en `99_CORE/MIGRATION/NAME_EQUIVALENCES.md`. Las entradas anteriores de este CHANGELOG y los documentos de `MIGRATION/` conservan los nombres históricos.
- Pruebas: 305 de la biblioteca y 27 del flujo, en verde.

## 2026-10-09 — Reestructuración arquitectónica, fase B: flujo por ubicación

- **El estado de un paquete es su ubicación** (`02_ENGINEERING` → `03_REVIEW/REVIEW_PACKAGES` → `04_AUDIT/AUDIT_PACKAGES` → `05_RELEASED` → copia en `06_DELIVERABLES`).
- Nuevo `99_CORE/SCRIPTS/` (WF-001): `SEND_TO_REVIEW`, `RETURN_TO_ENGINEERING`, `SEND_TO_AUDIT`, `APPROVE_AUDIT`, `RELEASE_DOCUMENTS`, `ISSUE_IFA`, `ISSUE_IFC`, `ISSUE_ASBUILT`, `CONFIRM_SENT`, `START_ASBUILT`, `CLOSE_PROJECT`, `CHECK_STATE`; biblioteca `fwlib.py` / `workflow.py`; 27 pruebas.
- Registro en `90_MANAGEMENT/LEDGER/` (manifiesto SHA-256 por `PQ-nn`, eventos, estado calculado).
- Regla: solo `APPROVED` avanza; todo paquete modificado vuelve a Ingeniería; auditoría única por emisión sobre el conjunto; DWG + XREF + PDF viajan juntos y Claude revisa solo el PDF.
- Campo `Resultado:` en la hoja de revisión y `Emisión:` / `Paquetes:` / `Resultado:` en el informe de auditoría.
- Reglas actualizadas: `M6` (11.2), `COMMANDS`, `REVIEW_SHEET`, `PROJECT_AUDIT` (A1-20), `DOCUMENT_RULES`, `CLAUDE`, `FOLDER_TEMPLATES`, `FRAMEWORK_GUIDE`.
- `verificador_documentos.py` 0.7.0: omite `LEDGER` y los `RELEASE_*` generados.

## 2026-10-09 — Reestructuración arquitectónica, fase A

- Estructura física reorganizada: `01_INPUT`, `02_PROJECT`, `02_ENGINEERING`, `03_REVIEW`, `04_AUDIT`, `05_RELEASED`, `06_DELIVERABLES`, `90_MANAGEMENT`, `98_LIBRARY`, `99_CORE`.
- `CLAUDE.md` pasa a `99_CORE/CLAUDE.md`; la raíz conserva un archivo de arranque que lo importa.
- `99-BIBLIOTECA` pasa a `98_LIBRARY`; `REGLAS` pasa a `99_CORE/RULES`.
- Se agregan `README.md`, `CHANGELOG.md`, `.gitignore` y `.gitattributes`.
- Sin cambios de contenido ni de lógica del flujo.

## [2026-10-13] — Unificación de nombres de carpetas y activos internos

### Cambios
- **Renombrado masivo de carpetas**: todas las subcarpetas del template unificadas a `ALL_UPPER_WITH_UNDERSCORES`. Afecta `02_ENGINEERING/`, `03_REVIEW/`, `04_AUDIT/`, `06_DELIVERABLES/`, `90_MANAGEMENT/`, `98_LIBRARY/PLUGINS/*/` y `98_LIBRARY/02_PROJECT_DATA/`. 65 directorios renombrados.
- **Activos internos marcados como master-only** (M3, fila 6): `ASSETS/`, `OUTPUT/`, `TESTS/`, `TEMPLATES/` dentro de cada plugin y `98_LIBRARY/CORE/` ya **no se copian** al crear un proyecto nuevo desde la plantilla; son exclusivos de la maestra para autooptimización del framework.
- **31 archivos .md actualizados** con las nuevas rutas de carpetas (referencias de texto en CLAUDE.md, COMMANDS.md, FRAMEWORK_GUIDE.md, FOLDER_TEMPLATES.md, DOCUMENT_RULES.md, scripts de cálculo y más).

## [2026-10-13] charter_exporter v0.2.0 — Word automático + rutas .project/

### Cambios
- `charter_exporter.py` actualizado a v0.2.0
- Nuevo: generación de Word (`.docx`) via Pandoc (sin intervención manual)
- Nuevo: `_encontrar_raiz()` — detecta automáticamente la raíz del proyecto
- Nuevo: rutas por defecto auto-derivadas:
  - PDF → `90_MANAGEMENT/CHARTER/`
  - Word → `90_MANAGEMENT/CHARTER/`
  - HTML (intermedio) → `.project/render/` (invisible al usuario)
- Nuevo: `_actualizar_seal()` — actualiza `.project/SEAL.json` con el sha256 del `.md`
- Nuevo: parámetro `--sin-docx` para omitir la generación Word
- `.project/` inicializado con `data/`, `render/` y `SEAL.json`
- `90_MANAGEMENT/CHARTER/` creado como destino de entregables del charter
