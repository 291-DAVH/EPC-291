---
name: "create-management-document"
description: "Genera artefactos PM² para proyectos (actas, planes, reportes, canvases, logs) según la fase activa del ciclo PM²: Iniciando, Planificación, Ejecución o Cierre."
---

# Skill: create-pm2-document

## Propósito
Genera documentos de gestión de proyectos siguiendo la metodología PM² v3.0 (European Commission CoEPM²). Crea artefactos completos con contenido del proyecto real, listos para usar en `90_MANAGEMENT/` o `02_PROJECT/Management/`.

## Contexto de ejecución
- **Invocación:** explícita — ejecutar solo cuando el usuario pida generar un documento de gestión (acta, plan, reporte, canvas, log).
- **Contexto requerido:** directorio `90_MANAGEMENT` o `02_PROJECT`. No ejecutar en `03_ENGINEERING`, `01_INPUT` ni `04_REVIEW`.
- **No ejecutar si:** el usuario consulta sobre metodología PM²; está leyendo documentos existentes; la conversación es sobre análisis técnico.
- **Señales de activación:** el usuario dice "generar acta", "crear plan", "preparar reporte", "armar canvas de inicio/cierre", "hacer el project charter", o menciona un artefacto PM² explícitamente.

## Plugin de referencia
Usar `.claude/library/plugins/management/plugin.json` v2.0 para identificar el template (`templates[].file`), la fase (`templates[].phase`) y ubicar los canvases HTML.

## Ciclo de vida PM²

```
INICIANDO ──[RfP]──► PLANIFICACIÓN ──[RfE]──► EJECUCIÓN ──[RfC]──► CIERRE
                                   ↕
                        MONITOREO Y CONTROL (continuo)
```

## Artefactos por fase

**INICIANDO** (→ RfP)
- Project Initiation Request, Business Case, Project Charter
- Canvas: `PM2_PM_Initiation_Canvas.html` / `PM2_PgM_Initiation_Canvas.html`

**PLANIFICACIÓN** (→ RfE)
- Project Handbook, Stakeholder Matrix, Work Plan
- Outsourcing/Procurement Plan, Acceptance Plan, Transition Plan, Business Implementation Plan
- Sub-planes (en apéndice del Handbook): Requirements, Change, Risk, Issue, Quality, Communications

**EJECUCIÓN** (→ RfC)
- Meeting Agenda & MoM, Status Report, Progress Report, Change Request, Quality Review Report

**CIERRE** (→ cierre administrativo)
- Canvas: `PM2_PM_End_Canvas.html`
- Project-End Report, Acceptance Note

**MONITOREO Y CONTROL** (continuo)
- Risk Log, Issue Log, Decision Log, Change Log, NCR Log

## Proceso de generación

1. **Identificar** qué artefacto pide el usuario y su fase PM²
2. **Recopilar** información del proyecto desde `01_INPUT/` y `02_PROJECT/`
3. **Seleccionar formato:**
   - Canvas → publicar como Artifact HTML (paleta suave, proporciones A4)
   - Documento → crear `.md` con contenido real y estructura PM²
   - Log → crear tabla `.md` con columnas PM² estándar
4. **Destino:**
   - Gestión → `90_MANAGEMENT/`
   - Planes técnicos → `02_PROJECT/Management/`
   - Canvases → Artifact + HTML en `90_MANAGEMENT/Canvases/`
5. **Confirmar** si hay datos clave faltantes antes de generar

## Convenciones de nombres
```
YYYY-MM-DD_[PROYECTO-ID]_[TIPO-ARTEFACTO]_v[N].md
```

## Estructura por tipo

### Documento MD (planes, actas, reportes)
```markdown
# [Tipo de Artefacto]
**Proyecto:** | **ID:** | **Versión:** | **Fecha:**
**Preparado por:** | **Aprobado por:**
---
[Secciones según estructura PM²]
```

### Log (Risk, Issue, Decision, Change, NCR)
| ID | Fecha | Descripción | Probabilidad/Impacto | Responsable | Estado | Acción |

## Governance Roles PM²
- **AGB** — Appropriate Governance Body
- **PSC** — Project Steering Committee
- **PO** — Project Owner | **SP** — Solution Provider
- **BM** — Business Manager | **PM** — Project Manager
- **BIG** — Business Implementation Group
- **PCT** — Project Core Team | **PST** — Project Support Team

## Integración con el framework
Este skill complementa las plantillas de gestión de `management-templates.md` (módulo M8) y los documentos D01-D28. Para documentos del framework (actas, informes, puertas), preferir las plantillas de M8; para artefactos PM² puros (canvases, planes de gestión detallados), usar este skill.
