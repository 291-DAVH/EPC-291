# Dependencias e impacto

> Archivo generado por `python tools/build/impact_map.py` a partir del código (importaciones y referencias a módulos del motor). No se edita a mano: el gate avisa si quedó desactualizado.

Cómo leerlo: **Usa** = de qué depende la unidad; **Lo usan** = quién se rompe o cambia si esta unidad cambia; **Impacto** = todo lo que alcanza, directa o indirectamente.

## Motores

| Unidad | Usa | Lo usan | Impacto si la modificas |
|---|---|---|---|
| `calc` | — | `backend.norms`, `backend.sld`, `drawing.board_design`, `drawing.mld`, `drawing.sld`, `standards` | `backend.app`, `backend.layout`, `backend.norms`, `backend.sld`, `drawing.board_design`, `drawing.mld`, `drawing.sld`, `standards` |
| `documents` | — | — | — |
| `drawing.board_design` | `calc`, `drawing.export`, `drawing.mld`, `drawing.sld` | `backend.sld` | `backend.app`, `backend.layout`, `backend.sld` |
| `drawing.export` | — | `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing.board_design` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing.board_design` |
| `drawing.mld` | `calc`, `drawing.sld`, `drawing.symbols` | `drawing.board_design` | `backend.app`, `backend.layout`, `backend.sld`, `drawing.board_design` |
| `drawing.sld` | `calc`, `drawing.symbols`, `drawing.titleblock` | `drawing.board_design`, `drawing.mld` | `backend.app`, `backend.layout`, `backend.sld`, `drawing.board_design`, `drawing.mld` |
| `drawing.symbols` | — | `drawing.mld`, `drawing.sld` | `backend.app`, `backend.layout`, `backend.sld`, `drawing.board_design`, `drawing.mld`, `drawing.sld` |
| `drawing.titleblock` | — | `drawing.sld` | `backend.app`, `backend.layout`, `backend.sld`, `drawing.board_design`, `drawing.mld`, `drawing.sld` |
| `plan` | — | `backend.layout` | `backend.app`, `backend.layout` |
| `rules` | — | `backend.knowledge` | `backend.admin`, `backend.app`, `backend.knowledge` |
| `standards` | `calc` | — | — |

## Módulos del backend

| Módulo | Usa | Lo usan |
|---|---|---|
| `backend.admin` | `backend.core`, `backend.deliverables`, `backend.knowledge`, `backend.projects` | `backend.app` |
| `backend.app` | `backend.admin`, `backend.backlog`, `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` | — |
| `backend.backlog` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.core` | — | `backend.admin`, `backend.app`, `backend.backlog`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.deliverables` | `backend.core`, `backend.projects` | `backend.admin`, `backend.app`, `backend.issuing`, `backend.management`, `backend.reporting` |
| `backend.engineering` | `backend.core`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.identity` | `backend.core` | `backend.app`, `backend.layout`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements` |
| `backend.intake` | `backend.core`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting`, `backend.requirements` |
| `backend.issuing` | `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `drawing.export` | `backend.app` |
| `backend.knowledge` | `backend.core`, `rules` | `backend.admin`, `backend.app` |
| `backend.layout` | `backend.core`, `backend.identity`, `backend.projects`, `backend.sld`, `drawing.export`, `plan` | `backend.app` |
| `backend.management` | `backend.core`, `backend.deliverables`, `backend.intake`, `backend.projects`, `backend.requirements` | `backend.app`, `backend.reporting` |
| `backend.masterdata` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.norms` | `backend.core`, `backend.identity`, `calc` | `backend.app` |
| `backend.projects` | `backend.core`, `backend.identity` | `backend.admin`, `backend.app`, `backend.backlog`, `backend.deliverables`, `backend.engineering`, `backend.intake`, `backend.issuing`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.registers` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.reporting` |
| `backend.reporting` | `backend.backlog`, `backend.core`, `backend.deliverables`, `backend.identity`, `backend.intake`, `backend.management`, `backend.projects`, `backend.registers`, `backend.requirements`, `backend.schedule`, `backend.wbs`, `drawing.export` | `backend.app` |
| `backend.requirements` | `backend.core`, `backend.identity`, `backend.intake`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting` |
| `backend.schedule` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.sld` | `backend.core`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `calc`, `drawing.board_design`, `drawing.export` | `backend.app`, `backend.layout` |
| `backend.wbs` | `backend.core`, `backend.projects` | `backend.app`, `backend.backlog`, `backend.reporting`, `backend.schedule` |

## Paquetes externos por unidad del motor

Lo declarado en `pyproject.toml` frente a lo que el código importa de verdad.

| Unidad | Importa | Declarado | Falta declarar |
|---|---|---|---|
| `calc` | `openpyxl` | `openpyxl` | — |
| `documents` | `docx`, `playwright`, `pypdf` | — | `docx`, `playwright`, `pypdf` |
| `drawing.board_design` | `openpyxl` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | — |
| `drawing.export` | `ezdxf`, `matplotlib` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | — |
| `drawing.mld` | `lxml` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | — |
| `drawing.sld` | `cairosvg`, `ezdxf`, `lxml`, `openpyxl`, `shapely`, `svgelements` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | `cairosvg` |
| `drawing.symbols` | — | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | — |
| `drawing.titleblock` | `ezdxf`, `openpyxl`, `shapely`, `svgelements`, `vtracer` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | `vtracer` |
| `plan` | `ezdxf` | `epc-calc`, `ezdxf`, `lxml`, `matplotlib`, `openpyxl`, `shapely`, `svgelements` | — |
| `rules` | — | — | — |
| `standards` | `jsonschema`, `pypdf`, `pypdfium2` | `jsonschema`, `pypdf` | `pypdfium2` |

## Plugins

| Plugin | Empaqueta (motor) | Requiere (plugins) | Lo requieren |
|---|---|---|---|
| `aea-calc` | `calc` | — | `board-design`, `mld`, `sld` |
| `board-design` | `calc`, `drawing` | `aea-calc`, `iec-symbols`, `iram-titleblock`, `mld`, `sld` | — |
| `doc-quality` | `documents` | — | `pm2-docs`, `spec-writer` |
| `equipment-catalog` | — | — | `procurement` |
| `iec-symbols` | `drawing` | — | `board-design`, `mld`, `sld` |
| `intake-analysis` | — | — | — |
| `iram-titleblock` | `drawing` | — | `board-design`, `mld`, `sld` |
| `mld` | `calc`, `drawing` | `aea-calc`, `iec-symbols`, `iram-titleblock`, `sld` | `board-design` |
| `pm2-docs` | `documents` | `doc-quality` | — |
| `procurement` | — | `equipment-catalog` | — |
| `sld` | `calc`, `drawing` | `aea-calc`, `iec-symbols`, `iram-titleblock` | `board-design`, `mld` |
| `spec-writer` | `documents` | `doc-quality` | — |
| `standard-ingest` | `rules`, `standards` | — | — |
