# 90_MANAGEMENT — Gestión del proyecto

Contiene los documentos vivos de la gestión del proyecto. **Todos son editables por el usuario**, salvo los bloques marcados «GUÍA DEL ARCHIVO (no editar)» que son instrucciones de cabecera.

## Archivos en la raíz

| Archivo | Quién lo llena | Cuándo |
|---|---|---|
| `PROJECT_SCOPE.md` | Project Engineer (con Claude) | Inicio del proyecto |
| `PROJECT_CHARTER.md` | Project Engineer (con Claude) | Inicio del proyecto |
| `PROJECT_CHARTER_EXECUTIVE.md` | Project Engineer (con Claude) | Inicio del proyecto |
| `GOALS.md` | Project Engineer (con Claude) | Inicio del proyecto |
| `PROJECT_INFORMATION.md` | Project Engineer (con Claude) | Inicio y durante el proyecto |
| `CLIENT_REQUIREMENTS.md` | Project Engineer (con Claude) | Al recibir requisitos del cliente |
| `ENGINEERING_STANDARDS.md` | Project Engineer (con Claude) | Inicio del proyecto |
| `PROJECT_STATUS.md` | Project Engineer / Claude | Al terminar cada sesión y al cambiar de estado |
| `AUDIT_REGISTER.md` | Auditor / Project Engineer | Por cada auditoría e informe de avance |
| `CHANGE_REQUESTS.md` | Project Engineer | Por cada RFC abierta |
| `ASSUMPTIONS_AND_DECISIONS.md` | Project Engineer | Por cada decisión técnica relevante |
| `TRACEABILITY_MATRIX.md` | Project Engineer (con Claude) | Actualización continua |
| `DELIVERABLES.md` | Project Engineer (con Claude) | Inicio y actualización por fase |
| `DRAWING_STATUS.md` | Project Engineer | Por cada cambio de estado de plano |
| `LESSONS_LEARNED.md` | Todo el equipo | Durante el proyecto |
| `SCHEDULE_CCPM.md` | Project Engineer (con Claude) | Solo en modo «Ingeniería + gestión» |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `CHARTER/` | Charter PDF/Word generados por `charter_exporter.py` y `canvas_exporter.py` |
| `GOVERNANCE/` | Planes de gestión (RISK_PLAN, QUALITY_HSE_PLAN, PROJECT_HANDBOOK) |
| `PROGRESS/` | Informes de avance (`PROGRESS-nn`) |
| `REPORTS/` | Punch list, close checklist, redline log |
