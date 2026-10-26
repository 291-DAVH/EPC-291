# Dependencias e impacto

> Archivo generado por `python tools/build/impact_map.py` a partir del código (importaciones y referencias a módulos del motor). No se edita a mano: el gate avisa si quedó desactualizado.

Cómo leerlo: **Usa** = de qué depende la unidad; **Lo usan** = quién se rompe o cambia si esta unidad cambia; **Impacto** = todo lo que alcanza, directa o indirectamente.

## Motores

| Unidad | Usa | Lo usan | Impacto si la modificas |
|---|---|---|---|
| `calc` | — | `backend.norms`, `backend.sld`, `drawing`, `mld`, `sld`, `standards` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.norms`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld`, `standards` |
| `documents` | — | — | — |
| `drawing` | `calc`, `mld`, `sld` | `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld` |
| `dxf` | — | `backend.admin`, `plan`, `sld` | `backend.admin`, `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `plan`, `sld` |
| `mld` | `calc`, `sld`, `symbols` | `drawing` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing` |
| `plan` | `dxf` | `backend.layout` | `backend.app`, `backend.layout` |
| `rules` | — | `backend.knowledge` | `backend.admin`, `backend.app`, `backend.knowledge` |
| `sld` | `calc`, `dxf`, `symbols`, `titleblock` | `drawing`, `mld` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld` |
| `standards` | `calc` | — | — |
| `symbols` | — | `mld`, `sld` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld` |
| `titleblock` | — | `sld` | `backend.app`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld` |

## Módulos del backend

| Módulo | Usa | Lo usan |
|---|---|---|
| `backend.admin` | `backend.core`, `backend.deliverables`, `backend.knowledge`, `backend.projects`, `dxf` | `backend.app` |
| `backend.app` | `backend.admin`, `backend.backlog`, `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` | — |
| `backend.backlog` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.core` | — | `backend.admin`, `backend.app`, `backend.backlog`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.deliverables` | `backend.core`, `backend.projects` | `backend.admin`, `backend.app`, `backend.issuing`, `backend.management`, `backend.reporting` |
| `backend.engineering` | `backend.core`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.identity` | `backend.core` | `backend.app`, `backend.layout`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements` |
| `backend.intake` | `backend.core`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting`, `backend.requirements` |
| `backend.issuing` | `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `drawing` | `backend.app` |
| `backend.knowledge` | `backend.core`, `rules` | `backend.admin`, `backend.app` |
| `backend.layout` | `backend.core`, `backend.identity`, `backend.projects`, `backend.sld`, `drawing`, `plan` | `backend.app` |
| `backend.management` | `backend.core`, `backend.deliverables`, `backend.intake`, `backend.projects`, `backend.requirements` | `backend.app`, `backend.reporting` |
| `backend.masterdata` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.norms` | `backend.core`, `backend.identity`, `calc` | `backend.app` |
| `backend.projects` | `backend.core`, `backend.identity` | `backend.admin`, `backend.app`, `backend.backlog`, `backend.deliverables`, `backend.engineering`, `backend.intake`, `backend.issuing`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.registers` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.reporting` |
| `backend.reporting` | `backend.backlog`, `backend.core`, `backend.deliverables`, `backend.identity`, `backend.intake`, `backend.management`, `backend.projects`, `backend.registers`, `backend.requirements`, `backend.schedule`, `backend.wbs`, `drawing` | `backend.app` |
| `backend.requirements` | `backend.core`, `backend.identity`, `backend.intake`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting` |
| `backend.schedule` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.sld` | `backend.core`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `calc`, `drawing` | `backend.app`, `backend.layout` |
| `backend.wbs` | `backend.core`, `backend.projects` | `backend.app`, `backend.backlog`, `backend.reporting`, `backend.schedule` |

## Paquetes externos por unidad del motor

Lo declarado en `pyproject.toml` frente a lo que el código importa de verdad.

| Unidad | Importa | Declarado | Falta declarar |
|---|---|---|---|
| `calc` | `openpyxl` | `openpyxl` | — |
| `documents` | `playwright`, `pypdf`, `python-docx` | `playwright`, `pypdf`, `python-docx` | — |
| `drawing` | `ezdxf`, `matplotlib`, `openpyxl` | `epc-calc`, `epc-mld`, `epc-sld`, `epc-titleblock`, `ezdxf`, `matplotlib`, `openpyxl` | — |
| `dxf` | — | `ezdxf` | — |
| `mld` | `lxml` | `epc-calc`, `epc-dxf`, `epc-sld`, `epc-symbols`, `ezdxf`, `lxml` | — |
| `plan` | `ezdxf` | `epc-dxf`, `ezdxf` | — |
| `rules` | — | — | — |
| `sld` | `cairosvg`, `ezdxf`, `lxml`, `openpyxl`, `shapely`, `svgelements` | `cairosvg`, `epc-calc`, `epc-dxf`, `epc-symbols`, `epc-titleblock`, `ezdxf`, `lxml`, `openpyxl`, `shapely`, `svgelements` | — |
| `standards` | `jsonschema`, `pypdf`, `pypdfium2` | `jsonschema`, `pillow`, `pypdf`, `pypdfium2` | — |
| `symbols` | — | — | — |
| `titleblock` | `ezdxf`, `openpyxl`, `shapely`, `svgelements`, `vtracer` | `ezdxf`, `lxml`, `openpyxl`, `shapely`, `svgelements`, `vtracer` | — |

## Plugins

| Plugin | Empaqueta (motor) | Requiere (plugins) | Lo requieren |
|---|---|---|---|
| `aea-calc` | `calc` | — | `board-design`, `mld`, `sld`, `standard-ingest` |
| `board-design` | `calc`, `drawing`, `dxf`, `mld`, `sld`, `symbols`, `titleblock` | `aea-calc`, `mld`, `sld` | — |
| `doc-quality` | `documents` | — | `pm2-docs`, `spec-writer` |
| `dxf-output` | `dxf` | — | `plan-drawing`, `sld` |
| `equipment-catalog` | — | — | `procurement` |
| `iec-symbols` | `symbols` | — | `mld`, `sld` |
| `intake-analysis` | — | — | — |
| `iram-titleblock` | `titleblock` | — | `sld` |
| `mld` | `calc`, `dxf`, `mld`, `sld`, `symbols`, `titleblock` | `aea-calc`, `iec-symbols`, `sld` | `board-design` |
| `plan-drawing` | `dxf`, `plan` | `dxf-output` | — |
| `pm2-docs` | `documents` | `doc-quality` | — |
| `procurement` | — | `equipment-catalog` | — |
| `sld` | `calc`, `dxf`, `sld`, `symbols`, `titleblock` | `aea-calc`, `dxf-output`, `iec-symbols`, `iram-titleblock` | `board-design`, `mld` |
| `spec-writer` | `documents` | `doc-quality` | — |
| `standard-ingest` | `calc`, `rules`, `standards` | `aea-calc` | — |
