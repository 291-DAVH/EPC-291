# 05-management: gestión del proyecto

Datos de gestión del proyecto, escritos y leídos por la plataforma (pestañas **Plan**, **Registros**, **Informes** del proyecto). El cliente no ve esta carpeta: ve los entregables, los datos de entrada, los requisitos y los informes que se le publican.

| Archivo o carpeta | Qué es | Quién lo escribe |
|---|---|---|
| `project-status.json` | fase, avance, salud y hitos | plataforma (Resumen, Plan) |
| `wbs.json`, `schedule.json`, `backlog.json` | EDT, cronograma y backlog | pestaña Plan |
| `deliverables.json` | entregables y su estado | emisión (Ingeniería › Emitir) |
| `registers/<tipo>.json` | riesgos (RIE), cambios (RFC), incidencias (INC), decisiones (DEC), supuestos (SUP), interesados (STK) | pestaña Registros |
| `progress/`, `reports/` | informes de gestión generados (Markdown y PDF) y `reports/generated.json` | pestaña Informes |

Los tipos de registro y de informe los define la metodología del proyecto (`management/methodologies/<id>/registers.json` y `reports.json`). Los registros no se borran: cambian de estado y guardan su historial (quién, qué y cuándo).
