# EPC-291

Automated EPC engineering framework built from plugins ("Lego"): calculations, drawings, documents, rules extracted from standards, and a web app for end users. Runs today inside Claude Code; the same engine is meant for web and desktop.

Español: [README.es.md](README.es.md)

## Repository layout

Migration to the [target architecture](docs/architecture/target-structure.md) is in progress; this is the current state (phases 2 and 3 done).

```
EPC-291/
├─ README.md  README.es.md  CHANGELOG.md  CONTRIBUTING.md  .env.example  .editorconfig  .gitattributes  .gitignore
├─ docs/            architecture, ADRs, explanation, branching policy, dependencies, migration records
├─ planning/        software planning during development: vision, PRD, backlog, sprints, BOARD   (not shipped)
├─ platform/        product source (moving to frontend/ backend/ engine/ claude/ in the next phases)
│   ├─ core/  methodologies/  jurisdictions/  apps/  tests/  tools/
│   └─ pyproject.toml  requirements.txt  requirements-dev.txt
├─ claude/          AI layer (phase 3 done)
│   ├─ plugins/        one folder per plugin + registry.json
│   ├─ skills/  agents/  marketplace/  mcp/  prompts/  evals/
├─ management/      project-management knowledge shipped with the product
│   └─ templates/project-skeleton/   project skeleton: workspace (editable) + deliverables (client-facing)
├─ shared/          contracts used by several parts: schemas/ (JSON Schema), i18n/ (catalogs)
├─ tools/           repository tooling: ci/run_gate.py (test battery), planning/board.py
└─ local/           GIT-IGNORED, never versioned
    ├─ dev-knowledge/   standards, third-party reports, study material
    ├─ legacy/          archived original folders and old repositories
    ├─ projects-demo/   20 simulated projects for demos
    └─ projects/        real client projects (each in its own repository)
```

## Where to start
- **What an EPC is and why the structure looks like this:** [docs/explanation/what-is-epc.md](docs/explanation/what-is-epc.md), [docs/architecture/README.md](docs/architecture/README.md).
- **What we are building and in which order:** [planning/README.md](planning/README.md) (vision, PRDs, backlog, sprints, [BOARD](planning/BOARD.md)).

## Branches
`main` (stable) <- `dev` (integration) <- `feature/*`, `fix/*`, `chore/*`. See [docs/BRANCHING.md](docs/BRANCHING.md). Enable the safety hook after cloning:

```
git config core.hooksPath platform/tools/hooks
```

## Quick start (Windows)
Test battery for any change (from the repository root): `platform\.venv\Scripts\python tools\ci\run_gate.py`.

Setup and tools (from `platform/`):
```
cd platform
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python tools\build\epc_build.py registry         # validate hub + skills, write hub/registry.json
.venv\Scripts\python tools\ci\check_skill_conflicts.py          # duplicate / orphan skills
.venv\Scripts\python tools\build\epc_build.py package all       # dist\<id>-<ver>.plugin for Claude Code
.venv\Scripts\python tools\build\epc_build.py marketplace       # dist\marketplace (official layout + marketplace.json)
```
Run the app (two terminals, from `platform/`):
```
.venv\Scripts\python -m uvicorn apps.api.main:app --port 8000 --env-file .env.demo
cd apps\web && npm install && npm run dev                        # http://localhost:5173
```
Demo data: `.venv\Scripts\python tools\dev\seed_demo.py` creates 20 simulated projects in `local/projects-demo/`. Copy `.env.example` to `platform/.env.demo` and set `EPC_PROJECTS` to that folder. `EPC_ROLE=admin` unlocks the technical console.

## Plugins
| Plugin | Version | Kind | Requires |
|---|---|---|---|
| `aea-calc` | 1.6.0 | calc | - |
| `iec-symbols` | 0.4.16 | knowledge | - |
| `iram-titleblock` | 0.5.1 | generator | - |
| `sld` | 0.1.1 | generator | aea-calc, iec-symbols, iram-titleblock |
| `mld` | 0.1.0 (pending) | generator | sld, iram-titleblock, iec-symbols |
| `standard-ingest` | 0.1.0 | workflow | - |
| `intake-analysis` | 0.1.0 | workflow | - |
| `pm2-docs` | 0.1.0 | workflow | doc-quality |
| `doc-quality` | 0.1.0 | workflow | - |
| `spec-writer` | 0.1.0 | workflow | doc-quality |
| `procurement` | 0.1.0 | connector | equipment-catalog |
| `equipment-catalog` | 0.1.0 | knowledge | - |

The source of truth is `claude/plugins/registry.json` (generated).

## Rules of the house
- Plugins govern skills. A skill defined twice: the plugin copy governs and a warning is raised (error in production builds).
- `.svg` is internal only; `.dxf` is edited in the workspace and delivered as a stamped copy (`shared/schemas/deliverable-policy.json`).
- Copyrighted PDFs and anything in `local/dev-knowledge/` never enter the repository (ignore rules + pre-commit hook).
- Product content is English; Claude explains to the user in Spanish.
- The end-user web app never shows plugins, skills, rules or internal files; those exist only for the admin role.

## Documentation
| Document | Content |
|---|---|
| [docs/README.md](docs/README.md) | Index of all documents |
| [docs/BRANCHING.md](docs/BRANCHING.md) | Branching policy |
| [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | Python, system tools and plugin graph |
| [docs/USER_DATA_MODEL.md](docs/USER_DATA_MODEL.md) | What the end user sees and how customer input becomes requirements |
| [docs/plan/PLAN_FRAMEWORK_EPC.md](docs/plan/PLAN_FRAMEWORK_EPC.md) | Architecture and roadmap |
| [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) | Changes and how to contribute |

## Status
Draft 0.1.0. Calculation tables and standards rules are pending validation against the official documents (`claude/plugins/aea-calc/docs/11-pendientes.md`).
