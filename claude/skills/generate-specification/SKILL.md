---
name: "generate-specification"
description: "Genera pliegos de especificaciones técnicas (PG) y especificaciones técnicas (ET) para cualquier disciplina de ingeniería, usando el agente Document Writer y el conocimiento aprendido de pliegos del usuario."
---

# generar-pliego

> **Naming rule (always enforced):** all files and folders use `kebab-case-english`.
> See `CLAUDE.md` in this skill's root for the full convention.

---

## Contexto de ejecución

- **Invocación:** explícita — ejecutar solo cuando el usuario pida generar, redactar o revisar un pliego técnico (`PG`), especificación técnica (`ET`) o memoria descriptiva (`MD`).
- **Contexto requerido:** directorio `02_ENGINEERING`. No ejecutar en `90_MANAGEMENT`, `01_INPUT`, `04_REVIEW` ni `06_DELIVERABLES`.
- **Señales de activación:** el usuario dice "generar pliego", "redactar especificación", "crear pliego [disciplina]", "capítulo [nombre]", o entrega un paquete cuya LME incluye un `PG-nnn`.
- **Agente de redacción:** delega la redacción al agente **Document Writer** (`.claude/agents/document-writer.md`).

---

## Capacidades nativas (siempre disponibles, sin capacitación)

| Capacidad | Descripción |
|---|---|
| Generar pliego completo | Todos los capítulos del `PG` en archivos `.md` numerados |
| Generar capítulo individual | Un solo capítulo del pliego |
| **Ensamblar desde bloques LEGO** | `python3 assemble-spec.py <discipline>` — offline, sin Claude |
| Revisar pliego existente | Auditar un pliego para hallazgos de calidad contractual |
| Autocontrol del pliego | Verificar criterios de aceptación, normas, marcas abiertas y coherencia |

Con capacitación (`skill learn`), además:
- Adopta el estilo, nivel de detalle y estructura de los pliegos aprobados del usuario.
- Aplica las normas internas específicas del cliente.
- Reutiliza capítulos modelo ya validados como punto de partida.

---

## Modo LEGO (ensamblado offline desde bloques)

Para proyectos Ford, en lugar de generar desde cero, usar los bloques pre-escritos:

```bash
# 1. Abrir el 00-project-data.md de la disciplina y tildar [x] los bloques que aplican
#    Ubicación: knowledge/templates/<discipline>/[blocks/]00-project-data.md

# 2. Ensamblar:
python3 assemble-spec.py electrical --out spec-mi-proyecto.md

# 3. Resultado en knowledge/assembled/spec-mi-proyecto.md
#    Reemplazar todos los {{VARIABLES}} con datos reales del proyecto
```

**Disciplinas disponibles:**
| Clave | Disciplina | Bloques |
|-------|-----------|---------|
| `electrical` | Eléctrica | 17 |
| `civil` | Civil | 13 |
| `fire-suppression` | Combate de Incendios | 13 |
| `fire-detection` | Detección de Incendios | 12 |
| `hvac` | HVAC | 13 |
| `thermomechanical` | Termomecánica | 11 |

Bloques en `knowledge/templates/<discipline>/[blocks/]`:
```
00-project-data.md          ← checklist de bloques + datos del proyecto
01-descriptive-report.md
02-standards-codes.md
03-detail-engineering.md
04-general-conditions.md
05a-...  05b-... (discipline-specific)
06-testing-commissioning.md
07-asbuilt-docs.md
08-training.md
09-responsibilities.md
```

---

## Paso 1 — Identificar el paquete en la LME

Leer `deliverables.md` y localizar el entregable `PG-nnn` correspondiente. Verificar:
- **Disciplina** del pliego (E, C, H, FP, I, T, etc.).
- **Capítulos requeridos** para la fase actual (`IC`, `IB`, `ID`, `IE`).
- **Estado** de los paquetes de los que depende este pliego (deben estar `REVIEWED`).

Si el pliego no existe en la LME, proponer su registro antes de continuar.

---

## Paso 2 — Verificar la puerta de preparación (por capítulo)

Evaluar capítulo por capítulo según la tabla de dependencias de M5:

| Capítulo | Depende de |
|---|---|
| 01 Alcance | Línea base (`project-charter.md` aprobado) |
| 02 Informe descriptivo | Etapa 1 — criterios de diseño |
| 03 Normas y códigos | Línea base + `engineering-standards.md` |
| 04 Materiales y equipos | Etapa 2 — cálculos dimensionados (`REVIEWED`) |
| 05 Ejecución | Etapa 2 y diagramas (`REVIEWED`) |
| 06 Controles de calidad | Capítulos 04 y 05 redactados |
| 07 Documentación de entrega | Capítulos anteriores redactados |
| 08 Garantías | Requisitos del cliente confirmados |
| 09 Responsabilidades | Todos los capítulos anteriores (`siempre el último`) |

Capítulos sin respaldo quedan `BLOCKED` con su `BLQ-nnn`. Continuar con los que sí cumplen.

---

## Paso 3 — Cargar el conocimiento aprendido

Si el skill fue capacitado (`skill learn`), leer `memory/INDEX.md`:

1. Identificar pliegos de disciplina similar en `memory/`.
2. Leer los resúmenes de capítulos relevantes.
3. Tomar nota del nivel de detalle, vocabulario y estructura del cliente.
4. **No copiar contenido** — usar como guía de estilo y patrón estructural.

Si no hay capacitación: proceder con las reglas base de `TECHNICAL_SPECIFICATIONS_GUIDE.md` y el agente Document Writer.

---

## Paso 4 — Redactar (delegar al agente Document Writer)

Invocar el agente **Document Writer** con el siguiente contexto:

```
Disciplina: [código DISC]
Paquete: [PQ-nn]
Entregable: [PG-nnn código completo]
Fase: [IC/IB/ID/IE]
Capítulos a redactar: [lista de capítulos cuya puerta se cumple]
Documentos de respaldo disponibles: [lista de archivos REVIEWED]
Pliegos similares aprendidos: [sí/no — si sí, rutas en memory/]
```

El agente Document Writer redacta siguiendo sus propias reglas (`.claude/agents/document-writer.md`).

---

## Paso 5 — Guardar y registrar

Guardar cada capítulo en `02-engineering/TECHNICAL_SPECS/` con la nomenclatura:

```
[SIGLA]-[DISC]-PG-[nnn]_[nn]_[NombreCapitulo]_Rev[00.0.IC].md
```

Ejemplo:
```
VIL-E-PG-001_01_Scope_Rev00.0.ID.md
VIL-E-PG-001_04_Materials_Rev00.0.ID.md
```

Actualizar:
- `deliverables.md` — estado `DRAFT` del paquete correspondiente.
- `traceability-matrix.md` — requisitos cubiertos por este pliego.

---

## Paso 6 — Autocontrol y entrega a revisión

Antes de pasar a `FOR_REVIEW`, ejecutar el autocontrol del pliego (por capítulo):

1. ¿Cada requisito tiene criterio de aceptación?
2. ¿Ningún valor técnico sin fuente identificable?
3. ¿Normas citadas con edición (año o versión)?
4. ¿Sin `{{placeholders}}` sin reemplazar?
5. ¿Sin marcas `[DEFINIR]` no registradas en `project-status.md`?
6. ¿Nivel de detalle coherente con la fase de ingeniería?
7. ¿Capítulo de Responsabilidades es el último?
8. ¿Formato Pandoc correcto (sin numeración manual en títulos, viñetas con `-`)?

Con el verificador `epc_documents.specification_verifier` (`engine/documents`, `PYTHONPATH=engine/documents/src`):
```bash
python -m epc_documents.specification_verifier 02-engineering/TECHNICAL_SPECS
```

Entregar la hoja de revisión del paquete y detenerse.

---

## Capacitación de la skill

### Dónde depositar los pliegos

```
.claude/skills/generar-pliego/knowledge/
├── pdf/          ← PDFs fuente (kebab-case: ford-pliego-electrico-001.pdf)
├── extracted/    ← Texto extraído de Sección 4 (kebab-case .md)
├── assembled/    ← Pliegos ensamblados listos para editar
├── templates/    ← Bloques LEGO por disciplina (ver estructura arriba)
├── examples/     ← Capítulos modelo aprobados por el cliente
├── standards/    ← Normas internas, guías de estilo del cliente
└── references/   ← Pliegos públicos, normas de organismos
```

### Cómo capacitar

```bash
# Estudiar todo lo nuevo o modificado
python -B .claude/library/core/skill_learn.py generar-pliego learn

# Ver estado de capacitación
python -B .claude/library/core/skill_learn.py generar-pliego status

# Estudiar un pliego específico
python -B .claude/library/core/skill_learn.py generar-pliego learn pdf/ford-pliego-electrico-001.pdf

# Reconstruir el conocimiento desde cero
python -B .claude/library/core/skill_learn.py generar-pliego relearn
```

### Qué aprende el skill

Por cada pliego en `knowledge/`, el motor genera en `memory/`:
- Resumen del alcance y disciplina.
- Estructura de capítulos y nivel de detalle.
- Normas citadas y requisitos característicos del cliente.
- Índice semántico cruzado por disciplina y tipo de capítulo.

El agente Document Writer consulta `memory/INDEX.md` antes de redactar para alinearse con los estándares del usuario.
