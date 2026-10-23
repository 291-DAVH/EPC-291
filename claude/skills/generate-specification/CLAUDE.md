# generar-pliego — Naming & Format Rules

These rules are **permanent**. Apply them in every session without exception.
Never revert to Spanish names, SCREAMING_CASE, or numbered Spanish titles.

---

## File & Folder Naming

| Rule | ✓ Correct | ✗ Wrong |
|------|-----------|---------|
| All file and folder names in **kebab-case** | `05a-lv-switchboards.md` | `05A_TABLEROS_BT.md` |
| Language: **English** | `civil/blocks/` | `templates_civil/bloques/` |
| No accented characters in filenames | `fire-detection/` | `deteccion-de-incendios/` |
| Scripts: kebab-case `.py` | `assemble-spec.py` | `armar_pliego.py` |
| Outputs: kebab-case `.md` | `spec-electrical.md` | `PLIEGO_ELECTRICO.md` |
| Temp/internal scripts: prefix `_` | `_refactor.py` | `refactor.py` |

---

## Directory Structure (generar-pliego skill)

```
generar-pliego/
├── SKILL.md                        ← skill definition (Spanish content OK)
├── CLAUDE.md                       ← this file — naming rules
├── assemble-spec.py                ← offline block assembler
├── skill.json
├── cache/
├── core/
├── knowledge/
│   ├── pdf/                        ← source PDFs (kebab-case names)
│   ├── extracted/                  ← extracted section-4 text (kebab-case .md)
│   ├── assembled/                  ← output specs assembled by assemble-spec.py
│   ├── templates/
│   │   ├── template-ford-electrical-reference.md
│   │   ├── electrical/             ← electrical blocks (flat, no subdir)
│   │   │   ├── 00-project-data.md
│   │   │   ├── 01-descriptive-report.md
│   │   │   └── ...
│   │   ├── civil/blocks/
│   │   ├── fire-suppression/blocks/
│   │   ├── fire-detection/blocks/
│   │   ├── hvac/blocks/
│   │   └── thermomechanical/blocks/
│   ├── examples/
│   ├── references/
│   └── standards/
├── learning/
├── memory/
├── outputs/
├── standards/
└── templates/
```

---

## Block File Naming Pattern

```
<nn[x]>-<english-slug>.md
```

- `00` through `09` for block number
- Optional letter suffix for sub-blocks (`05a`, `05b`, ...)
- Slug: lowercase English, hyphens only, no underscores, no accents

| Block | File |
|-------|------|
| Project data | `00-project-data.md` |
| Descriptive report | `01-descriptive-report.md` |
| Standards & codes | `02-standards-codes.md` |
| Detail engineering | `03-detail-engineering.md` |
| General conditions | `04-general-conditions.md` |
| Testing & commissioning | `06-testing-commissioning.md` |
| As-built docs | `07-asbuilt-docs.md` |
| Training | `08-training.md` |
| Responsibilities | `09-responsibilities.md` |

---

## Variables in Block Content

Use `{{UPPER_SNAKE_CASE}}` for all project-specific placeholders:

```
{{PROJECT_NAME}}   {{CONTRACT_NO}}   {{PLANT_SITE}}
{{AREA_SECTOR}}    {{SITE_MANAGER}}  {{ISSUE_DATE}}
{{REV}}            {{SUPPLY_VOLTAGE}} {{MV_VOLTAGE}}
```

---

## Discipline Keys (used by assemble-spec.py)

| Key | Discipline |
|-----|-----------|
| `electrical` | Electrical (BT + MT) |
| `civil` | Civil |
| `fire-suppression` | Fire Suppression (combate incendios) |
| `fire-detection` | Fire Detection (detección incendios) |
| `hvac` | HVAC |
| `thermomechanical` | Thermomechanical (termomecánica) |

---

## Markdown Style in Blocks

- Headings: `## BLOCK NN — TITLE` (English, uppercase)
- Metadata comment: `<!-- BLOCK: NN | USAGE: ALWAYS|CONDITIONAL -->`
- Tables: GFM pipe tables
- Lists: `-` bullets (not `*`)
- No manual numbering in headings
- No inline HTML except `<!-- ... -->` metadata comments

---

## What NOT to Do

- Do **not** rename files to Spanish
- Do **not** use `SCREAMING_SNAKE_CASE` for filenames
- Do **not** create new files with accented characters
- Do **not** use PascalCase or camelCase for filenames
- Do **not** add `.txt` extensions to markdown content
