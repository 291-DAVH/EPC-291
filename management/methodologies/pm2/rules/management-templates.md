# management-templates.md

> **Propósito:** Plantillas operativas para los documentos D10–D28 del catálogo M8.
> **Uso:** base de cada documento; la plataforma las aplica a D11 a D15 y la skill `create-management-document` al resto.
> **Ubicación de salida:** `workspace/05-management/` del proyecto (ver ruta exacta en cada sección). Los informes D11 a D15 los genera la plataforma; el resto se redacta con la skill `create-management-document`.
> **Confidencialidad:** Los campos de costo, presupuesto, honorarios y condiciones comerciales son confidenciales y **nunca se completan** a partir de datos reales en estos archivos.
> **Licencia base:** Adaptado de PM² v3.1 (CC BY 4.0 — European Commission).

---

## Índice

| D-Código | Nombre | Comando |
|----------|--------|---------|
| [D10](#d10) | Acta de Reunión | `generar acta de reunión` |
| [D11](#d11) | Informe de Estado | pestaña *Informes* |
| [D12](#d12) | Informe de Avance | pestaña *Informes* |
| [D13](#d13) | Informe de Riesgos | pestaña *Informes* |
| [D14](#d14) | Informe de Esfuerzo | pestaña *Informes* |
| [D15](#d15) | Informe de Cambios | pestaña *Informes* |
| [D17](#d17) | Acta de Puerta de Fase | `generar acta de puerta [fase]` |
| [D18](#d18) | Tablero del Proyecto | `actualizar tablero` |
| [D19](#d19) | Acta de Aceptación | `generar acta de aceptación` |
| [D20](#d20) | Revisión del Cliente | `generar revisión del cliente` |
| [D22](#d22) | Informe de Visita a Obra | `generar informe visita a obra` |
| [D25](#d25) | Informe Final del Proyecto | `generar informe final` |
| [D26](#d26) | Lienzo Final del Proyecto | `generar lienzo final` |
| [D28](#d28) | Informe de Lecciones Aprendidas | `generar informe de lecciones` |
| [CANVAS-I](#canvas-i) | Lienzo de Inicio del Proyecto | `generar lienzo de inicio` |

---

## D10 — Acta de Reunión {#d10}

> **Comando:** `generar acta de reunión`
> **Archivo:** `90-management/progress/MTG-nnn_AAAAMMDD.md`
> **Fuente PM²:** Minutes of Meeting (Artefacts v3.1, p.189-190)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Título de reunión:** [TÍTULO]
**Tipo:** [Kickoff / Progreso / Técnica / Revisión Cliente / Coordinación / Extraordinaria]
**Fecha:** [DD/MM/AAAA]
**Hora:** [HH:MM – HH:MM]
**Lugar / Plataforma:** [Oficina / Teams / Zoom / Obra]
**Coordinador:** [NOMBRE]
**Acta elaborada por:** [NOMBRE / ROL]
**Fecha de emisión:** [DD/MM/AAAA]

### Participantes

| Nombre | Empresa / Rol | Iniciales | Asistió |
|--------|-------------|-----------|---------|
| | | | Sí / No |
| | | | |

### Agenda

| N° | Tema | Responsable | Duración (min) |
|----|------|-------------|----------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |

### Resumen de la reunión

[Narrativa de los puntos tratados, acuerdos generales y contexto relevante.]

### Decisiones tomadas

| ID | Descripción | Fecha | Responsable | Comunicar a |
|----|-------------|-------|-------------|-------------|
| DEC-nnn | | DD/MM/AAAA | | |

> Las decisiones se trasladan a `assumptions-and-decisions.md` como `DEC-nnn`.

### Acciones y compromisos

| ID | Fecha creación | Descripción | Responsable | Fecha límite | Estado |
|----|---------------|-------------|------------|-------------|--------|
| AC-001 | | | | | ABIERTO |
| AC-002 | | | | | |

### Próxima reunión (si aplica)

**Fecha:** [DD/MM/AAAA]
**Lugar:** [lugar]
**Agenda propuesta:**
1. [Punto 1]
2. [Punto 2]

### Documentos relacionados

| Documento | Código / Revisión | Ubicación |
|-----------|------------------|-----------|
| | | |

---

## D11 — Informe de Estado {#d11}

> **Generación:** pestaña *Informes* del proyecto (o `POST /api/projects/{id}/reporting`); la plataforma lo completa con los datos del proyecto
> **Archivo:** `workspace/05-management/progress/STATUS-nn_AAAAMMDD.md` y `.pdf`
> **Fuente PM²:** Project Status Report — formato compacto (Artefacts v3.1, p.191-192)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Fase actual:** [Inicio / Planificación / Ejecución / Cierre]
**Período reportado:** [DD/MM/AAAA – DD/MM/AAAA]
**N° Informe:** nn
**Elaborado por:** [PM / NOMBRE]
**Fecha:** [DD/MM/AAAA]

### Estado general

| Dimensión | Estado | Tendencia | Comentario breve |
|-----------|--------|-----------|-----------------|
| **Alcance** | VERDE / AMARILLO / ROJO | ↑ / → / ↓ | |
| **Cronograma** | | | |
| **Calidad** | | | |
| **Riesgos** | | | |
| **Cambios** | | | |

**Estado general del proyecto:** VERDE / AMARILLO / ROJO

**Resumen ejecutivo:**
[2–3 oraciones sobre el estado global del proyecto en el período.]

### Indicadores de desempeño

| Indicador | Planificado | Real | Variación |
|-----------|------------|------|-----------|
| Avance físico global (%) | % | % | % |
| Avance cronograma (%) | % | % | % |
| Hitos completados / total | n / N | n / N | |

### Actividades del período

**Realizadas:**
- [Actividad 1]
- [Actividad 2]

**Planificadas para el próximo período:**
- [Actividad 1]
- [Actividad 2]

### Hitos

| Hito | Fecha línea base | Fecha real / proyectada | Estado |
|------|-----------------|------------------------|--------|
| | DD/MM/AAAA | DD/MM/AAAA | Completado / En plazo / Con retraso |

### Cambios activos (del registro de cambios)

| rfc-nnn | Descripción breve | Estado |
|---------|-------------------|--------|
| | | ABIERTO / EVALUADO / APROBADO |

### Riesgos activos relevantes

| RIS-nnn | Descripción breve | Nivel | Acción en curso |
|---------|------------------|-------|----------------|
| | | ALTO / MEDIO | |

### Problemas / Incidencias

| Descripción | Impacto | Acción | Responsable |
|-------------|---------|--------|-------------|
| | | | |

### Decisiones requeridas

| Tema | Decisor | Fecha límite |
|------|---------|-------------|
| | | |

---

## D12 — Informe de Avance {#d12}

> **Generación:** pestaña *Informes* del proyecto (o `POST /api/projects/{id}/reporting`); la plataforma lo completa con los datos del proyecto
> **Archivo:** `workspace/05-management/progress/progress-nn_AAAAMMDD.md` y `.pdf`
> **Fuente PM²:** Project Progress Report (Artefacts v3.1, p.194-196)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Período:** [DD/MM/AAAA – DD/MM/AAAA]
**N° Informe:** nn
**Elaborado por:** [PM / NOMBRE]
**Revisado por:** [NOMBRE / ROL]
**Fecha:** [DD/MM/AAAA]

---

## 1. Resumen Ejecutivo

[Síntesis del estado del proyecto, incluyendo estado general (VERDE/AMARILLO/ROJO), avance respecto a la línea base, cambios significativos del período y próximas acciones críticas. Máximo 1 página.]

## 2. Interesados Clave

| Nombre | Rol | Organización | Nivel de involucramiento |
|--------|-----|-------------|------------------------|
| | Project Owner | | Alto |
| | Project Manager | | Alto |
| | [Cliente] | | |

## 3. Hitos y Entregables

| Hito / Entregable | Fecha línea base | Fecha real / pronóstico | Estado |
|-------------------|-----------------|------------------------|--------|
| [Hito 1] | DD/MM/AAAA | DD/MM/AAAA | Completado / En plazo / Con retraso |

## 4. Plan de Trabajo por Paquete

| Paquete de trabajo | Responsable | Avance (%) | Estado | Observaciones |
|-------------------|------------|-----------|--------|---------------|
| | | | | |

## 5. Cambios de Alcance

Ver el registro completo de cambios (pestaña *Registros*).

| rfc-nnn | Título | Estado | Impacto en entregables |
|---------|--------|--------|----------------------|
| | | | |

**Cambios aprobados acumulados:** [n rfc aprobados]

## 6. Riesgos Principales y Acciones

| RIS-nnn | Descripción | Nivel | Acción | Responsable | Fecha |
|---------|-------------|-------|--------|-------------|-------|
| | | ALTO / MEDIO | | | |

## 7. Problemas Principales y Acciones

| Problema | Impacto | Acción | Responsable | Estado |
|---------|---------|--------|-------------|--------|
| | | | | |

## 8. Otras Acciones en Curso / Planificadas

| Acción | Responsable | Estado | Fecha límite |
|--------|-------------|--------|-------------|
| | | | |

## 9. Logros del Período

- [Logro 1]
- [Logro 2]

## Apéndice: Documentos Relacionados

| Documento | Versión / Rev. | Ubicación |
|-----------|---------------|-----------|
| registers/change.json | — | workspace/05-management/ |
| registers/risk.json | — | workspace/05-management/ |

---

## D13 — Informe de Riesgos {#d13}

> **Generación:** pestaña *Informes* del proyecto (o `POST /api/projects/{id}/reporting`); la plataforma lo completa con los datos del proyecto
> **Archivo:** `workspace/05-management/reports/RISKS-nn_AAAAMMDD.md` y `.pdf`

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Período:** [DD/MM/AAAA – DD/MM/AAAA]
**N° Informe:** nn
**Elaborado por:** [PM / NOMBRE]
**Fecha:** [DD/MM/AAAA]

### Resumen del Registro de Riesgos

| Categoría | Alto (Crítico) | Medio | Bajo | Total activos |
|-----------|--------------|-------|------|--------------|
| Técnico | | | | |
| Cronograma | | | | |
| Externo / Cliente | | | | |
| Organizacional | | | | |
| **Total** | | | | |

### Riesgos Activos de Nivel Alto

| RIS-nnn | Descripción | Prob. | Impacto | Nivel | Estrategia | Responsable | Estado |
|---------|-------------|-------|---------|-------|-----------|------------|--------|
| | | Alto/Med/Bajo | Alto/Med/Bajo | ALTO | Mitigar/Transferir/Aceptar | | ABIERTO |

### Riesgos de Nivel Medio Activos

| RIS-nnn | Descripción | Prob. | Impacto | Estrategia | Responsable |
|---------|-------------|-------|---------|-----------|------------|
| | | | | | |

### Riesgos Nuevos en el Período

| RIS-nnn | Descripción | Prob. | Impacto | Nivel | Estrategia asignada |
|---------|-------------|-------|---------|-------|-------------------|
| | | | | | |

### Riesgos Cerrados en el Período

| RIS-nnn | Descripción | Motivo de cierre | Fecha cierre |
|---------|-------------|-----------------|-------------|
| | | Materializado / Evitado / Expirado | |

### Evolución del Perfil de Riesgo

| Período anterior | Período actual | Tendencia |
|-----------------|---------------|-----------|
| Riesgos altos: n | Riesgos altos: n | ↑ / → / ↓ |

### Conclusiones y Acciones Recomendadas

- [Conclusión / acción 1]
- [Conclusión / acción 2]

> **Fuente:** registro de riesgos del proyecto (pestaña *Registros*)

---

## D14 — Informe de Esfuerzo {#d14}

> **Generación:** pestaña *Informes* del proyecto (o `POST /api/projects/{id}/reporting`); la plataforma lo completa con los datos del proyecto
> **Archivo:** `workspace/05-management/reports/EFFORT-nn_AAAAMMDD.md` y `.pdf`

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Período acumulado:** [DD/MM/AAAA – DD/MM/AAAA]
**N° Informe:** nn
**Elaborado por:** [PM / NOMBRE]
**Fecha:** [DD/MM/AAAA]

### Esfuerzo Acumulado por Disciplina

| Disciplina / Rol | HH Línea base | HH Acumuladas | Desviación | % Avance reportado |
|-----------------|--------------|--------------|-----------|-------------------|
| | | | | |
| **TOTAL** | | | | |

> Los valores de HH planificadas corresponden al plan aprobado. No incluir tarifas ni costos.

### Esfuerzo del Período por Paquete de Trabajo

| Paquete de trabajo | HH Plan período | HH Reales período | Var. | Estado |
|-------------------|----------------|-----------------|------|--------|
| | | | | |

### Proyección de Esfuerzo Remanente

| Disciplina | HH Realizadas | HH Remanentes estimadas | HH Total proyectadas |
|-----------|--------------|------------------------|---------------------|
| | | | |

### Observaciones y Alertas

- [Observación sobre desviaciones significativas.]
- [Riesgos de esfuerzo identificados.]

---

## D15 — Informe de Cambios {#d15}

> **Generación:** pestaña *Informes* del proyecto (o `POST /api/projects/{id}/reporting`); la plataforma lo completa con los datos del proyecto
> **Archivo:** `workspace/05-management/reports/CHANGES-nn_AAAAMMDD.md` y `.pdf`
> **Fuente PM²:** Change Log (Artefacts v3.1, p.206)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Período:** [DD/MM/AAAA – DD/MM/AAAA]
**N° Informe:** nn
**Elaborado por:** [PM / NOMBRE]
**Fecha:** [DD/MM/AAAA]

### Resumen del Período

| Estado rfc | Cantidad en período | Acumulado total |
|-----------|--------------------|-----------------:|
| ABIERTOS (nuevos) | | |
| EVALUADOS | | |
| APROBADOS | | |
| RECHAZADOS | | |
| DIFERIDOS | | |
| IMPLEMENTADOS | | |
| CERRADOS | | |
| **TOTAL ACTIVOS** | | |

### Cambios Aprobados en el Período

| rfc-nnn | Título | Categoría | DEC-nnn | Impacto alcance | Impacto cronograma | Responsable |
|---------|--------|-----------|---------|----------------|-------------------|-------------|
| | | Alcance / Diseño / Normativa / Cliente | | | | |

### Cambios Rechazados o Diferidos en el Período

| rfc-nnn | Título | Decisión | DEC-nnn | Justificación |
|---------|--------|---------|---------|--------------|
| | | RECHAZADO / DIFERIDO | | |

### Cambios en Proceso de Evaluación

| rfc-nnn | Título | Fecha apertura | Evaluador | Fecha límite decisión |
|---------|--------|---------------|---------|----------------------|
| | | | | |

### Impacto Acumulado de Cambios Aprobados sobre la Línea Base

| Dimensión | Línea base original | Cambios aprobados | Estado actual |
|-----------|--------------------|--------------------|--------------|
| Alcance (descripción) | | +n cambios aprobados | |
| Cronograma (variación) | Fecha original | Δ semanas | Nueva fecha proyectada |
| Documentos afectados | — | n documentos | Ver propagación en rfc |

### Conclusiones

- [Conclusión 1]
- [Conclusión 2]

> **Fuente:** registro de cambios del proyecto (pestaña *Registros*)
> Cada cambio resuelto tiene su `DEC-nnn` en el registro de decisiones (pestaña *Registros*).

---

## D17 — Acta de Puerta de Fase {#d17}

> **Comando:** `generar acta de puerta [fase]`
> **Archivo:** `90-management/progress/GATE-nn_[FASE].md`
> **Fases válidas:** Inicio / Planificacion / Ejecucion / Cierre
> **Fuente PM²:** Phase-Exit Review Checklist (Artefacts v3.1, p.207-211)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Fase que se cierra:** [FASE]
**Fase siguiente:** [FASE SIGUIENTE]
**Fecha de revisión:** [DD/MM/AAAA]
**Revisor / Rol:** [NOMBRE / ROL]
**Elaborado por:** [PM]

### Resumen de Cumplimiento por Fase

| Fase | % Cumplimiento | Estado | Fecha revisión | Revisada previamente |
|------|---------------|--------|---------------|---------------------|
| Inicio | % | VERDE/AMARILLO/ROJO | DD/MM/AAAA | Sí / No |
| Planificación | % | | | |
| Ejecución | % | | | |
| Cierre | % | | | |

**Leyenda:** ROJO < 50% · AMARILLO 51–80% · VERDE > 80%

**Cumplimiento global:** % | Estado: VERDE / AMARILLO / ROJO

---

### Lista de Verificación — Fase de Inicio

| N° | Criterio | Respuesta | Puntuación | Comentario |
|----|---------|-----------|-----------|------------|
| 1 | ¿Existe un documento de Solicitud de Inicio aprobado? | Sí/No | 0 | |
| 2 | ¿Están documentados el contexto, alcance, entregables y resultados esperados? | Sí/No | | |
| 3 | ¿Se ha identificado el Project Owner? | Sí/No | | |
| 4 | ¿Están documentados los beneficios y criterios de éxito? | Sí/No | | |
| 5 | ¿Se han identificado todos los interesados clave? | Sí/No | | |
| 6 | ¿Están definidos los roles y responsabilidades iniciales? | Sí/No | | |
| 7 | ¿Se ha establecido el comité directivo del proyecto? | Sí/No | | |
| 8 | ¿Se han analizado supuestos, restricciones y riesgos iniciales? | Sí/No | | |
| 9 | ¿Se ha aprobado el Charter del Proyecto por el Project Owner? | Sí/No | | |
| 10 | ¿El proyecto está entregando conforme al cronograma en esta fase? | Sí/No | | |
| 11 | ¿Está el proyecto listo para avanzar a la Fase de Planificación? | Sí/No | | |

---

### Lista de Verificación — Fase de Planificación

| N° | Criterio | Respuesta | Puntuación | Comentario |
|----|---------|-----------|-----------|------------|
| 1 | ¿La matriz de interesados está completa con nombres y datos de contacto? | Sí/No | 0 | |
| 2 | ¿Están definidos todos los roles y responsabilidades del proyecto? | Sí/No | | |
| 3 | ¿Se ha descompuesto el alcance en paquetes de trabajo manejables (WBS)? | Sí/No | | |
| 4 | ¿Están todas las actividades asignadas a responsables? | Sí/No | | |
| 5 | ¿Se han validado el esfuerzo y la duración con los responsables de disciplina? | Sí/No | | |
| 6 | ¿Están todos los paquetes de trabajo programados? | Sí/No | | |
| 7 | ¿Se ha identificado la ruta crítica? | Sí/No | | |
| 8 | ¿Están definidos los indicadores y métricas de desempeño? | Sí/No | | |
| 9 | ¿El Plan del Proyecto está aprobado (línea base)? | Sí/No | | |
| 10 | ¿Está definido y documentado el enfoque de gestión de riesgos? | Sí/No | | |
| 11 | ¿Existe un Registro de Riesgos con estrategias de respuesta aprobadas? | Sí/No | | |
| 12 | ¿Existe un Registro de Supuestos y Decisiones activo? | Sí/No | | |
| 13 | ¿Se ha documentado y aprobado un Plan de Calidad y HSE? | Sí/No | | |
| 14 | ¿Se han definido los criterios de aceptación de entregables? | Sí/No | | |
| 15 | ¿Existe un Plan de Adquisiciones documentado (si aplica)? | Sí/No | | |
| 16 | ¿Se ha aprobado el Project Handbook? | Sí/No | | |
| 17 | ¿Están todos los planes del proyecto aprobados? | Sí/No | | |
| 18 | ¿El proyecto está listo para avanzar a la Fase de Ejecución? | Sí/No | | |

---

### Lista de Verificación — Fase de Ejecución

| N° | Criterio | Respuesta | Puntuación | Comentario |
|----|---------|-----------|-----------|------------|
| 1 | ¿Están disponibles los recursos para completar actividades y transferir entregables? | Sí/No | 0 | |
| 2 | ¿Se han ejecutado las actividades conforme al Plan del Proyecto? | Sí/No | | |
| 3 | ¿Se han producido, actualizado y revisado todos los artefactos planificados? | Sí/No | | |
| 4 | ¿Se han verificado y controlado los entregables según el plan de calidad? | Sí/No | | |
| 5 | ¿Los entregables han sido revisados y aprobados? | Sí/No | | |
| 6 | ¿Se han implementado todos los cambios aprobados? | Sí/No | | |
| 7 | ¿Están todos los riesgos críticos mitigados o cerrados? | Sí/No | | |
| 8 | ¿Están todos los problemas/incidencias del proyecto resueltos o cerrados? | Sí/No | | |
| 9 | ¿Han sido todos los entregables provisoriamente aprobados por el Project Owner? | Sí/No | | |
| 10 | ¿Se han realizado las actividades de transición planificadas? | Sí/No | | |
| 11 | ¿Se ha realizado la capacitación requerida? | Sí/No | | |
| 12 | ¿Están los entregables plenamente operacionales? | Sí/No | | |
| 13 | ¿Se ha comunicado la transferencia de responsabilidades a todos los interesados? | Sí/No | | |
| 14 | ¿Se ha realizado la transferencia formal al equipo de operaciones / cliente? | Sí/No | | |
| 15 | ¿El proyecto está listo para avanzar a la Fase de Cierre? | Sí/No | | |

---

### Lista de Verificación — Fase de Cierre

| N° | Criterio | Respuesta | Puntuación | Comentario |
|----|---------|-----------|-----------|------------|
| 1 | ¿Se realizó la reunión de cierre del proyecto? | Sí/No | 0 | |
| 2 | ¿Se evaluaron los indicadores finales de desempeño vs. la línea base? | Sí/No | | |
| 3 | ¿Se han evaluado los beneficios del proyecto y las metas no alcanzadas? | Sí/No | | |
| 4 | ¿Se evaluó la satisfacción del cliente / stakeholders? | Sí/No | | |
| 5 | ¿Se han asignado las acciones de seguimiento post-proyecto? | Sí/No | | |
| 6 | ¿Se han documentado las lecciones aprendidas? | Sí/No | | |
| 7 | ¿Se han realizado todas las actividades de hand-over al cliente/operaciones? | Sí/No | | |
| 8 | ¿Está el soporte y mantenimiento activo según lo planificado? | Sí/No | | |
| 9 | ¿Todos los interesados relevantes dieron retroalimentación del proyecto? | Sí/No | | |
| 10 | ¿Se ha elaborado y distribuido el Informe Final del Proyecto (D25)? | Sí/No | | |
| 11 | ¿Están todos los entregables y artefactos archivados en el repositorio del proyecto? | Sí/No | | |
| 12 | ¿Se han completado todos los procedimientos de gestión de configuración? | Sí/No | | |
| 13 | ¿Fue el proyecto formalmente aceptado por el Project Owner / Cliente? | Sí/No | | |
| 14 | ¿Se ha liberado formalmente al equipo del proyecto? | Sí/No | | |
| 15 | ¿El proyecto está listo para ser cerrado? | Sí/No | | |

---

### Decisión de Puerta

**Resultado:** APROBADO / APROBADO CON CONDICIONES / RECHAZADO — REQUIERE REVISIÓN

**Condiciones (si resultado es Condicionado):**
- [Condición 1 — responsable — fecha límite]
- [Condición 2]

**Firmantes:**

| Nombre | Rol | Firma | Fecha |
|--------|-----|-------|-------|
| | Project Owner | | DD/MM/AAAA |
| | Project Manager | | |
| | [Cliente / Representante] | | |

> La decisión de puerta genera `DEC-nnn` en `assumptions-and-decisions.md`.

---

## D18 — Tablero del Proyecto {#d18}

> **Comando:** `actualizar tablero`
> **Archivo:** `90-management/DASHBOARD.md`
> *(Documento permanente — se actualiza en cada período, no se crea uno nuevo)*

---

**Proyecto:** [NOMBRE DEL PROYECTO] | **Código:** [CÓDIGO]
**Fase:** [FASE ACTUAL] | **Última actualización:** [DD/MM/AAAA] | **PM:** [NOMBRE]

---

### Estado General

| Dimensión | Estado | Tendencia | Comentario |
|-----------|--------|-----------|------------|
| **Alcance** | VERDE/AMARILLO/ROJO | ↑/→/↓ | |
| **Cronograma** | | | |
| **Calidad** | | | |
| **Riesgos** | | | |
| **Cambios** | | | |
| **GLOBAL** | | | |

### Avance del Proyecto

| Métrica | Planificado | Real | Δ |
|---------|------------|------|---|
| Avance global (%) | % | % | |
| Hitos completados / total | n/N | n/N | |
| Días transcurridos / total | n/N | — | |

### Próximos Hitos Críticos (30 días)

| Hito | Fecha planificada | Estado |
|------|------------------|--------|
| | DD/MM/AAAA | En plazo / En riesgo / Con retraso |

### Riesgos de Nivel Alto Activos

| RIS-nnn | Descripción breve | Estrategia | Responsable |
|---------|------------------|-----------|------------|
| | | | |

### Cambios rfc Activos

| rfc-nnn | Título breve | Estado | Impacto |
|---------|-------------|--------|---------|
| | | ABIERTO / EVALUADO | |

### Acciones Prioritarias Abiertas

| Acción | Responsable | Fecha límite | Prioridad |
|--------|-------------|-------------|-----------|
| | | | Alta / Media |

### Documentos Pendientes de Revisión / Aprobación

| Documento | Código | Rev. | Responsable | Fecha límite |
|-----------|--------|------|-------------|-------------|
| | | | | |

---

## D19 — Acta de Aceptación {#d19}

> **Comando:** `generar acta de aceptación`
> **Archivo:** `90-management/progress/ACC-nnn.md`
> **Fuente PM²:** Acceptance/Transition Plan (Artefacts v3.1)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Acta N°:** nnn
**Entregable:** [DESCRIPCIÓN DEL ENTREGABLE O PAQUETE ACEPTADO]
**Código / Referencia entregable:** [REF]
**Revisión entregable:** [REV nn]
**Fecha de aceptación:** [DD/MM/AAAA]

### Criterios de Aceptación

| N° | Criterio de aceptación | ¿Cumple? | Observación |
|----|----------------------|---------|-------------|
| 1 | | Sí / No / Parcial | |
| 2 | | | |
| 3 | | | |

### Resultado de la Aceptación

**Decisión:** ACEPTADO / ACEPTADO CON OBSERVACIONES / RECHAZADO

**Observaciones:**
- [Observación 1]

**Condiciones para cierre (si Aceptado con Observaciones):**
- [Condición 1 — responsable — fecha límite]

**Acciones generadas:**

| Acción | Responsable | Fecha límite | Estado |
|--------|-------------|-------------|--------|
| | | | |

### Firmantes

| Nombre | Rol | Firma | Fecha |
|--------|-----|-------|-------|
| | Project Owner / Cliente | | DD/MM/AAAA |
| | Project Manager | | |
| | [Responsable de disciplina] | | |

> Si el resultado es **RECHAZADO**, se emite `rfc-nnn` en `change-requests.md`.
> La decisión genera `DEC-nnn` en `assumptions-and-decisions.md`.

---

## D20 — Revisión del Cliente {#d20}

> **Comando:** `generar revisión del cliente`
> **Archivo:** `90-management/progress/CLIENT_REVIEW-nn.md`

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Revisión N°:** nn
**Fecha:** [DD/MM/AAAA]
**Hito asociado:** [NOMBRE DEL HITO / ENTREGA PARCIAL]
**Elaborado por:** [PM / NOMBRE]

### Entregables Presentados

| Entregable | Código | Rev. | Disciplina | Estado previo |
|-----------|--------|------|-----------|--------------|
| | | | | Para revisión cliente |

### Comentarios del Cliente

| N° | Documento | Pág./Sección | Comentario del cliente | Categoría | Acción / Respuesta |
|----|-----------|-------------|----------------------|-----------|-------------------|
| C01 | | | | Mayor / Menor / Info | |
| C02 | | | | | |

**Categorías:** Mayor = requiere modificación técnica · Menor = corrección editorial · Info = solo información.

### Resultado de la Revisión

**Decisión del cliente:** APROBADO / APROBADO CON COMENTARIOS / RECHAZADO — REQUIERE REEMISIÓN

**Fecha límite para respuesta/reemisión:** [DD/MM/AAAA]

### Acciones Generadas

| Acción | Responsable | Fecha límite | Estado |
|--------|-------------|-------------|--------|
| | | | |

> Los **comentarios Mayores** que modifiquen alcance, criterios de diseño o equipos aprobados generan `rfc-nnn` en `change-requests.md`.

---

## D22 — Informe de Visita a Obra {#d22}

> **Comando:** `generar informe visita a obra`
> **Archivo:** `90-management/reports/SITE_VISIT-nn_AAAAMMDD.md`

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Visita N°:** nn
**Fecha:** [DD/MM/AAAA]
**Lugar / Instalación:** [NOMBRE DE LA OBRA / SITIO]
**Elaborado por:** [NOMBRE / ROL]
**Fecha de emisión:** [DD/MM/AAAA]

### Participantes

| Nombre | Empresa / Rol | Asistió |
|--------|-------------|---------|
| | | Sí / No |

### Objetivo de la Visita

[Descripción del propósito: inspección de avance, verificación de instalaciones, resolución de consultas técnicas, etc.]

### Estado General de Obra

**Estado general:** Conforme / Con observaciones / No conforme
**Resumen:**
[Descripción breve del estado general observado.]

### Hallazgos por Disciplina

#### [Disciplina — ej.: Civil]

| N° | Descripción del hallazgo | Plano / Referencia | Estado | Foto ref. |
|----|------------------------|-------------------|--------|-----------|
| H01 | | | Conforme / No conforme / Pendiente | |

#### [Disciplina — ej.: Eléctrica]

| N° | Descripción del hallazgo | Plano / Referencia | Estado | Foto ref. |
|----|------------------------|-------------------|--------|-----------|
| H01 | | | | |

### No Conformidades Detectadas

| NC-nnn | Descripción | Plano / Ref. | Gravedad | Responsable | Fecha límite |
|--------|-------------|-------------|---------|------------|-------------|
| | | | Mayor / Menor | | DD/MM/AAAA |

> Las No Conformidades graves pueden generar `rfc-nnn` si modifican criterios de diseño o equipos aprobados.

### Acciones Acordadas

| Acción | Responsable | Fecha comprometida | Estado |
|--------|------------|------------------|--------|
| | | | ABIERTO |

### Consultas Técnicas Resueltas en Obra

| N° | Consulta | Respuesta / Criterio aplicado | DEC-nnn |
|----|---------|------------------------------|---------|
| | | | |

### Conclusiones Generales

- [Conclusión 1]
- [Conclusión 2]

### Registro Fotográfico

| Foto | Descripción | Ubicación en archivo |
|------|-------------|---------------------|
| Foto-01 | | |

---

## D25 — Informe Final del Proyecto {#d25}

> **Comando:** `generar informe final`
> **Archivo:** `90-management/reports/PROJECT_END_REPORT.md`
> **Fuente PM²:** Project-End Report (Artefacts v3.1, p.236-242)

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Fecha de inicio:** [DD/MM/AAAA]
**Fecha de cierre:** [DD/MM/AAAA]
**Elaborado por:** [PM / NOMBRE]
**Revisado por:** [NOMBRE / ROL]
**Fecha:** [DD/MM/AAAA]

---

## 1. Introducción

El propósito de este informe es documentar los elementos clave del proyecto, capturar la satisfacción del cliente, evaluar la gestión del proyecto, documentar las lecciones aprendidas y ofrecer recomendaciones post-proyecto.

[Descripción breve del proyecto: contexto, objetivo general, alcance entregado.]

---

## 2. Éxito del Proyecto

### 2.1 Efectividad

[¿En qué medida el producto/entregable satisfizo las necesidades del cliente, de la organización ejecutora y de los requisitos del contrato?]

**Métricas de desempeño destacadas:**
- [Métrica 1]
- [Métrica 2]

### 2.2 Evaluación del Proyecto (Alcance – Cronograma – Calidad)

| Dimensión | Línea base | Resultado real | Variación | Evaluación |
|-----------|-----------|---------------|----------|-----------|
| Alcance | [Descripción] | [Descripción] | [Δ] | Conforme / Con desviaciones |
| Cronograma | [Fecha fin plan] | [Fecha fin real] | [Δ días] | |
| Calidad | [Criterios] | [Resultados] | | |

[Análisis de las variaciones. ¿Cuántos rfc se aprobaron? ¿Cuál fue el impacto acumulado en el alcance?]

---

## 3. Evaluación de la Gestión del Proyecto

### 3.1 General

[Evaluación global de la gestión aplicada.]

### 3.2 Gestión de Riesgos

[Riesgos significativos identificados y materializados. Riesgos que ocurrieron sin haber sido identificados. Efectividad de las estrategias de respuesta.]

| Categoría | Registrados | Materializados | Evitados |
|-----------|------------|:--------------|:--------|
| Alto | | | |
| Medio | | | |

### 3.3 Gestión de Interesados

[Efectividad de la gestión de stakeholders. Aspectos destacables y áreas de mejora.]

### 3.4 Comunicaciones del Proyecto

[Efectividad del plan de comunicaciones. Canales utilizados. Aspectos a mejorar.]

### 3.5 Resolución de Problemas

[Incidencias significativas ocurridas y cómo se resolvieron.]

### 3.6 Aceptación de Entregables

[Efectividad del proceso de revisión y aceptación con el cliente. Entregables que generaron más ciclos de revisión.]

---

## 4. Transición del Proyecto

| Actividad de transición | Realizada | Fecha | Observación |
|------------------------|-----------|-------|-------------|
| Entrega de documentación As-Built | Sí / No | | |
| Capacitación al cliente / operaciones | Sí / No | | |
| Transferencia formal de responsabilidades | Sí / No | | |

---

## 5. Evaluación de Equipos

### 5.1 Desempeño de la Organización

[Evaluación del desempeño de la organización ejecutora en el contexto del proyecto.]

### 5.2 Desempeño del Equipo del Proyecto

[Evaluación del equipo núcleo. Responsabilidades clave cumplidas. Áreas de mejora.]

---

## 6. Lecciones Aprendidas y Mejores Prácticas

| LL-nnn | Área | Descripción | Recomendación para futuros proyectos |
|--------|------|-------------|-------------------------------------|
| LL-001 | Técnica | | |
| LL-002 | Gestión | | |
| LL-003 | Proceso / Calidad | | |

---

## 7. Recomendaciones Post-Proyecto

- [Recomendación 1]
- [Recomendación 2]

---

## Apéndice: Documentos de Referencia

| Documento | Versión / Rev. | Ubicación |
|-----------|---------------|-----------|
| Charter del Proyecto | | 90-management/charter/ |
| Plan del Proyecto (línea base) | | 90-management/ |
| Registro de Cambios | — | 90-management/change-requests.md |
| Registro de Riesgos | — | 90-management/GOVERNANCE/RISK_REGISTER.md |
| Lecciones Aprendidas (detalle) | — | 90-management/reports/lessons_REPORT.md |
| Lienzo Final del Proyecto | — | 90-management/reports/PROJECT_END_CANVAS.md |

---

## D26 — Lienzo Final del Proyecto {#d26}

> **Comando:** `generar lienzo final`
> **Archivo:** `90-management/reports/PROJECT_END_CANVAS.md`
> **Fuente PM²:** PM² Project End Canvas (CC BY 4.0)

---

**Proyecto:** [NOMBRE DEL PROYECTO] | **Código:** [CÓDIGO] | **Fecha de cierre:** [DD/MM/AAAA] | **PM:** [NOMBRE]

---

| **Descripción del Proyecto** | **Entregables Producidos** |
|-----------------------------|--------------------------|
| [Objetivo general del proyecto y contexto en 2–3 líneas.] | - [Entregable 1]<br>- [Entregable 2]<br>- [Entregable 3] |

---

| **Factores de Éxito del Proyecto** | **Cronograma de Hitos (real)** |
|-----------------------------------|-------------------------------|
| - [Factor 1]<br>- [Factor 2]<br>- [Factor 3] | [Hito 1] → DD/MM/AAAA<br>[Hito 2] → DD/MM/AAAA |

---

| **Resultados Plenamente Alcanzados** | **Resultados Parcialmente Alcanzados** |
|-------------------------------------|--------------------------------------|
| - [Resultado 1]<br>- [Resultado 2] | - [Resultado parcial — qué faltó o quedó diferido] |

---

| **Lecciones Aprendidas — Técnicas** | **Lecciones Aprendidas — Gestión** |
|------------------------------------|-----------------------------------|
| - [Lección técnica 1]<br>- [Lección técnica 2] | - [Lección de gestión 1]<br>- [Lección de gestión 2] |

---

| **Acciones de Mejora (interna)** | **Recomendaciones Post-Proyecto** |
|---------------------------------|----------------------------------|
| - [Acción de mejora para la organización] | - [Recomendación para el cliente / operaciones] |

---

## D28 — Informe de Lecciones Aprendidas {#d28}

> **Comando:** `generar informe de lecciones`
> **Archivo:** `90-management/reports/lessons_REPORT.md`

---

**Proyecto:** [NOMBRE DEL PROYECTO]
**Código:** [CÓDIGO]
**Elaborado por:** [PM / NOMBRE]
**Fecha:** [DD/MM/AAAA]

### Registro Completo de Lecciones Aprendidas

| LL-nnn | Área | Fase | Descripción de la lección | Causa raíz | Impacto | Recomendación | Aplicabilidad |
|--------|------|------|--------------------------|-----------|---------|--------------|--------------|
| LL-001 | Técnica | Ejecución | | | Alto/Medio/Bajo | | Proyectos de ingeniería similares |
| LL-002 | Gestión | Planificación | | | | | |
| LL-003 | Proceso / Calidad | Cierre | | | | | |

---

### Lecciones por Categoría

#### Técnicas

| LL-nnn | Fase | Descripción | Recomendación |
|--------|------|-------------|--------------|
| | | | |

#### Gestión de Proyectos

| LL-nnn | Fase | Descripción | Recomendación |
|--------|------|-------------|--------------|
| | | | |

#### Procesos y Calidad

| LL-nnn | Fase | Descripción | Recomendación |
|--------|------|-------------|--------------|
| | | | |

#### Relación con el Cliente / Comunicación

| LL-nnn | Fase | Descripción | Recomendación |
|--------|------|-------------|--------------|
| | | | |

### Síntesis de las Lecciones Más Importantes

1. **[Área]:** [La lección más importante y su impacto.]
2. **[Área]:** [Segunda lección más valiosa.]
3. **[Área]:** [Tercera lección.]

### Aplicabilidad a Otros Proyectos

[¿Qué tipo de proyectos futuros se beneficiarían de estas lecciones? ¿Qué elementos deberían incorporarse a la metodología o plantillas estándar?]

---

## CANVAS-I — Lienzo de Inicio del Proyecto {#canvas-i}

> **Comando:** `generar lienzo de inicio`
> **Archivo:** `90-management/charter/PROJECT_INITIATION_CANVAS.md`
> **Fuente PM²:** PM² Project Initiation Canvas (CC BY 4.0)
> **Momento de uso:** Al inicio del proyecto, antes o durante la elaboración del Charter.

---

**Proyecto:** [NOMBRE DEL PROYECTO] | **Código:** [CÓDIGO] | **Fecha:** [DD/MM/AAAA] | **PM:** [NOMBRE]

---

| **Alcance del Proyecto** | |
|--------------------------|--|
| **INCLUIDO (IN)** | **EXCLUIDO (OUT)** |
| - [Qué sí está en el alcance del proyecto] | - [Qué explícitamente NO está en el alcance] |
| - | - |

---

| **Entregables / Productos** | **Resultados Esperados** |
|---------------------------|------------------------|
| - [Entregable o producto 1] | - [Resultado, beneficio o cambio esperado 1] |
| - [Entregable 2] | - [Resultado 2] |

---

| **Supuestos** | **Beneficios** |
|--------------|----------------|
| - [Supuesto 1] | - [Beneficio 1 para el cliente / organización] |
| - [Supuesto 2] | - [Beneficio 2] |

---

| **Restricciones y Dependencias** | **Cronograma de Hitos (estimado)** |
|---------------------------------|-----------------------------------|
| - [Restricción 1: normativa, plazo contractual, recursos] | [Hito 1] → [Fecha estimada] |
| - [Dependencia 1: datos de cliente, permisos] | [Hito 2] → [Fecha estimada] |
| - | [Hito final — Entrega] → [Fecha estimada] |

---

| **Riesgos Iniciales** | **Gobernanza y Equipo** |
|----------------------|------------------------|
| - [Riesgo 1 — nivel estimado] | **Project Owner:** [Nombre] |
| - [Riesgo 2] | **Project Manager:** [Nombre] |
| - [Riesgo 3] | **Disciplinas:** [Lista] |
| | **Cliente / Solicitante:** [Nombre / Empresa] |

---

| **Criterios de Éxito del Proyecto** | **Factores Críticos de Éxito** |
|------------------------------------|-------------------------------|
| - [Criterio medible 1] | - [Factor 1: ej. disponibilidad oportuna de datos de entrada] |
| - [Criterio medible 2] | - [Factor 2: ej. decisiones rápidas del cliente] |
| - [Criterio medible 3] | - [Factor 3] |

---

| **Desglose de Trabajo — Nivel 1 (WBS)** |
|----------------------------------------|
| - **Paquete 1:** [Nombre — ej. Ingeniería Conceptual] |
| - **Paquete 2:** [Nombre — ej. Ingeniería Básica — Disciplina Eléctrica] |
| - **Paquete 3:** [Nombre — ej. Ingeniería Básica — Disciplina Civil] |
| - **Paquete 4:** [Nombre — ej. Coordinación y Gestión del Proyecto] |

---

*Plantillas adaptadas de PM² v3.1 para uso interno del framework de gestión de proyectos de ingeniería.*
*Licencia base: CC BY 4.0 — European Commission (PM² Project Management Methodology).*


---

## Sección §Programme — Plantillas de Gestión de Programas

> **Módulo:** M10 `.claude/rules/m10-programme-management.md`
> **Uso:** Claude usa estas plantillas al ejecutar `escalar a programa`, `agregar proyecto al programa` y `generar estado del programa`.
> **Confidencialidad:** Los campos de costo, presupuesto, honorarios y condiciones comerciales son confidenciales y **nunca se completan** con datos reales.
> **Licencia base:** Adaptado de PM² v3.1 (CC BY 4.0 — European Commission).

### Índice §Programme

| Código | Nombre | Comando |
|--------|--------|---------|
| [PC](#pc) | Charter del Programa | `escalar a programa` ● |
| [PMP](#pmp) | Plan de Gestión del Programa | `escalar a programa` ● |
| [PROAD](#proad) | Hoja de Ruta del Programa | `escalar a programa` ● |
| [PBEN](#pben) | Registro de Beneficios del Programa | `escalar a programa` ● |
| [PGSTATUS](#pgstatus) | Informe de Estado del Programa | `generar estado del programa` |

---

## PC — Charter del Programa {#pc}

> **Comando:** `escalar a programa` ●
> **Archivo:** `90-management/PROGRAMME/PROGRAMME_charter.md`
> **Fuente PM²:** PM² Programme Management Guide v3.1 — Programme Charter

---

**Programa:** [NOMBRE DEL PROGRAMA]
**Código:** [PGM-XXX]
**Versión:** 1.0
**Estado:** BORRADOR / APROBADO
**Fecha:** [DD/MM/AAAA]
**Preparado por:** [Programme Manager — NOMBRE]
**Aprobado por:** [Programme Sponsor — NOMBRE]

---

### 1. Descripción del Programa

[Descripción concisa del programa: qué agrupa, por qué se gestiona como programa y no como proyectos independientes. 3-5 líneas.]

### 2. Justificación (Business Case)

[Por qué el programa existe. Problema u oportunidad que aborda. Qué lo diferencia de gestionar cada proyecto por separado.]

### 3. Alcance del Programa

#### 3.1 Incluye
- [Proyecto / Disciplina / Entregable 1]
- [Proyecto / Disciplina / Entregable 2]

#### 3.2 Excluye explícitamente
- [Lo que no está cubierto]

### 4. Proyectos constituyentes

| ID | Nombre del Proyecto | PM | Estado | Interdependencias clave |
|----|-------------------|----|--------|------------------------|
| P01 | [Nombre] | [PM] | [estado] | — |
| P02 | [Nombre] | [PM] | [estado] | depende de P01 |

### 5. Objetivos y beneficios esperados

| N° | Objetivo | Métrica | Baseline | Meta | Fecha medición |
|----|----------|---------|----------|------|---------------|
| B01 | [Objetivo] | [cómo se mide] | [valor actual] | [valor objetivo] | [fecha] |
| B02 | | | | | |

### 6. Gobernanza

| Rol | Nombre | Responsabilidad |
|-----|--------|----------------|
| Programme Sponsor | [Nombre] | Autoriza el programa; aprueba cambios de alcance |
| Programme Manager | [Nombre] | Coordina proyectos; gestiona PROAD y PBEN |
| PSC-P | [Miembros] | Decisiones transversales al programa |
| PM Proyecto P01 | [Nombre] | Gestiona P01 con autonomía |
| PM Proyecto P02 | [Nombre] | Gestiona P02 con autonomía |

### 7. Supuestos y restricciones

**Supuestos:**
- [Supuesto 1]

**Restricciones:**
- [Restricción 1]

### 8. Riesgos transversales del programa

| ID | Descripción | P | I | Nivel | Respuesta |
|----|-------------|---|---|-------|-----------|
| PGRIE-001 | [Riesgo que afecta a más de un proyecto] | — | — | — | — |

### 9. Hitos del programa

| Hito | Descripción | Fecha planificada | Proyecto(s) involucrado(s) |
|------|-------------|-------------------|--------------------------|
| H01 | Kick-off del programa | DD/MM/AAAA | Todos |
| H02 | [Hito clave 1] | | |
| H03 | Cierre del programa | | |

### 10. Historial de versiones

| Versión | Fecha | Autor | Cambio |
|---------|-------|-------|--------|
| 1.0 | DD/MM/AAAA | [Nombre] | Emisión inicial |

---

*Charter generado con el framework PM² v3.1 adaptado. Módulo M10.*

---

## PMP — Plan de Gestión del Programa {#pmp}

> **Comando:** `escalar a programa` ●
> **Archivo:** `90-management/PROGRAMME/PROGRAMME_management_PLAN.md`
> **Fuente PM²:** PM² Programme Management Guide v3.1 — Programme Management Plan

---

**Programa:** [NOMBRE DEL PROGRAMA]
**Código:** [PGM-XXX]
**Versión:** 1.0
**Fecha:** [DD/MM/AAAA]
**Programme Manager:** [Nombre]

---

### 1. Propósito

Este Plan define cómo se coordinan los proyectos constituyentes del Programa `[NOMBRE]`, cómo se gestionan las interdependencias y cómo se reporta al PSC-P.

### 2. Modo de gestión

| Aspecto | Decisión |
|---------|---------|
| Reuniones de programa | [Frecuencia: semanal / quincenal / mensual] |
| Informe de estado del programa | [Frecuencia: cada STATUS de proyectos / mensual] |
| Escalada de dependencias bloqueantes | Programme Manager → PSC-P en [plazo] |
| Gestión de cambios transversales | rfc en el proyecto origen → revisión por PSC-P si afecta a otro proyecto |

### 3. Coordinación entre proyectos

#### 3.1 Reuniones

| Tipo | Participantes | Frecuencia | Responsable |
|------|--------------|------------|-------------|
| Coordinación de programa | Programme Manager + PMs | [frecuencia] | Programme Manager |
| PSC-P | Sponsor + PSC-P | [frecuencia] | Programme Sponsor |

#### 3.2 Gestión de interdependencias

Las interdependencias se documentan en `PROGRAMME_roadmap.md`. El proceso es:
1. PM identifica una dependencia con otro proyecto → la registra en PROAD.
2. Si la dependencia crea un riesgo de retraso → escala al Programme Manager.
3. Si afecta al alcance o al presupuesto → PSC-P decide.

#### 3.3 Gestión de cambios transversales

Un cambio que afecta a más de un proyecto genera:
- Un rfc en el proyecto origen (proceso M8).
- Una revisión por el Programme Manager.
- Una decisión del PSC-P si el cambio impacta en otro proyecto (genera DEC-nnn a nivel programa).

### 4. Reporting

| Documento | Frecuencia | Audiencia | Responsable |
|-----------|-----------|-----------|-------------|
| STATUS por proyecto (D11) | [según M8] | PSC del proyecto | PM del proyecto |
| PGSTATUS del programa | Mensual | PSC-P | Programme Manager |
| Revisión de PBEN | Trimestral | Programme Sponsor | Programme Manager |

### 5. Criterios de éxito del programa

| Criterio | Indicador | Meta |
|----------|----------|------|
| [Criterio 1] | [Cómo se mide] | [Valor] |

### 6. Plan de cierre del programa

El programa se cierra cuando:
- [ ] Todos los proyectos constituyentes están cerrados.
- [ ] Los beneficios de PBEN han sido realizados o documentados como no realizados con causa.
- [ ] El `PROJECT_END_REPORT.md` del programa ha sido aprobado por el Programme Sponsor.

---

*Plan generado con el framework PM² v3.1 adaptado. Módulo M10.*

---

## PROAD — Hoja de Ruta del Programa {#proad}

> **Comando:** `escalar a programa` ●
> **Archivo:** `90-management/PROGRAMME/PROGRAMME_roadmap.md`
> **Fuente PM²:** PM² Programme Management Guide v3.1 — Programme Roadmap

---

**Programa:** [NOMBRE DEL PROGRAMA]
**Código:** [PGM-XXX]
**Versión:** 1.0
**Fecha:** [DD/MM/AAAA]
**Programme Manager:** [Nombre]

---

### 1. Cronograma integrado

| Proyecto | Fase | Inicio planificado | Fin planificado | Estado | RAG |
|---------|------|--------------------|----------------|--------|-----|
| P01 — [Nombre] | Iniciación | DD/MM/AAAA | DD/MM/AAAA | [estado] | 🟢/🟡/🔴 |
| P01 — [Nombre] | Ejecución | DD/MM/AAAA | DD/MM/AAAA | | |
| P02 — [Nombre] | Iniciación | DD/MM/AAAA | DD/MM/AAAA | | |
| P02 — [Nombre] | Ejecución | DD/MM/AAAA | DD/MM/AAAA | | |

> **RAG:** 🟢 En plazo · 🟡 Riesgo de retraso · 🔴 Retrasado

### 2. Interdependencias

| ID | Proyecto origen | Entregable | Proyecto receptor | Necesario para | Fecha límite | Estado |
|----|----------------|------------|------------------|----------------|-------------|--------|
| DEP-001 | P01 | [Entregable] | P02 | [Para qué] | DD/MM/AAAA | Pendiente |
| DEP-002 | | | | | | |

### 3. Hitos del programa

| ID | Hito | Proyecto(s) | Fecha planificada | Fecha real | Estado |
|----|------|------------|-------------------|-----------|--------|
| H01 | Kick-off del programa | Todos | DD/MM/AAAA | | |
| H02 | [Hito clave 1] | P01 | DD/MM/AAAA | | |
| H03 | [Hito clave 2] | P01, P02 | DD/MM/AAAA | | |
| H04 | Cierre del programa | Todos | DD/MM/AAAA | | |

### 4. Ruta crítica del programa

[Narrativa: qué secuencia de entregables determina la duración mínima del programa. Cuál es el cuello de botella actual.]

### 5. Historial de versiones

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | DD/MM/AAAA | Emisión inicial |

---

*Hoja de ruta generada con el framework PM² v3.1 adaptado. Módulo M10.*

---

## PBEN — Registro de Beneficios del Programa {#pben}

> **Comando:** `escalar a programa` ●
> **Archivo:** `90-management/PROGRAMME/PROGRAMME_BENEFITS_REGISTER.md`
> **Fuente PM²:** PM² Programme Management Guide v3.1 — Benefits Realisation Plan

---

**Programa:** [NOMBRE DEL PROGRAMA]
**Código:** [PGM-XXX]
**Versión:** 1.0
**Fecha:** [DD/MM/AAAA]
**Programme Manager:** [Nombre]

---

### 1. Beneficios planificados

| ID | Descripción del beneficio | Tipo | Responsable de realización | Métrica | Baseline | Meta | Fecha esperada |
|----|--------------------------|------|--------------------------|---------|----------|------|---------------|
| BEN-001 | [Beneficio que no podría lograrse con proyectos independientes] | Técnico / Operativo / Estratégico | [Nombre / Rol] | [Indicador medible] | [Valor actual] | [Valor objetivo] | DD/MM/AAAA |
| BEN-002 | | | | | | | |

> **Confidencialidad:** Los beneficios expresados en términos económicos, de costo o de ahorro **no se registran** en este archivo.

### 2. Estado de realización

| ID | Descripción | Estado | Valor medido | Fecha medición | Observaciones |
|----|------------|--------|-------------|---------------|---------------|
| BEN-001 | | Pendiente / En curso / Realizado / No realizado | | | |

### 3. Beneficios no realizados

| ID | Descripción | Causa | Decisión |
|----|------------|-------|---------|
| | | | Aceptar / Redefinir / Cancelar |

### 4. Resumen de realización

| Total planificados | Realizados | En curso | No realizados |
|--------------------|-----------|---------|--------------|
| | | | |

### 5. Historial de versiones

| Versión | Fecha | Cambio |
|---------|-------|--------|
| 1.0 | DD/MM/AAAA | Emisión inicial |

---

*Registro generado con el framework PM² v3.1 adaptado. Módulo M10.*

---

## PGSTATUS — Informe de Estado del Programa {#pgstatus}

> **Comando:** `generar estado del programa`
> **Archivo:** `90-management/PROGRAMME/STATUS/PGSTATUS-nn_AAAAMMDD.md`
> **Fuente PM²:** PM² Programme Management Guide v3.1 — Programme Status Report

---

**Programa:** [NOMBRE DEL PROGRAMA]
**Código:** [PGM-XXX]
**Informe N°:** nn
**Período:** [DD/MM/AAAA — DD/MM/AAAA]
**Fecha de emisión:** [DD/MM/AAAA]
**Programme Manager:** [Nombre]

---

### 1. Estado global del programa

| RAG global | 🟢 En curso / 🟡 Atención requerida / 🔴 Crítico |
|-----------|---|

[Narrativa de 3-5 líneas: situación actual del programa, avance general, novedad principal del período.]

### 2. Estado por proyecto

| Proyecto | PM | Fase actual | RAG | Avance % | Hito próximo | Fecha hito |
|---------|----|-----------|----|---------|-------------|-----------|
| P01 — [Nombre] | [PM] | [Fase] | 🟢/🟡/🔴 | [%] | [Hito] | DD/MM/AAAA |
| P02 — [Nombre] | [PM] | [Fase] | 🟢/🟡/🔴 | [%] | [Hito] | DD/MM/AAAA |

> **RAG:** 🟢 En plazo y alcance · 🟡 Riesgo identificado, bajo control · 🔴 Retraso o desvío que requiere decisión del PSC-P

### 3. Interdependencias críticas

| DEP-ID | Origen | Receptor | Estado | Riesgo | Acción requerida |
|--------|--------|---------|--------|--------|----------------|
| DEP-001 | P01 | P02 | [estado] | [Sí/No] | [Acción] |

### 4. Riesgos transversales

| ID | Descripción | Nivel | Respuesta activa |
|----|------------|-------|----------------|
| PGRIE-001 | | 🟢/🟡/🔴 | |

### 5. Decisiones pendientes del PSC-P

| Decisión requerida | Propuesta | Urgencia | Responsable |
|-------------------|----------|---------|-------------|
| | | Alta / Media | |

### 6. Beneficios — estado del período

| ID | Beneficio | Estado | Novedad |
|----|----------|--------|---------|
| BEN-001 | | Pendiente / En curso / Realizado | |

### 7. Acciones al cierre del período

| Acción | Responsable | Fecha límite | Estado |
|--------|-------------|-------------|--------|
| | | DD/MM/AAAA | Abierta / Cerrada |

### 8. Próximo período

[Qué se espera para el período siguiente: hitos, decisiones, entregas clave.]

---

*Informe generado con el framework PM² v3.1 adaptado. Módulo M10.*
