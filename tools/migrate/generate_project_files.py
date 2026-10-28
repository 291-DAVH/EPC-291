#!/usr/bin/env python3
"""Generate READMEs, dependency docs and config files for the restructured platform (run from epc-workspace/)."""
HISTORICAL (2026-10-23): one-off migration script for the old `platform/` layout. Do not run it again; kept for traceability.
import json
import pathlib

W = pathlib.Path(__file__).resolve().parents[3]
PF = W / "platform"


def w(p, t):
    p = pathlib.Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(t, encoding="utf-8")


reg = json.loads((PF / "hub/registry.json").read_text(encoding="utf-8"))

w(W / ".gitignore", """# Workspace-level safety net (the workspace itself is not a repository; platform/ is)
dev-knowledge/
_legacy/
projects/*/
!projects/_template/
platform/.venv/
platform/dist/
""")
w(W / "dev-knowledge/.gitignore", "*\n!.gitignore\n!README.md\n")
w(PF / ".editorconfig", "root = true\n[*]\ncharset = utf-8\nend_of_line = lf\ninsert_final_newline = true\nindent_style = space\nindent_size = 4\n[*.{json,yml,yaml,md}]\nindent_size = 2\n[*.{bat,ps1}]\nend_of_line = crlf\n")
w(PF / ".gitattributes", "* text=auto eol=lf\n*.dxf text eol=lf\n*.svg text eol=lf\n*.xlsx binary\n*.docx binary\n*.png binary\n*.plugin binary\n")
w(PF / "CHANGELOG.md", """# Changelog

## 0.1.0 - 2026-10-23
- Restructured the legacy folders into one platform: `hub/` (10 plugins), `skills/` (12 skills), `core/workflow`, `methodologies/pm2`, `jurisdictions/AR`, `agents/`.
- Plugins resolve each other from the hub; `vendor/*.plugin` copies removed.
- `sld` 0.1.1: compatible with `iec-symbols` >= 0.4.14 file naming; `cairosvg` optional.
- Study and copyrighted material moved to `dev-knowledge/` (outside git).
- See `docs/MIGRATION_LOG.md` and `docs/MIGRATION_INVENTORY.md`.
""")
w(PF / "CONTRIBUTING.md", """# Contributing

1. Plugins live only in `hub/<id>/`; skills only in `skills/<id>/`. Plugins govern their skills.
2. Replaced a plugin or skill? Run:
   ```
   python tools/ci/check_skill_conflicts.py --env production
   python tools/build/epc_build.py registry
   ```
3. Never commit PDF/DWG or anything from `dev-knowledge/`. Enable the hook: `git config core.hooksPath tools/hooks`.
4. Product content (code, schemas, ids, templates, prompts) is English. Claude explains to the user in Spanish.
5. Bump `version` in `plugin.json` and add a `CHANGELOG.md` line for every behavior change.
""")
w(PF / "pyproject.toml", """[project]
name = "epc-platform"
version = "0.1.0"
description = "Plugin-based automated EPC engineering framework"
requires-python = ">=3.10"
dependencies = []   # core is stdlib only

[project.optional-dependencies]
# Per-plugin extras (the plugin.json "python.requires" field is the source of truth)
calc     = ["openpyxl>=3.1"]
drawing  = ["openpyxl>=3.1", "lxml", "ezdxf", "svgelements", "shapely"]
rules    = ["pypdf", "pypdfium2", "pillow", "jsonschema"]   # standard-ingest; the rules engine itself is stdlib only
previews = ["cairosvg", "pillow"]          # needs the Cairo library on Windows; optional
dev      = ["pytest>=7.4", "pytest-cov>=4.1"]

[tool.pytest.ini_options]
testpaths = ["hub", "tools"]
python_files = "test_*.py"

# System tools (not pip packages), optional: pandoc (md -> docx), libreoffice/soffice (Office -> PDF),
# poppler-utils (pdftotext, pdftoppm).
""")
w(PF / "requirements.txt", "# Minimum to run the drawing + calculation plugins\nopenpyxl>=3.1\nlxml\nezdxf\nsvgelements\nshapely\n")
w(PF / "requirements-dev.txt", "-r requirements.txt\npytest>=7.4\npytest-cov>=4.1\n")

rows = "\n".join(
    f"| [`{k}`](hub/{k}/) | {v['version']} | {v['kind']} | {v['status']} | {', '.join(v['requires']) or '-'} | {', '.join(v['skills']) or '-'} |"
    for k, v in reg["plugins"].items())
w(PF / "README.md", """# EPC Platform

Plugin-based framework for automated EPC engineering (Engineering, Procurement, Construction). Built like Lego: small plugins with explicit contracts, governed by a small core. Runs today inside Claude Code; the same engine is meant to run on the web (Python + React) and on the desktop.

## Layout

```
platform/
├─ hub/             ALL plugins (single source of truth, one folder per plugin) + registry.json
├─ skills/          ALL skills (plugins govern them; plugin copy wins on duplicates)
├─ core/workflow/   workflow engine seed: state rules, transition scripts, commands
├─ core/rules/      rules engine (epc_rules): load rules.json per jurisdiction, query, check
├─ methodologies/   pm2 (default), pmi, custom: swappable management packs
├─ jurisdictions/   country packs (AR active): standards -> rules.json, drawing conventions
├─ agents/          specialist agents (document writer, auditors, ...)
├─ schemas/         JSON schemas: plugin, rules, deliverable policy
├─ i18n/            UI/document strings (en, es)
├─ apps/            api (FastAPI) and web (React) running; cli, mcp, desktop not built yet
├─ tools/           build, ci, hooks, migrate, dev
├─ tests/golden/    reference inputs/outputs
└─ docs/            plan, architecture, migration notes
```

Siblings of this repository (never inside it): `../dev-knowledge/` (standards, third-party reports, study material, never versioned) and `../projects/` (client projects: `workspace/` editable, `deliverables/` client-facing).

## Plugins

| Plugin | Version | Kind | Status | Requires | Skills |
|---|---|---|---|---|---|
""" + rows + """

## Quick start (Windows)

```
python -m venv .venv
.venv\\Scripts\\python -m pip install -r requirements-dev.txt
.venv\\Scripts\\python tools\\build\\epc_build.py registry       # validate hub + skills
.venv\\Scripts\\python tools\\ci\\check_skill_conflicts.py        # duplicate / orphan skills
.venv\\Scripts\\python tools\\build\\epc_build.py package all     # dist\\<id>-<ver>.plugin for Claude Code
git config core.hooksPath tools/hooks                          # block PDF/DWG commits
```

Generate a single-line diagram from the example:

```
cd hub\\sld
..\\..\\.venv\\Scripts\\python scripts\\sld_paginate.py default examples\\input_for_sld_V1.xlsx <output_dir> SLD_V1 default default
```

## Rules of the house
- Plugins govern skills. A skill defined twice: the plugin copy governs and a warning is raised (error in production builds).
- `.svg` is internal only; `.dxf` is edited in the workspace and delivered as a stamped copy. See `schemas/deliverable-policy.json`.
- Copyrighted PDFs never enter this repository (`.gitignore` + pre-commit hook).
- Product content is English; Claude explains to the user in Spanish. See `docs/README.es.md`.

## Dependencies
See [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md).

## Status
Draft 0.1.0. Calculation tables are pending validation against the official standards (`hub/aea-calc/docs/11-pendientes.md`).
""")
w(PF / "docs/README.es.md", """# Plataforma EPC (resumen en español)

Framework de ingeniería EPC automatizada, armado con plugins (como Lego). Hoy corre dentro de Claude Code; el mismo motor pasará a web (Python + React) y a escritorio.

- `hub/` contiene todos los plugins; `skills/` todas las skills. Los plugins gobiernan: si una skill está duplicada, vale la del plugin y se te avisa antes de producción.
- `../dev-knowledge/` guarda normas, informes de terceros y material de estudio: nunca se versiona ni se sube.
- `../projects/<cliente>/<proyecto>/` separa `workspace/` (editable, interno) de `deliverables/` (lo que recibe el cliente).
- `.svg` nunca se entrega; `.dxf` se edita en el workspace y se entrega una copia sellada.
- Gestión de proyecto: PM² por defecto; el usuario puede elegir PMI u otra metodología.
- Plan completo: `docs/plan/PLAN_FRAMEWORK_EPC.md`. Registro de la migración: `docs/MIGRATION_LOG.md`.
""")
w(PF / "docs/DEPENDENCIES.md", """# Dependencies

## Python (>= 3.10)
| Package | Needed by | Required |
|---|---|---|
| openpyxl >= 3.1 | aea-calc, iram-titleblock, sld, mld, procurement | yes |
| lxml | iram-titleblock, sld, mld | yes |
| ezdxf | iram-titleblock, sld, mld (DXF output) | yes |
| svgelements | sld | yes |
| shapely | sld | yes |
| pypdf | standard-ingest (text extraction) | yes, for standard-ingest |
| pypdfium2, pillow | standard-ingest (render scanned pages to PNG) | yes, for standard-ingest |
| jsonschema | standard-ingest (schema validation; falls back to a minimal check) | recommended |
| cairosvg (+ Cairo library on Windows) | iec-symbols build tools, sld PNG previews | optional |
| pillow | iec-symbols build tools | optional |
| pytest, pytest-cov | tests | dev |

The core (`tools/`, registry, skill checks) uses only the standard library.

## System tools (optional)
`pandoc` (Markdown -> Word), `libreoffice`/`soffice` (Office -> PDF, used by doc-quality and pm2-docs), `poppler-utils` (`pdftotext`, `pdftoppm`).

## Plugin graph (hub)
```
sld  -> aea-calc, iec-symbols, iram-titleblock
mld  -> sld, iram-titleblock, iec-symbols
spec-writer -> doc-quality
pm2-docs    -> doc-quality
procurement -> equipment-catalog
standard-ingest -> (core/rules engine, no plugin dependency)
```
Versions are checked by `tools/build/epc_build.py registry` (semver ranges: `^`, `~`, exact).

## Known runtime notes
- `sld` needs `iec-symbols >= 0.4.14` (symbol files are named `291_E_LV_SLD_IEC60617_<id>.svg`).
- `pm2-docs` imports `document_verifier` from `doc-quality`; until hub path resolution exists, run with `PYTHONPATH=hub/doc-quality/scripts`.
- Five `doc-quality` tests for `input_converter` fail on Windows (the fake soffice is a shell script); PDF stamping tests need poppler/pandoc.
""")

for k, v in reg["plugins"].items():
    existing = PF / f"hub/{k}/README.md"
    if existing.exists():
        continue
    m = json.loads((PF / f"hub/{k}/plugin.json").read_text(encoding="utf-8"))
    req = "".join(f"- `{d}` {r}\n" for d, r in m.get("requires", {}).items()) or "- none\n"
    sk = "".join(f"- [`{s['id']}`](../../skills/{s['id']}/SKILL.md) ({s['role']})\n" for s in m.get("skills", [])) or "- none\n"
    py = ", ".join(m.get("python", {}).get("requires", [])) or "stdlib only"
    out = "".join(f"- `.{o['format']}`: {o['channel']}\n" for o in m.get("outputs", [])) or "- none\n"
    status = f" - **{m['status']}**" if "status" in m else ""
    w(existing, f"""# {k}

{m['description']}

- Version: {m['version']} ({m['kind']}){status}
- Entitlement: `{m.get('entitlement', '-')}`
- Python: {py}

## Requires
{req}
## Skills
{sk}
## Outputs
{out}
See `plugin.json` for the full manifest. Legacy origin: `{m.get('legacy', {}).get('source', '-')}`.
""")

w(PF / "hub/README.md", "# hub\n\nOne folder per plugin: `plugin.json` (governs), code, data, docs, tests. `registry.json` is generated by `python tools/build/epc_build.py registry`; do not edit it by hand.\n\nReplace a plugin by replacing its folder here, then run the registry and skill-conflict checks.\n")
w(PF / "core/README.md", "# core\n\n`workflow/` holds the seed of the workflow engine migrated from the legacy template: state rules (`rules/`), transition scripts (`scripts/`, with `states.json`, `workflow.py`, `fwlib.py`) and fixed-phrase commands (`commands/`). Next step: turn `states.json` + `workflow.py` into the engine described in docs/plan section 2.4.\n")
w(PF / "methodologies/pm2/methodology.json", json.dumps({"id": "pm2", "name": "PM2 (European Commission)", "version": "0.1.0", "default": True,
    "phases": ["Initiating", "Planning", "Executing", "Closing"], "artifacts_catalog": "rules/m8-management-documents.md",
    "templates": "templates/", "programme": "rules/m10-programme-management.md", "plugin": "pm2-docs", "status": "migrated-from-template"}, indent=2) + "\n")
w(PF / "methodologies/pmi/README.md", "# pmi\n\nPlaceholder for the PMI/PMBOK methodology pack. Must fill the same project entities as `pm2`. Not started.\n")
w(PF / "methodologies/custom/README.md", "# custom\n\nEmpty skeleton for a company-specific methodology. Copy `pm2/methodology.json` as a starting point.\n")
ar = {"id": "AR", "name": "Argentina", "default_locale": "es-AR", "currency": "ARS", "frequency_hz": 50, "standards_bodies": ["AEA", "IRAM"],
      "voltages_lv": [230, 400], "status": "active", "packs": {"electrical": ""}, "legacy_index": "_legacy/standards-index.md"}
w(PF / "jurisdictions/AR/jurisdiction.json", json.dumps(ar, indent=2, ensure_ascii=False) + "\n")
w(PF / "jurisdictions/_template/jurisdiction.json", json.dumps({**ar, "id": "XX", "name": "", "default_locale": "", "currency": "", "status": "template", "standards_bodies": []}, indent=2) + "\n")
w(PF / "jurisdictions/README.md", "# jurisdictions\n\nOne folder per country (ISO 3166 alpha-2). Each standard becomes `<domain>/<STANDARD-ID>/rules.json` promoted from `dev-knowledge/standards/<CC>/<STANDARD-ID>/draft/` (schema: `schemas/rules.schema.json`). Currently the AEA tables still live inside `hub/aea-calc/scripts/` (`aea_tables.json`, `rules/`) and must be moved here once validated.\n")
w(PF / "i18n/en/common.json", json.dumps({"app.name": "EPC Platform", "project.workspace": "Workspace", "project.deliverables": "Deliverables"}, indent=2) + "\n")
w(PF / "i18n/es/common.json", json.dumps({"app.name": "Plataforma EPC", "project.workspace": "Espacio de trabajo", "project.deliverables": "Entregables"}, indent=2, ensure_ascii=False) + "\n")
w(PF / "tests/README.md", "# tests\n\n`golden/` holds reference input/output sets (Excel -> JSON -> SVG). Seeds: `hub/sld/tests/fixtures/{a1,a3}` and `hub/iram-titleblock/tests/fixtures`.\nRun plugin unit tests from each plugin's `scripts/` folder: `python -m unittest discover -s . -p \"test_*.py\"`.\n")
w(PF / "apps/README.md", "# apps\n\nPlanned adapters over the same engine: `cli`, `mcp` (one MCP server per plugin), `api` (FastAPI), `web` (React), `desktop` (Tauri/Electron). Not built yet.\n")
w(W / "projects/_template/.epc/project.json", json.dumps({"schema_version": "1.0", "client": "", "project_code": "", "jurisdiction": "AR", "locale": "es-AR",
    "methodology": "pm2", "disciplines": ["electrical"], "phase": "IC", "engine_min_version": "0.1.0"}, indent=2) + "\n")
w(W / "projects/_template/README.md", "# Project template\n\nCopy to `projects/<CLIENT>/<PROJECT>/`.\n\n- `workspace/` editable, internal, versioned in git (svg, dxf masters, md sources, calc json).\n- `deliverables/` client-facing, read-only, written only by the publish step (see `platform/schemas/deliverable-policy.json`).\n- `.epc/` platform state: `project.json`, `plugins.lock` (`python tools/build/epc_build.py lock <project>`), `ledger/`.\n- `_out/` temporary files, not versioned.\n")
print("files written")
