# Dependencias e impacto

> Archivo generado por `python tools/build/impact_map.py` a partir del código (importaciones y referencias a módulos del motor). No se edita a mano: el gate avisa si quedó desactualizado.

Cómo leerlo: **Usa** = de qué depende la unidad; **Lo usan** = quién se rompe o cambia si esta unidad cambia; **Impacto** = todo lo que alcanza, directa o indirectamente.

## Motores

| Unidad | Usa | Lo usan | Impacto si la modificas |
|---|---|---|---|
| `aea90364` | — | `backend.catalogs`, `backend.norms`, `backend.sld`, `drawing`, `mld`, `sld`, `standards` | `backend.admin`, `backend.app`, `backend.catalogs`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.norms`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld`, `standards` |
| `arch` | — | `backend.layout` | `backend.app`, `backend.coordination`, `backend.layout` |
| `documents` | — | — | — |
| `drawing` | `aea90364`, `dxf`, `mld`, `sld`, `titleblock` | `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld` | `backend.app`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld` |
| `dxf` | — | `backend.catalogs`, `backend.layout`, `drawing`, `mld`, `plan`, `sld`, `titleblock` | `backend.admin`, `backend.app`, `backend.catalogs`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `plan`, `sld`, `titleblock` |
| `mld` | `aea90364`, `dxf`, `symbols`, `titleblock` | `drawing` | `backend.app`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing` |
| `plan` | `dxf` | `backend.coordination`, `backend.layout` | `backend.app`, `backend.coordination`, `backend.layout` |
| `rules` | — | `backend.knowledge` | `backend.admin`, `backend.app`, `backend.knowledge` |
| `sld` | `aea90364`, `dxf`, `symbols`, `titleblock` | `drawing` | `backend.app`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing` |
| `standards` | `aea90364` | — | — |
| `symbols` | — | `backend.admin`, `backend.catalogs`, `mld`, `sld` | `backend.admin`, `backend.app`, `backend.catalogs`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld` |
| `titleblock` | `dxf` | `drawing`, `mld`, `sld` | `backend.app`, `backend.coordination`, `backend.issuing`, `backend.layout`, `backend.reporting`, `backend.sld`, `drawing`, `mld`, `sld` |

## Módulos del backend

| Módulo | Usa | Lo usan |
|---|---|---|
| `backend.admin` | `backend.catalogs`, `backend.core`, `backend.deliverables`, `backend.identity`, `backend.knowledge`, `backend.projects`, `symbols` | `backend.app` |
| `backend.app` | `backend.admin`, `backend.backlog`, `backend.catalogs`, `backend.coordination`, `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` | — |
| `backend.backlog` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.catalogs` | `aea90364`, `backend.core`, `backend.identity`, `backend.projects`, `dxf`, `symbols` | `backend.admin`, `backend.app`, `backend.layout`, `backend.sld` |
| `backend.coordination` | `backend.core`, `backend.identity`, `backend.layout`, `backend.projects`, `plan` | `backend.app` |
| `backend.core` | — | `backend.admin`, `backend.app`, `backend.backlog`, `backend.catalogs`, `backend.coordination`, `backend.deliverables`, `backend.engineering`, `backend.identity`, `backend.intake`, `backend.issuing`, `backend.knowledge`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.deliverables` | `backend.core`, `backend.projects` | `backend.admin`, `backend.app`, `backend.issuing`, `backend.management`, `backend.reporting` |
| `backend.engineering` | `backend.core`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.identity` | `backend.core` | `backend.admin`, `backend.app`, `backend.catalogs`, `backend.coordination`, `backend.layout`, `backend.masterdata`, `backend.norms`, `backend.projects`, `backend.registers`, `backend.reporting`, `backend.requirements` |
| `backend.intake` | `backend.core`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting`, `backend.requirements` |
| `backend.issuing` | `backend.core`, `backend.deliverables`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `drawing` | `backend.app` |
| `backend.knowledge` | `backend.core`, `rules` | `backend.admin`, `backend.app` |
| `backend.layout` | `arch`, `backend.catalogs`, `backend.core`, `backend.identity`, `backend.projects`, `backend.sld`, `drawing`, `dxf`, `plan` | `backend.app`, `backend.coordination` |
| `backend.management` | `backend.core`, `backend.deliverables`, `backend.intake`, `backend.projects`, `backend.requirements` | `backend.app`, `backend.reporting` |
| `backend.masterdata` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.issuing`, `backend.sld` |
| `backend.norms` | `aea90364`, `backend.core`, `backend.identity` | `backend.app` |
| `backend.projects` | `backend.core`, `backend.identity` | `backend.admin`, `backend.app`, `backend.backlog`, `backend.catalogs`, `backend.coordination`, `backend.deliverables`, `backend.engineering`, `backend.intake`, `backend.issuing`, `backend.layout`, `backend.management`, `backend.masterdata`, `backend.registers`, `backend.reporting`, `backend.requirements`, `backend.schedule`, `backend.sld`, `backend.wbs` |
| `backend.registers` | `backend.core`, `backend.identity`, `backend.projects` | `backend.app`, `backend.reporting` |
| `backend.reporting` | `backend.backlog`, `backend.core`, `backend.deliverables`, `backend.identity`, `backend.intake`, `backend.management`, `backend.projects`, `backend.registers`, `backend.requirements`, `backend.schedule`, `backend.wbs`, `drawing` | `backend.app` |
| `backend.requirements` | `backend.core`, `backend.identity`, `backend.intake`, `backend.projects` | `backend.app`, `backend.management`, `backend.reporting` |
| `backend.schedule` | `backend.core`, `backend.projects`, `backend.wbs` | `backend.app`, `backend.reporting` |
| `backend.sld` | `aea90364`, `backend.catalogs`, `backend.core`, `backend.engineering`, `backend.masterdata`, `backend.projects`, `drawing` | `backend.app`, `backend.layout` |
| `backend.wbs` | `backend.core`, `backend.projects` | `backend.app`, `backend.backlog`, `backend.reporting`, `backend.schedule` |

## Paquetes externos por unidad del motor

Lo declarado en `pyproject.toml` frente a lo que el código importa de verdad.

| Unidad | Importa | Declarado | Falta declarar |
|---|---|---|---|
| `aea90364` | `openpyxl` | `openpyxl` | — |
| `arch` | `ezdxf`, `numpy`, `pillow`, `pypdfium2` | `ezdxf`, `numpy`, `pillow`, `pypdfium2` | — |
| `documents` | `playwright`, `pypdf`, `python-docx` | `playwright`, `pypdf`, `python-docx` | — |
| `drawing` | `ezdxf`, `matplotlib`, `openpyxl` | `epc-aea90364`, `epc-mld`, `epc-sld`, `epc-titleblock`, `ezdxf`, `matplotlib`, `openpyxl` | — |
| `dxf` | `ezdxf`, `lxml`, `shapely`, `svgelements`, `vtracer` | `ezdxf`, `lxml`, `shapely`, `svgelements`, `vtracer` | — |
| `mld` | `lxml` | `epc-aea90364`, `epc-dxf`, `epc-symbols`, `epc-titleblock`, `lxml` | — |
| `plan` | `ezdxf` | `epc-dxf`, `ezdxf` | — |
| `rules` | — | — | — |
| `sld` | `cairosvg`, `lxml`, `openpyxl` | `cairosvg`, `epc-aea90364`, `epc-dxf`, `epc-symbols`, `epc-titleblock`, `lxml`, `openpyxl` | — |
| `standards` | `jsonschema`, `pypdf`, `pypdfium2` | `jsonschema`, `pillow`, `pypdf`, `pypdfium2` | — |
| `symbols` | — | — | — |
| `titleblock` | — | `epc-dxf` | — |

## Plugins

| Plugin | Empaqueta (motor) | Requiere (plugins) | Lo requieren |
|---|---|---|---|
| `aea-calc` | `aea90364` | — | `board-design`, `mld`, `sld`, `standard-ingest` |
| `board-design` | `aea90364`, `drawing`, `dxf`, `mld`, `sld`, `symbols`, `titleblock` | `aea-calc`, `dxf-output`, `iram-titleblock`, `mld`, `sld` | — |
| `doc-quality` | `documents` | — | `pm2-docs`, `spec-writer` |
| `dxf-output` | `dxf` | — | `board-design`, `iram-titleblock`, `mld`, `plan-drawing`, `sld` |
| `equipment-catalog` | — | — | `procurement` |
| `iec-symbols` | `symbols` | — | `mld`, `sld` |
| `intake-analysis` | — | — | — |
| `iram-titleblock` | `dxf`, `titleblock` | `dxf-output` | `board-design`, `mld`, `sld` |
| `mld` | `aea90364`, `dxf`, `mld`, `symbols`, `titleblock` | `aea-calc`, `dxf-output`, `iec-symbols`, `iram-titleblock` | `board-design` |
| `plan-drawing` | `dxf`, `plan` | `dxf-output` | — |
| `pm2-docs` | `documents` | `doc-quality` | — |
| `procurement` | — | `equipment-catalog` | — |
| `sld` | `aea90364`, `dxf`, `sld`, `symbols`, `titleblock` | `aea-calc`, `dxf-output`, `iec-symbols`, `iram-titleblock` | `board-design` |
| `spec-writer` | `documents` | `doc-quality` | — |
| `standard-ingest` | `aea90364`, `rules`, `standards` | `aea-calc` | — |
