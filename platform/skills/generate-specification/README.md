# generar-pliego — Wiki

Skill for generating Ford technical specifications (pliegos) from modular LEGO blocks.

---

## Quick Start

```bash
# 1. Open 00-project-data.md for your discipline and tick [x] the blocks that apply
# 2. Run the assembler:
python3 assemble-spec.py electrical --out spec-project-name.md

# 3. Open knowledge/assembled/spec-project-name.md and replace {{VARIABLES}}
```

---

## File Structure

```
generar-pliego/
├── SKILL.md                         ← Claude skill definition
├── CLAUDE.md                        ← Naming & format rules (read first)
├── README.md                        ← This file
├── assemble-spec.py                 ← Block assembler (offline)
│
└── knowledge/
    ├── pdf/                         ← Source PDFs (ford-pliego-*.pdf)
    ├── extracted/                   ← Extracted Section 4 text (ford-pliego-*.md)
    ├── assembled/                   ← Output specs ready for editing
    └── templates/
        ├── template-ford-electrical-reference.md   ← Full reference (monolithic)
        ├── electrical/              ← 17 blocks (flat)
        ├── civil/blocks/            ← 13 blocks
        ├── fire-suppression/blocks/ ← 13 blocks
        ├── fire-detection/blocks/   ← 12 blocks
        ├── hvac/blocks/             ← 13 blocks
        └── thermomechanical/blocks/ ← 11 blocks
```

---

## Block Map

| Block | File | Usage |
|-------|------|-------|
| 00 | `00-project-data.md` | **ALWAYS** — project fields + checklist |
| 01 | `01-descriptive-report.md` | **ALWAYS** |
| 02 | `02-standards-codes.md` | **ALWAYS** |
| 03 | `03-detail-engineering.md` | **ALWAYS** |
| 04 | `04-general-conditions.md` | **ALWAYS** |
| 05a–05h | discipline-specific blocks | IF APPLICABLE |
| 06 | `06-testing-commissioning.md` | **ALWAYS** |
| 07 | `07-asbuilt-docs.md` | **ALWAYS** |
| 08 | `08-training.md` | IF APPLICABLE |
| 09 | `09-responsibilities.md` | **ALWAYS** |

---

## Disciplines & Discipline-Specific Blocks

### Electrical (`electrical/`)
| Block | File | Description |
|-------|------|-------------|
| 05a | `05a-lv-switchboards.md` | LV switchboards |
| 05b | `05b-cables-conductors.md` | Cables & conductors |
| 05c | `05c-cable-trays.md` | Cable trays |
| 05d | `05d-underground-conduits.md` | Underground conduits / below road |
| 05e | `05e-grounding.md` | Grounding |
| 05f | `05f-lighting.md` | Lighting |
| 05g | `05g-power-outlets.md` | Power outlets & services |
| 05h | `05h-medium-voltage.md` | Medium voltage |

### Civil (`civil/blocks/`)
| Block | File |
|-------|------|
| 05a | `05a-preliminary-works.md` |
| 05b | `05b-concrete.md` |
| 05c | `05c-foundations.md` |
| 05d | `05d-pavements-exterior.md` |

### Fire Suppression (`fire-suppression/blocks/`)
| Block | File |
|-------|------|
| 05a | `05a-hydraulic-network.md` |
| 05b | `05b-sprinklers.md` |
| 05c | `05c-fire-hose-cabinets.md` |
| 05d | `05d-fire-testing.md` |

### Fire Detection (`fire-detection/blocks/`)
| Block | File |
|-------|------|
| 05a | `05a-facp.md` |
| 05b | `05b-detection-devices.md` |
| 05c | `05c-detection-conduits.md` |

### HVAC (`hvac/blocks/`)
| Block | File |
|-------|------|
| 05a | `05a-hvac-equipment.md` |
| 05b | `05b-ducts-diffusers.md` |
| 05c | `05c-hvac-panels.md` |
| 05d | `05d-hvac-testing.md` |

### Thermomechanical (`thermomechanical/blocks/`)
| Block | File |
|-------|------|
| 05a | `05a-mechanical-ventilation.md` |
| 05b | `05b-thermomechanical-equipment.md` |

---

## Naming Convention (enforced by CLAUDE.md)

- All filenames: **kebab-case English** (`05a-lv-switchboards.md`)
- No Spanish in filenames, no underscores, no accents
- Variables inside blocks: `{{UPPER_SNAKE_CASE}}`
- Assembled outputs go to `knowledge/assembled/`

---

## Knowledge Base

Extracted source texts from 27 Ford pliegos are in `knowledge/extracted/`:

| Discipline | Files |
|------------|-------|
| Electrical | `ford-pliego-electrico-001..010.md` |
| Civil | `ford-pliego-civil-001..003.md` |
| Fire Suppression | `ford-pliego-combate-de-incendios-001..005.md` |
| Fire Detection | `ford-pliego-deteccion-de-incendios-001..004.md` |
| HVAC | `ford-pliego-hvac-001..003.md` |
| Thermomechanical | `ford-pliego-termomecanica-001..002.md` |

Only Section 4 (Especificaciones Técnicas Particulares) is extracted.
Sections 1–3 and annexes are client-provided and never change.
