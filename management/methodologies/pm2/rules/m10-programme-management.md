# Módulo M10 — Gestión de Programas

Autoridad: la misma que `CLAUDE.md`. Complementa M8. Claude lo lee cuando el usuario ejecuta `escalar a programa`, `disolver programa`, `agregar proyecto al programa`, `generar estado del programa` o `ver estado del programa`.

---

## 1. Concepto de Programa

Un **Programa** es un conjunto de Proyectos relacionados que se gestionan de forma coordinada para obtener beneficios que no serían posibles gestionándolos de manera independiente.

| Criterio | Proyecto | Programa |
|---|---|---|
| Entregables | un conjunto unificado | entregables por proyecto; sinergia entre ellos |
| Equipo | un PM | un Programme Manager + un PM por proyecto |
| Contratos | uno o consolidado | contratos separados por proyecto o disciplina |
| Cronograma | fases coordinadas internamente | timelines distintos con interdependencias formales |
| Beneficio principal | suma de entregables | beneficio que ningún proyecto produce solo |

**Regla de escalada:** ante la duda, sigue como Proyecto. La escalada es una decisión de gobernanza, no una clasificación técnica.

---

## 2. Roles de Programa

| Rol | Equivalencia en Proyecto | Responsabilidad |
|---|---|---|
| Programme Sponsor | Project Owner | Autoriza el programa; aprueba el Programme Charter |
| Programme Manager | Project Manager | Coordina entre proyectos; gestiona PROAD, PBEN y dependencias transversales |
| PM de proyecto | Project Manager | Gestiona su proyecto con autonomía; usa M8 normalmente |
| Programme Steering Committee (PSC-P) | Steering Committee | Toma decisiones que afectan a más de un proyecto |

El Programme Manager **no sustituye** a los PMs individuales; su rol es la coordinación de interdependencias y la realización de beneficios.

---

## 3. Estructura de documentos

### 3.1 Antes de escalar (Proyecto)
```
90-management/
  charter/          ← charter del proyecto
  progress/         ← actas, estados
  reports/          ← informes
```

### 3.2 Después de escalar (Programa)
```
90-management/
  PROGRAMME/
    PROGRAMME_charter.md            ← PC   (plantilla en management-templates.md)
    PROGRAMME_management_PLAN.md    ← PMP
    PROGRAMME_roadmap.md            ← PROAD
    PROGRAMME_BENEFITS_REGISTER.md  ← PBEN
    STATUS/
      PGSTATUS-nn_AAAAMMDD.md       ← PGSTATUS (informe de estado del programa)
  PROJECTS/
    [NOMBRE-PROYECTO-1]/            ← proyecto original convertido
      charter/
      progress/
      reports/
    [NOMBRE-PROYECTO-2]/            ← nuevo proyecto o disciplina
      charter/
      progress/
      reports/
```

### 3.3 Catálogo de documentos de Programa

| ID | Documento | Ruta (relativa a `90-management/`) | Disparador |
|---|---|---|---|
| PC | Charter del Programa | `PROGRAMME/PROGRAMME_charter.md` | `escalar a programa` ● |
| PMP | Plan de Gestión del Programa | `PROGRAMME/PROGRAMME_management_PLAN.md` | `escalar a programa` ● |
| PROAD | Hoja de Ruta del Programa | `PROGRAMME/PROGRAMME_roadmap.md` | `escalar a programa` ● |
| PBEN | Registro de Beneficios | `PROGRAMME/PROGRAMME_BENEFITS_REGISTER.md` | `escalar a programa` ● |
| PGSTATUS | Informe de Estado del Programa | `PROGRAMME/STATUS/PGSTATUS-nn_AAAAMMDD.md` | `generar estado del programa` |

Las plantillas de PC, PMP, PROAD, PBEN y PGSTATUS están en `.claude/rules/management-templates.md` (sección §Programme).

---

## 4. Frases fijas

### `escalar a programa` ● (cambio de estado crítico)

**Condición previa:** el proyecto tiene `charter aprobado`. La escalada puede originarse en un rfc aprobado que amplía el alcance, o en una decisión explícita del usuario.

**Claude ejecuta — en este orden:**

1. Genera `DEC-nnn` en `assumptions-and-decisions.md` documentando la decisión de escalar: fecha, motivo, quién lo decidió.
2. Crea `90-management/PROGRAMME/PROGRAMME_charter.md` (plantilla PC).
3. Crea `90-management/PROGRAMME/PROGRAMME_management_PLAN.md` (plantilla PMP).
4. Crea `90-management/PROGRAMME/PROGRAMME_roadmap.md` (plantilla PROAD).
5. Crea `90-management/PROGRAMME/PROGRAMME_BENEFITS_REGISTER.md` (plantilla PBEN).
6. Crea `90-management/PROJECTS/[NOMBRE-PROYECTO-1]/` con subcarpetas `charter/`, `progress/`, `reports/` y copia el charter existente como charter del Proyecto 1. El original queda en `90-management/charter/` como referencia histórica.
7. Informa al usuario qué se creó y solicita: nombre definitivo del Proyecto 1 (si difiere del nombre actual), nombre del Proyecto 2, nombre del Programme Manager.

**Confirmación requerida:** sí — el usuario debe escribir la frase exacta `escalar a programa` o confirmarla al ser preguntado.

---

### `disolver programa` ● (cambio de estado crítico)

**Condición previa:** existe `90-management/PROGRAMME/PROGRAMME_charter.md`.

**Claude ejecuta — en este orden:**

1. Genera `DEC-nnn` en `assumptions-and-decisions.md` documentando la decisión de disolver: fecha, motivo, estado de beneficios al momento de la disolución.
2. Mueve los documentos de programa a `90-management/PROGRAMME/ARCHIVED/` (nunca borra; renombra con sufijo `_DISSOLVED_AAAAMMDD`).
3. Informa los proyectos activos bajo `PROJECTS/` y pregunta por cada uno: ¿continúa activo como proyecto independiente, o se cierra?
4. Para cada proyecto que continúa independiente: Claude informa que su carpeta en `PROJECTS/[nombre]/` es ahora su `90-management/` autónomo. No mueve archivos sin confirmación si hay riesgo de pérdida.
5. Para cada proyecto que se cierra: genera un `GATE-nn_CLOSING` y lo marca como cerrado.
6. Informa estado final.

**Confirmación requerida:** sí — el usuario debe escribir la frase exacta `disolver programa` o confirmarla al ser preguntado.

---

### `agregar proyecto al programa: [nombre]`

Crea `90-management/PROJECTS/[nombre]/` con subcarpetas `charter/`, `progress/`, `reports/`. No requiere confirmación ●, pero Claude informa antes de crear y espera un «sí» si la carpeta ya existe.

---

### `generar estado del programa`

Genera `PGSTATUS-nn_AAAAMMDD.md` en `90-management/PROGRAMME/STATUS/` usando la plantilla PGSTATUS. Consolida el estado RAG de cada proyecto bajo `PROJECTS/`. No reemplaza los STATUS individuales de cada proyecto.

---

### `ver estado del programa`

Muestra un resumen en chat (no genera archivo): estado RAG de cada proyecto, próxima interdependencia crítica según PROAD, y beneficios logrados vs. planificados según PBEN.

---

## 5. Reglas de programa

1. **Autonomía de proyectos.** Cada proyecto se gestiona con M8 de forma autónoma. El Programme Manager coordina dependencias y beneficios, no reemplaza a los PMs.
2. **Dependencias.** Las interdependencias se documentan en `PROGRAMME_roadmap.md`. Un proyecto que bloquea a otro se escala al PSC-P.
3. **Beneficios.** `PROGRAMME_BENEFITS_REGISTER.md` es el artefacto central del programa. Si no hay beneficios que justifiquen la coordinación, el programa debe disolverse.
4. **Informes consolidados.** El `PGSTATUS` consolida los STATUS individuales. Ambos conviven: el proyecto reporta a su PM; el programa reporta al PSC-P.
5. **Cierre del programa.** El programa se cierra cuando todos los proyectos están cerrados y los beneficios han sido realizados o documentados como no realizados. Genera un `PROJECT_END_REPORT.md` a nivel programa (plantilla D25).
6. **Confidencialidad.** La misma regla de `CLAUDE.md`: costos, presupuestos, honorarios y condiciones comerciales son confidenciales y **nunca se transcriben** en ningún artefacto del programa.
7. **Un solo nivel de programa.** Este módulo no define Portafolios. Si el usuario plantea gestionar programas de programas, Claude informa que está fuera del alcance del framework actual.
