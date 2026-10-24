# Módulo M8 — Documentos y puertas de gestión

Autoridad: la misma que `CLAUDE.md`. Complementa 4.2, 8.2 y 11. Claude lo lee cuando el usuario pide un informe, registra una incidencia, una reunión, una consulta de obra, una aceptación, o cuando se aproxima una puerta (gate).

## 1. Modo de gestión

Los modos son los dos de `starting-data.md` (sección 7); no se agrega un tercero, para no alterar `ccpm.py` ni el charter:

- **Solo ingeniería y trazabilidad documental (por defecto):** gestión mínima, es decir hitos, horas por paquete y semáforo. Se usan `ISSUE_LOG`, `EFFORT_BASELINE`, `STATUS-nn`, `DASHBOARD` y las actas (`MTG`, `GATE`, `ACC`). Sin cronograma CCPM.
- **Ingeniería + gestión del proyecto:** además el cronograma CCPM, los planes de `Governance/` completos y los informes D12 a D15.

Los archivos de `Governance/` existen en ambos modos; en el modo por defecto solo se completa lo que el proyecto necesita y el resto se marca «no aplica» con motivo.

## 2. Catálogo (D01 a D28)

> En esta plataforma los registros (riesgos, cambios, incidencias, decisiones, supuestos e interesados) son datos del proyecto, definidos por `registers.json` de la metodología y gestionados en la pestaña *Registros*; los informes D11 a D15 se definen en `reports.json` y se generan en la pestaña *Informes*. Las rutas de la tabla son relativas a `workspace/05-management/`.

| ID | Documento | Ubicación | Disparador |
|---|---|---|---|
| D01 | Manual del proyecto | `Governance/project-handbook.md` | `aprobar charter` |
| D02 | Interesados | pestaña Registros › Interesados | `aprobar charter` |
| D03 | Plan de comunicaciones | `Governance/Communications/comm-plan.md` | `aprobar charter` |
| D04 | Plan de riesgos | `Governance/risk-plan.md` | `aprobar charter` |
| D05 | Plan de calidad y HSE | `Governance/Quality_and_HSE/quality-hse-plan.md` | `aprobar charter` |
| D06 | Plan de adquisiciones | `Governance/procurement-plan.md` | `aprobar charter` |
| D07 | Plan de aceptación y transición | `Governance/acceptance-transition-plan.md` | `aprobar charter` |
| D08 | Línea base de esfuerzo | `Planning/effort-baseline.md` | `aprobar plan de paquetes` |
| D09 | Registro único de incidencias | pestaña Registros › Incidencias | `registrar incidencia` |
| D10 | Acta de reunión | `Meetings/MTG-nnn_AAAAMMDD.md` | `registrar reunión` |
| D11 | Informe de estado | `progress/STATUS-nn_AAAAMMDD` (md y pdf) | pestaña Informes |
| D12 | Informe de avance | `progress/progress-nn_AAAAMMDD` (md y pdf) | pestaña Informes |
| D13 | Informe de riesgos | `reports/RISKS-nn_AAAAMMDD` (md y pdf) | pestaña Informes |
| D14 | Informe de esfuerzo | `reports/EFFORT-nn_AAAAMMDD` (md y pdf) | pestaña Informes |
| D15 | Informe de cambios | `reports/CHANGES-nn_AAAAMMDD` (md y pdf) | pestaña Informes |
| D16 | Registro de no conformidades | `Governance/Quality_and_HSE/ncr-log.md` | `registrar incidencia` (NCR) |
| D17 | Acta de puerta | `Reports/GATE-nn_<fase>.md` | `cerrar fase`, `aprobar inicio` |
| D18 | Tablero | `Reports/DASHBOARD.md` | `tablero` |
| D19 | Acta de aceptación | `06-deliverables/transmittals/ACC-nnn.md` | `aceptación firmada` |
| D20 | Revisión del cliente | `Reports/CLIENT_REVIEW-nn.md` | `comentarios del cliente recibidos` |
| D21 | Consultas de obra | `Governance/Communications/rfi/site-rfi-log.md` | `registrar consulta de obra` |
| D22 | Visita a obra | `Reports/SITE_VISIT-nn_AAAAMMDD.md` | `registrar visita de obra` |
| D23 | Marcas de obra (redline) | `Reports/redline-log.md` | durante obra |
| D24 | Lista de pendientes | `Reports/punch-list.md` | `COMMISSIONING` |
| D25 | Informe final | `Reports/PROJECT_END_REPORT.md` | `generar informe de cierre` |
| D26 | Lienzo final | `Reports/PROJECT_END_CANVAS.md` | `generar informe de cierre` |
| D27 | Lista de cierre | `Reports/close-checklist.md` | `generar informe de cierre` |
| D28 | Informe de lecciones | `Historical/Lessons/lessons_REPORT.md` | `extraer lecciones` |

Las rutas de `90-management` omiten ese prefijo cuando no empiezan con `07_`. Las plantillas de D10 a D15, D17 a D20, D22, D25, D26 y D28 están en `.claude/rules/management-templates.md`.

## 3. Puertas (gates)

| Puerta | Cuándo | Frase | Criterios mínimos |
|---|---|---|---|
| Listo para ejecutar | Antes del primer `desarrollar paquete` | `aprobar inicio` ● | **Solo ingeniería:** charter aprobado; plan de paquetes aprobado; `EFFORT_BASELINE` completa; riesgos `RIE-nnn` con respuesta si los hay; `ISSUE_LOG` sin bloqueos. **Ingeniería + gestión:** además `RISK_PLAN`, `COMM_PLAN` y `STAKEHOLDERS` completos. |
| Fin de fase | Al `cliente aprueba` de cada fase (IC / IB / ID / IE) | `cerrar fase` ● | Entregas de la fase aprobadas por el cliente; comentarios cerrados; `CHANGES` al día; lecciones de la fase capturadas |
| Listo para cerrar | Antes de `cerrar proyecto` | `cerrar proyecto` ● | `CLOSE_CHECKLIST` completa; `ACC` firmada; `PUNCH_LIST` cerrada; lecciones extraídas |

Cada puerta produce un `GATE-nn` y una `DEC-nnn`.

## 4. Reglas de gestión

1. **Riesgos.** Escalas de 1 a 5; nivel = probabilidad × impacto; verde ≤ 2, amarillo 3 a 16, rojo ≥ 20. Estrategias: evitar, reducir, aceptar, transferir. Cadencia: revisar en cada informe de estado y antes de cada puerta. Un riesgo rojo sin respuesta bloquea la puerta.
2. **Incidencias.** Un solo registro (`ISSUE_LOG`). Los prefijos históricos `BLQ`, `PND`, `INF`, `PA` se conservan como tipo. Todo asunto tiene responsable y fecha.
3. **Respuesta del cliente.** Cada `INF` y cada envío con respuesta esperada tiene plazo (`COMM_PLAN`); vencido, aparece en `estado del proyecto`.
4. **Esfuerzo.** Las horas reales por paquete se anotan al cerrarlo y se comparan con `EFFORT_BASELINE`. Desvío mayor al 20 % pide causa en el informe de esfuerzo.
5. **Lecciones.** Al iniciar el proyecto y al comenzar cada fase, Claude lee `lessons_EXTRACTED_*` de `02-engineering/ARCHIVE` y las fichas del cliente, y declara cuáles aplica.
6. **Revisión liviana y completa.** Un paquete de bajo riesgo (sin cálculo ni seguridad) puede usar la hoja de revisión liviana: lista corta de verificación y una respuesta global. Un paquete con cálculo, seguridad o cambio de alcance usa la hoja completa. Claude propone cuál y el usuario confirma.
7. **Trazabilidad.** Ningún documento de este módulo borra información: cierra con evidencia o se reemplaza por una emisión nueva.

## 5. Ajustes de flujo pendientes de script

Estos ajustes están definidos pero **aún no los aplican los scripts** (`workflow.py`, `check-state.py`); hasta entonces rigen las reglas actuales de `CLAUDE.md` 11:

- Un paquete en elaboración mientras otro está en revisión (`workflow.py` hoy permite uno solo en `FOR_REVIEW`).
- Avance con `APPROVED_WITH_comments` documental tras una hoja delta corta.
- Estado del proyecto en una línea: fase + emisión + próxima puerta.
- Fechas reales del `ledger` en `ccpm.py`; borrador automático de avance; tablero generado por script.
- Aviso de desvío de versión del motor `.claude` en `CHECK_STATE`.


## 6. Escalada a Programa

Cuando un conjunto de proyectos debe gestionarse de forma coordinada para obtener beneficios transversales, el proyecto puede escalar a **Programa**. Ver `.claude/rules/m10-programme-management.md` para:
- Criterios de escalada Proyecto → Programa.
- Comandos `escalar a programa` ● y `disolver programa` ●.
- Catálogo de documentos de programa (PC, PMP, PROAD, PBEN, PGSTATUS).
- Estructura de carpetas bajo `90-management/PROGRAMME/` y `90-management/PROJECTS/`.

M8 sigue vigente sin cambios para cada proyecto constituyente; M10 aplica al nivel del programa.
