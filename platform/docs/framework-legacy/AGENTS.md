# Catálogo de Agentes del Framework

> Wiki del framework · Solo lectura · Versión 2.0 · 2026-10-14

Los agentes son especialistas que Claude invoca para tareas concretas. Cada uno opera con un rol definido, herramientas limitadas (solo lectura por defecto) e independencia del contexto de la sesión principal.

---

## Cuándo usar un agente

Los agentes se invocan mediante la herramienta `Agent` en las siguientes situaciones:

- La tarea requiere independencia de criterio (revisión, auditoría).
- La tarea es de lectura y análisis, no de escritura.
- Se necesita paralelizar consultas sobre distintas disciplinas.
- El análisis produciría demasiado contexto en la sesión principal.

---

## Catálogo

### Ingeniería de disciplinas

| Agente | Archivo | Disciplinas | Cuándo invocarlo |
|---|---|---|---|
| Senior Electrical Engineer | `senior-electrical-engineer.md` | E | Revisar cálculos eléctricos, verificar SLD/MLD, validar protecciones y cortocircuito |
| Senior Civil Engineer | `senior-civil-engineer.md` | C / S | Revisar cálculos de estructuras, fundaciones, hormigón y acero |
| Senior Mechanical Engineer | `senior-mechanical-engineer.md` | M / TM | Revisar equipos mecánicos, bombas, compresores, intercambiadores |
| Senior HVAC Engineer | `senior-hvac-engineer.md` | H | Revisar cargas térmicas, selección de equipos, ductos |
| Senior Piping & Plumbing Engineer | `senior-piping-plumbing-engineer.md` | PL / P | Revisar redes hidráulicas, P&IDs, selección de materiales |
| Senior Fire Protection Engineer | `senior-fire-protection-engineer.md` | FP / FD | Revisar redes de incendio, detección y alarma |
| Senior Instrumentation & Control Engineer | `senior-instrumentation-control-engineer.md` | I | Revisar hojas de datos de instrumentos, P&IDs, lógica de control |
| Senior Telecommunications Engineer | `senior-telecommunications-engineer.md` | T | Revisar redes de datos, cableado estructurado, CCTV |

### Coordinación técnica y calidad

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Lead Technical Coordinator | `lead-technical-coordinator.md` | Verificar coherencia entre disciplinas internas, revisar interfaces, detectar inconsistencias entre documentos |
| Interface Manager | `interface-manager.md` | Gestionar Battery Limits con entidades externas (otros contratistas, cliente, servicios públicos, organismos regulatorios) |
| QA/QC Engineer | `qa-qc-engineer.md` | Verificar nomenclatura, versionado, formato Pandoc, autocontrol de cierre documental |
| BIM Clash Detection Coordinator | `bim-clash-detection-coordinator.md` | Revisar matrices de interferencias entre disciplinas antes de emitir planos |

### Revisión y auditoría técnica

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Technical Reviewer | `technical-reviewer.md` | Estado `FOR_REVIEW` o `INTERNAL_REVIEW` — revisar paquetes con independencia |
| Technical Auditor | `technical-auditor.md` | Estado `FOR_AUDIT` — auditar emisiones con criterio adversarial |
| Constructability Reviewer | `constructability-reviewer.md` | Analizar diseños en etapas tempranas para identificar problemas de construcción antes de que lleguen a obra |

### Redacción técnica

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Document Writer | `document-writer.md` | Redactar o revisar pliegos técnicos (`PG`), especificaciones (`ET`) y memorias descriptivas (`MD`) para cualquier disciplina |

---

### Datos e Integración

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Catalog Master Normalizer | `catalog-normalizer-agent.md` | Analizar catálogos de fabricantes (ABB, Schneider, Siemens) y transformarlos en JSON maestro estandarizado por categoría de equipo (mccb.json, vfd.json, etc.) |

---

### Procura y Suministros

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Procurement Buyer Agent | `procurement-buyer-agent.md` | Gestionar RFQ, evaluar técnica y comercialmente ofertas, elaborar cuadro comparativo y recomendación de adjudicación |
| Expediting Coordinator | `expediting-coordinator.md` | Monitorear hitos de fabricación en talleres, coordinar logística de transporte y alertar desvíos de entrega |
| Materials Management Agent | `materials-management-agent.md` | Control de inventario en sitio, recepción contra OC con MTR, almacenamiento y preservación de equipos |

---

### Construcción y Campo

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Site Construction Manager | `site-construction-manager.md` | Supervisar avance físico diario, coordinar subcontratistas, resolver interferencias en campo, generar DPR |
| HSE Officer | `hse-officer.md` | Evaluar riesgos laborales (IPERC), revisar permisos de trabajo de alto riesgo, investigar incidentes, auditar seguridad |

---

### PMO — Gestión, Costos y Contratos

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Project Controls Planner | `project-controls-planner.md` | Desarrollar cronograma maestro (CPM), analizar ruta crítica, calcular EVM (SPI/CPI/EAC), generar Lookahead |
| Cost Control Estimator | `cost-control-estimator.md` | Monitorear flujo de caja, controlar desvíos presupuestarios, estimar Change Orders, calcular EAC |
| Contract Claims Manager | `contract-claims-manager.md` | Gestionar reclamos (claims) y disputas contractuales con cliente o subcontratistas, construir respaldo documental |

---

### Comisionamiento y Cierre

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Commissioning Start-Up Engineer | `commissioning-start-up-engineer.md` | Diseñar y ejecutar pre-commissioning (pruebas frío/caliente), gestionar Punch List, coordinar RFSU y start-up |
| Handover Documentation Specialist | `handover-documentation-specialist.md` | Compilar dossier final (As-Built, certificados, MTR, manuales O&M, garantías), gestionar entrega formal al cliente |

---

### Dirección y Coordinación General

| Agente | Archivo | Cuándo invocarlo |
|---|---|---|
| Project Manager | `project-manager.md` | Gestión integral de un subproyecto específico: alcance, cronograma, costo, calidad, riesgos, relación con cliente |
| Program Manager | `program-manager.md` | Coordinar múltiples subproyectos interconectados: recursos compartidos, dependencias, riesgos cruzados, Master Schedule |
| Director of Projects | `director-of-projects.md` | Alinear portfolio de programas EPC con objetivos estratégicos y financieros: flujo de caja, rentabilidad, Go/No-Go |
| Portfolio Manager | `portfolio-manager.md` | Alias del Director de Proyectos (mismo rol, diferente denominación organizacional) |

---

## Agente Document Writer — detalle

**Responsabilidad:** transforma decisiones técnicas ya tomadas en documentación técnica clara, precisa, verificable y exigible contractualmente.

**No es** ingeniero de disciplina — no calcula ni dimensiona. Opera sobre el resultado de los cálculos ya aprobados (`REVIEWED`).

**Capacidades:**
- Redactar capítulos de pliego para cualquier disciplina.
- Aplicar el estilo y estructura de los pliegos aprendidos por el skill `generar-pliego`.
- Ejecutar el autocontrol del pliego (criterios de aceptación, normas, marcas abiertas).
- Revisar pliegos existentes para hallazgos de calidad contractual.

**Invocación directa:** cuando el usuario pide `generar pliego`, la skill `generar-pliego` delega automáticamente al agente Document Writer.

---

## Resumen por fase del ciclo EPC

| Fase | Agentes principales |
|---|---|
| **Datos e Integración** | Catalog Master Normalizer |
| **Ingeniería** | Senior Engineers (disciplinas), Lead Technical Coordinator, Interface Manager, Constructability Reviewer, QA/QC, Technical Reviewer, Technical Auditor, Document Writer, BIM Clash Detection Coordinator |
| **Procura** | Procurement Buyer Agent, Expediting Coordinator, Materials Management Agent |
| **Construcción** | Site Construction Manager, HSE Officer |
| **PMO (transversal)** | Project Controls Planner, Cost Control Estimator, Contract Claims Manager |
| **Comisionamiento y Cierre** | Commissioning Start-Up Engineer, Handover Documentation Specialist |
| **Dirección** | Project Manager, Program Manager, Director of Projects / Portfolio Manager |
