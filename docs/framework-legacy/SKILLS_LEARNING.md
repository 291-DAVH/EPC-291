# Sistema de Skills — Guía de Capacitación Incremental

> Wiki del framework · Solo lectura · Versión 1.0 · 2026-10-14

---

## Concepto fundamental

Cada Skill tiene dos componentes separados:

| Componente | Descripción | Modifiable |
|---|---|---|
| **Finalidad** | Lo que la Skill hace (generar SLD, calcular cables, etc.) | No |
| **Conocimiento** | Cómo lo hace (estilos, normas, plantillas, convenciones) | Sí — vía capacitación |

Dos usuarios con la misma Skill obtienen resultados distintos si capacitaron la Skill con información diferente.

---

## Estructura de una Skill capacitable

```text
.claude/skills/<nombre>/
├── skill.json              ← declaración de capacidades y tipos de conocimiento
├── core/                   ← lógica interna de la Skill (no tocar)
├── knowledge/              ← BASE DE CONOCIMIENTO DEL USUARIO (aquí depositar archivos)
│   ├── pdf/                ← normas, manuales, catálogos
│   ├── svg/                ← símbolos, plantillas SVG corporativas
│   ├── dxf/                ← plantillas DXF del cliente
│   ├── examples/           ← ejemplos aprobados de proyectos anteriores
│   ├── standards/          ← criterios propios del cliente
│   ├── templates/          ← carátulas, láminas, rótulos corporativos
│   ├── images/             ← imágenes de referencia
│   └── references/         ← documentos de referencia adicionales
├── learning/
│   └── inventory.json      ← registro de qué fue estudiado (hashes SHA-256)
├── cache/                  ← caché temporal de aprendizaje
├── outputs/                ← salidas generadas por la Skill
├── templates/              ← plantillas de trabajo de la Skill
├── standards/              ← estándares activos de la Skill
└── memory/
    ├── INDEX.md            ← índice semántico generado automáticamente
    └── <archivo>.md        ← resumen y notas por cada archivo estudiado
```

---

## Comandos de capacitación

El motor de aprendizaje es `.claude/library/core/skill_learn.py`.

### Ver el estado

```bash
python -B .claude/library/core/skill_learn.py <skill_name> status
```

Muestra: archivos totales, estudiados, pendientes, modificados, último aprendizaje, tipos de conocimiento declarados.

### Aprender archivos nuevos o modificados

```bash
python -B .claude/library/core/skill_learn.py <skill_name> learn
```

- Escanea `knowledge/` completo.
- Calcula SHA-256 de cada archivo.
- Compara contra `learning/inventory.json`.
- Estudia solo los archivos nuevos o modificados.
- Genera resúmenes en `memory/`.
- Actualiza `memory/INDEX.md`.

### Aprender un archivo específico

```bash
python -B .claude/library/core/skill_learn.py <skill_name> learn <archivo.pdf>
```

### Aprender solo los modificados

```bash
python -B .claude/library/core/skill_learn.py <skill_name> learn --modified
```

### Reaprender desde cero

```bash
python -B .claude/library/core/skill_learn.py <skill_name> relearn
```

Borra `cache/`, `memory/` e `inventory.json`, luego estudia todo desde cero. Usar cuando se reestructure el conocimiento o haya inconsistencias.

---

## Flujo de trabajo típico

```text
1. Usuario deposita archivos en knowledge/
2. python -B skill_learn.py <skill> learn   → Skill aprende lo nuevo
3. Invocar la Skill normalmente              → aplica el conocimiento aprendido
4. Al agregar más archivos → skill learn    → solo estudia lo nuevo
```

---

## `skill.json` — estructura

Cada Skill declara qué tipos de conocimiento acepta:

```json
{
  "name": "nombre-de-la-skill",
  "version": "2.0.0",
  "supports_learning": true,
  "learnable_content": ["svg", "pdf", "dxf", "examples", "standards", "templates"],
  "knowledge_types": {
    "svg": "Descripción de qué SVGs son útiles para esta Skill",
    "pdf": "Qué PDFs aportan valor"
  },
  "capabilities": ["capacidad_1", "capacidad_2"],
  "invocation": "explicit",
  "context_requires": ["02_ENGINEERING"]
}
```

Los tipos `learnable_content` son las subcarpetas de `knowledge/` que la Skill procesará. Depositar archivos en subcarpetas no declaradas no produce error, pero la Skill no los estudiará.

---

## `learning/inventory.json` — estructura

```json
{
  "version": "1.0",
  "files": {
    "pdf/norma-iram-4503.pdf": {
      "hash": "a1b2c3d4e5f6...",
      "studied": true,
      "last_studied": "2026-10-14"
    },
    "svg/simbolo-motor.svg": {
      "hash": "f6e5d4c3b2a1...",
      "studied": true,
      "last_studied": "2026-10-14"
    }
  }
}
```

El motor no vuelve a estudiar un archivo si el hash no cambió. Si el archivo fue modificado, el hash cambia y se reestudia automáticamente.

---

## Skills disponibles y sus tipos de conocimiento

| Skill | `learnable_content` |
|---|---|
| `generate-electrical-symbol` | svg, pdf, standards, examples, references |
| `create-electrical-line-diagram` | svg, pdf, dxf, examples, standards, templates |
| `convert-sld-to-mld` | svg, examples, standards |
| `create-pm2-document` | pdf, templates, examples, standards |
| `electrical-dimensioning` | pdf, standards, examples, references |
| `generate-laminas-iram` | svg, dxf, templates, standards, images |
| `get-cotizacion` | pdf, examples, references |
| `memoria-calculos` | pdf, templates, examples, standards |
| `sintesis-memoria` | pdf, templates, examples |

---

## Capacidades funcionales vs. capacitación

Las capacidades funcionales **siempre están disponibles**, incluso si la Skill nunca fue capacitada.

Ejemplo — `create-electrical-line-diagram`:

| Capacidad | Disponible sin capacitación | Mejorada con capacitación |
|---|---|---|
| Generar SVG | Sí — usa biblioteca base IRAM | Sí — usa estilos y símbolos del cliente |
| Exportar PDF | Sí | Sí |
| Exportar DXF | Sí — genera DXF mínimo | Sí — usa plantilla DXF del cliente (`knowledge/dxf/`) |
| Lámina IRAM | Sí — usa plantilla base IRAM | Sí — usa carátula corporativa del cliente (`knowledge/templates/`) |
| Auto-export en estado `ENTREGABLE_AL_CLIENTE` | Sí | Sí |

---

## Requisitos especiales: SLD Generator (`create-electrical-line-diagram`)

### Exportar DXF

```bash
skill export dxf
generate dxf
exportar dxf
```

Disponible en cualquier momento. Si hay plantilla en `knowledge/dxf/`, la usa como base del layout. Si no, genera DXF mínimo con el contenido del SVG convertido a polylines.

Motor:
```bash
python -B .claude/library/core/skill_learn.py create-electrical-line-diagram export dxf <salida.dxf>
```

### Auto-export al estado `ENTREGABLE_AL_CLIENTE`

Cuando el estado del paquete llega a `ENTREGABLE_AL_CLIENTE`, la Skill genera automáticamente **SVG + PDF + DXF** sin intervención del usuario. El DXF es obligatorio.

### Lámina IRAM (capacidad nativa)

La Skill busca plantillas IRAM en este orden:
1. `knowledge/templates/` — plantilla corporativa del cliente (si fue capacitada).
2. Plantilla base IRAM del framework — si no existe plantilla personalizada.

---

## Notas de uso

- Los archivos en `knowledge/` **no se modifican** por el aprendizaje; solo se leen.
- `memory/` es generado automáticamente; no editarlo a mano.
- `cache/` puede borrarse sin problema; se regenera con el próximo `skill learn`.
- El `inventory.json` es la fuente de verdad del estado de aprendizaje; no editarlo manualmente.
- Para migrar el conocimiento a otro equipo: copiar la carpeta `knowledge/` completa y ejecutar `skill learn`.

---

## Portabilidad — qué viaja y qué no

Las skills tienen dos capas con reglas de portabilidad distintas:

| Capa | Qué contiene | ¿Viaja al compartir? | ¿Sobrevive el reset? |
|---|---|---|---|
| **Estructura de la skill** | `SKILL.md`, `skill.json`, `core/`, `standards/`, `templates/`, `outputs/` | **Sí** — es la skill en sí | **Sí** |
| **Conocimiento entrenado** | `knowledge/**`, `learning/inventory.json`, `cache/**`, `memory/**` | **No** — es local al usuario | **Sí** |

### Regla de reset (`iniciar proyecto`)

Al restablecer la plantilla para un nuevo proyecto, **solo se limpia el input del proyecto** (`01-input/99-unclassified/`, `starting-data.md`, entradas del changelog). El directorio `.claude/skills/` no se toca: el conocimiento acumulado en `knowledge/`, `learning/`, `cache/` y `memory/` se conserva íntegro.

### Compartir el framework con otra persona

Usar `.claude/hooks/package-framework.ps1` para generar una copia limpia:

```powershell
# Desde la carpeta raíz del framework:
.\.claude\hooks\package-framework.ps1 -Destination "C:\Ruta\Para\Destinatario"
```

El script copia todo el framework excepto el contenido de entrenamiento. El destinatario recibe las carpetas `knowledge/`, `learning/`, `cache/` y `memory/` vacías, listas para que cargue sus propios archivos y ejecute `skill learn`.

### Migrar el conocimiento a otra máquina

Para llevar el entrenamiento de una máquina a otra (mismo usuario, equipo nuevo):

1. Copiar la carpeta `.claude/skills/<nombre>/knowledge/` completa al destino.
2. En el destino, ejecutar `python -B .claude/library/core/skill_learn.py <skill> learn`.

El resto (`memory/`, `cache/`, `inventory.json`) se regenera automáticamente.

### Control de versiones (git)

El `.gitignore` del framework excluye el contenido de entrenamiento:

```
.claude/skills/*/knowledge/**
.claude/skills/*/learning/inventory.json
.claude/skills/*/cache/**
.claude/skills/*/memory/**
```

Un `git clone` del repositorio entrega la estructura de skills sin conocimiento previo — comportamiento equivalente al script de empaquetado.
