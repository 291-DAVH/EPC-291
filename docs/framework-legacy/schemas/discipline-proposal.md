# Schema: Propuesta de Disciplina (DISCIPLINE_PROPOSAL)

> **Uso:** Plantilla que Claude usa cuando propone incorporar o excluir una disciplina al alcance del proyecto, cuando detecta que falta definir el alcance de una disciplina, o cuando un cambio de alcance afecta a una disciplina nueva.
> **Disparador:** Aparece en la Fase 2 del arranque (`M3`) o en una rfc que amplía el alcance.

---

## Estructura del documento de propuesta

```markdown
---
tipo: DISCIPLINE_PROPOSAL
id: PROP-DISC-nnn
fecha: AAAA-MM-DD
disciplina: [E | C | S | A | M | TM | H | PL | FP | FD | I | T]
accion: [INCLUIR | EXCLUIR | MODIFICAR_ALCANCE]
estado: [PROPUESTA | APROBADA | RECHAZADA]
---

# Propuesta de Disciplina: [Nombre de la disciplina] — [INCLUIR / EXCLUIR / MODIFICAR]

## Contexto

[Por qué se genera esta propuesta: qué dato o documento la origina.]

## Descripción de la disciplina y su alcance propuesto

**Disciplina:** [nombre completo]
**Código:** [E / C / S / A / M / TM / H / PL / FP / FD / I / T]

**Alcance propuesto (IN):**
- [Qué incluye esta disciplina en el proyecto]
- [Sistemas, equipos, documentos que genera]

**Exclusiones explícitas (OUT):**
- [Qué NO incluye, con justificación si no es obvia]

## Justificación

[Por qué debe incluirse / excluirse / modificarse. Fundamento técnico o contractual.
Si es una exclusión: qué disciplina absorbe esa función, o por qué no es necesaria.]

## Impacto en el proyecto

| Aspecto | Impacto |
|---------|---------|
| LME (entregables) | [Se agregan / eliminan n entregables] |
| Paquetes | [Se agregan / eliminan n paquetes] |
| Interfaces con otras disciplinas | [Disciplinas afectadas: E↔I, H↔E, etc.] |
| Normas aplicables adicionales | [NOR-nnn: nombre de norma] |
| Carpeta en 02-engineering | [`02-engineering/XX_NOMBRE/`] |

## Parámetros técnicos requeridos para iniciar la disciplina

[Lista de parámetros que deben estar en `project-information.md` antes de que pueda arrancar la disciplina.
Si alguno falta, se registra como `INF-nnn`.]

| Parámetro | Estado | ID |
|-----------|--------|-----|
| [Parámetro 1] | DISPONIBLE / FALTANTE | PAR-nnn o INF-nnn |
| [Parámetro 2] | | |

## Decisión requerida

Esta propuesta requiere una `DEC-nnn` en `assumptions-and-decisions.md` para incorporarse a la línea base.

**Opciones:**
- **A — Aprobar:** La disciplina se incorpora al alcance con el alcance propuesto.
- **B — Rechazar:** La disciplina no se incluye. Justificación requerida.
- **C — Modificar:** Aprobar con el alcance modificado: [describir qué cambia].

**Frase fija para aprobar:** `aprobar propuesta PROP-DISC-nnn`
```

---

## Reglas de uso

1. Claude genera un `DISCIPLINE_PROPOSAL` cuando detecta que una disciplina marcada en `starting-data.md` no tiene su alcance definido en `project-scope.md`, o cuando una rfc agrega una disciplina nueva.
2. El documento se guarda en `90-management/GOVERNANCE/PROPOSALS/PROP-DISC-nnn_YYYYMMDD_[DISC].md`.
3. La propuesta no es aprobación: solo el usuario puede aprobarla con la frase fija.
4. Una propuesta aprobada genera automáticamente:
   - `DEC-nnn` en `assumptions-and-decisions.md`
   - Fila en `project-scope.md` (alcance `ALD-nnn` de la disciplina)
   - Carpeta `02-engineering/XX_NOMBRE/` (si no existe)
   - Filas de entregables en `deliverables.md`
   - Parámetros faltantes como `INF-nnn` en `project-status.md`

---

## Códigos de disciplina del framework

| Código | Disciplina | Agente de revisión |
|--------|-----------|-------------------|
| `E` | Eléctrica | `Senior Electrical Engineer` |
| `C` | Civil | `Senior Civil Engineer` |
| `S` | Estructuras | `Senior Civil Engineer` |
| `A` | Arquitectura | *(sin agente especializado — revisor técnico general)* |
| `M` | Mecánica | `Senior Mechanical Engineer` |
| `TM` | Termomecánica | `Senior Mechanical Engineer` |
| `H` | HVAC | `Senior HVAC Engineer` |
| `PL` | Cañerías / Sanitaria | `Senior Piping & Plumbing Engineer` |
| `FP` | Protección contra incendio (combate) | `Senior Fire Protection Engineer` |
| `FD` | Detección y alarma de incendio | `Senior Fire Protection Engineer` |
| `I` | Instrumentación y control | `Senior Instrumentation & Control Engineer` |
| `T` | Telecomunicaciones | `Senior Telecommunications Engineer` |
