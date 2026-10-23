# Framework de gestión de proyectos de ingeniería industrial multidisciplina

## Propósito

Plantilla Markdown reutilizable para llevar proyectos de ingeniería industrial multidisciplina (eléctrica, civil, estructuras, arquitectura, mecánica, cañerías, HVAC, protección y detección de incendio, instrumentación y control, telecomunicaciones) con trazabilidad documental, revisión, auditoría y emisión controladas. La ingeniería es el producto principal; la gestión la organiza, la auditoría la valida y los entregables la comunican.

## Arquitectura

```text
01_INPUT          información recibida (buzón del usuario)
02_ENGINEERING    outputs de ingeniería: SLD, MLD, láminas, cálculos (solo lectura)
02_ENGINEERING    trabajo técnico (todo entregable nace aquí)
03_REVIEW         hojas y evidencia de la revisión interna
04_AUDIT          auditoría: protocolo, informes y evidencia
05_RELEASED       documentación aprobada internamente (reservada para el flujo por ubicación)
06_DELIVERABLES   documentación emitida al cliente y transmittals
90_MANAGEMENT     gestión visible: estado, cambios, decisiones, trazabilidad, cronograma, lecciones
98_LIBRARY        conocimiento reutilizable: CALCULATIONS, EQUIPMENT, STANDARDS
99_CORE           motor del framework: reglas, comandos, plantillas y módulos (RULES/)
```

- **CORE** lo usa Claude; el usuario normalmente no trabaja allí.
- **MANAGEMENT** lo mantiene Claude y lo revisa y valida el usuario. Lo que Claude genera allí es propuesta hasta que el usuario lo valida.
- `99_CORE/FOLDER_TEMPLATES.md` contiene la tabla «Dónde vive cada archivo» y las plantillas de proyecto A a E.

## Flujo documental

**El estado de un paquete `PQ-nn` es su ubicación física**: `02_ENGINEERING` (único lugar de trabajo) → `03_REVIEW/REVIEW_PACKAGES` → `04_AUDIT/AUDIT_PACKAGES` → `05_RELEASED` → copia rotulada `Rev 00` en `06_DELIVERABLES`. Los scripts de `99_CORE/SCRIPTS/` mueven los paquetes y registran un manifiesto SHA-256 en `90_MANAGEMENT/LEDGER/`. Solo el resultado `APPROVED` avanza; todo paquete modificado vuelve a Ingeniería y el ciclo se reinicia. Detalle en `99_CORE/RULES/M6_states_and_quality.md` (11.2) y `99_CORE/SCRIPTS/README.md`.

## Uso de scripts

- `98_LIBRARY/CALCULATIONS/` contiene los scripts de cálculo y control (`ccpm.py`, `document_verifier.py`, `specification_verifier.py`, `input_converter.py`, `charter_exporter.py`, …). Pruebas: `python3 -B -m unittest discover -s 98_LIBRARY/CALCULATIONS` desde la raíz.
- `99_CORE/SCRIPTS/` contiene los scripts de transición (`SEND_TO_REVIEW.py`, `RETURN_TO_ENGINEERING.py`, `SEND_TO_AUDIT.py`, `APPROVE_AUDIT.py`, `RELEASE_DOCUMENTS.py`, `ISSUE_IFA.py`, `ISSUE_IFC.py`, `ISSUE_ASBUILT.py`, `CONFIRM_SENT.py`, `START_ASBUILT.py`, `CLOSE_PROJECT.py`, `CHECK_STATE.py`). Pruebas: `python3 -B -m unittest discover -s 99_CORE/SCRIPTS` desde la raíz.

## Incorporación de Claude

Claude carga el framework a través de `CLAUDE.md` (raíz), que importa `99_CORE/CLAUDE.md`. Las frases fijas están en `99_CORE/COMMANDS.md` (`ayuda` muestra las del momento). Para arrancar un proyecto: completar `01_INPUT/02_REQUIREMENTS/` con los datos de partida, depositar la documentación en `01_INPUT/99_UNCLASSIFIED/` y decir `iniciar proyecto`.

## Estructura del proyecto

Ver `99_CORE/FOLDER_TEMPLATES.md`. Guía completa para el usuario: `99_CORE/FRAMEWORK_GUIDE.md` (solo en la plantilla maestra).
