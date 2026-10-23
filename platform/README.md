# EPC Platform

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
├─ apps/            cli, mcp, api, web, desktop (not built yet)
├─ tools/           build, ci, hooks, migrate, dev
├─ tests/golden/    reference inputs/outputs
└─ docs/            plan, architecture, migration notes
```

Siblings of this repository (never inside it): `../dev-knowledge/` (standards, third-party reports, study material, never versioned) and `../projects/` (client projects: `workspace/` editable, `deliverables/` client-facing).

## Plugins

| Plugin | Version | Kind | Status | Requires | Skills |
|---|---|---|---|---|---|
| [`aea-calc`](hub/aea-calc/) | 1.6.0 | calc | active | - | size-feeder, dimension-installation, write-calculation-memo, write-memo-summary |
| [`doc-quality`](hub/doc-quality/) | 0.1.0 | workflow | active | - | - |
| [`equipment-catalog`](hub/equipment-catalog/) | 0.1.0 | knowledge | active | - | - |
| [`iec-symbols`](hub/iec-symbols/) | 0.4.16 | knowledge | active | - | generate-electrical-symbol |
| [`iram-titleblock`](hub/iram-titleblock/) | 0.5.1 | generator | active | - | generate-titleblock-sheet, generate-iram-sheet |
| [`mld`](hub/mld/) | 0.1.0 | generator | pending | sld, iram-titleblock, iec-symbols | convert-sld-to-mld |
| [`pm2-docs`](hub/pm2-docs/) | 0.1.0 | workflow | active | doc-quality | create-management-document |
| [`procurement`](hub/procurement/) | 0.1.0 | connector | active | equipment-catalog | request-quotation |
| [`sld`](hub/sld/) | 0.1.1 | generator | active | aea-calc, iec-symbols, iram-titleblock | generate-sld |
| [`spec-writer`](hub/spec-writer/) | 0.1.0 | workflow | needs-neutral-templates | doc-quality | generate-specification |
| [`standard-ingest`](hub/standard-ingest/) | 0.1.0 | workflow | active | - | analyze-standard |

## Quick start (Windows)

```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python tools\build\epc_build.py registry       # validate hub + skills
.venv\Scripts\python tools\ci\check_skill_conflicts.py        # duplicate / orphan skills
.venv\Scripts\python tools\build\epc_build.py package all     # dist\<id>-<ver>.plugin for Claude Code
git config core.hooksPath tools/hooks                          # block PDF/DWG commits
```

Generate a single-line diagram from the example:

```
cd hub\sld
..\..\.venv\Scripts\python scripts\sld_paginate.py default examples\input_for_sld_V1.xlsx <output_dir> SLD_V1 default default
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
