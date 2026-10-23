<div align="center">

<img src="assets/logo.png" alt="EPC-291" width="360"/>

# EPC-291

**Automated EPC engineering, built from plugins.**
Calculations, drawings, documents and standards-based rules for engineering projects, with a web app for customers and a technical console for engineers.

[![Version](https://img.shields.io/badge/version-0.1.0%20draft-1f6feb?style=for-the-badge)](CHANGELOG.md)
[![Gate](https://img.shields.io/badge/test%20battery-20%20checks-2ea44f?style=for-the-badge)](tools/ci/run_gate.py)
[![Python](https://img.shields.io/badge/python-3.12-3776ab?style=for-the-badge)](backend/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?style=for-the-badge)](backend/)
[![React](https://img.shields.io/badge/web-React%20%2B%20TypeScript-0ea5e9?style=for-the-badge)](frontend/)
[![PostgreSQL](https://img.shields.io/badge/database-PostgreSQL-336791?style=for-the-badge)](database/)
[![Plugins](https://img.shields.io/badge/plugins-12-f0abfc?style=for-the-badge)](claude/plugins/registry.json)
[![Argentina](https://img.shields.io/badge/jurisdiction-AR-64748b?style=for-the-badge)](engine/jurisdictions/)

[Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Architecture](docs/architecture/README.md) · [Planning board](planning/BOARD.md) · [Documentation](docs/README.md)

Español: [README.es.md](README.es.md)

</div>

---

## ✨ What it is

An EPC (Engineering, Procurement, Construction) platform made like Lego: small plugins that Claude Code can run today, over one engineering engine that will also serve a web app and a desktop app.

- **Engineering engine** — pure Python packages for calculation, drawing, documents, rules and standards, with no web or Claude dependency.
- **Claude layer** — plugins (packaging only), skills and agents that wrap the engine. Plugins govern their skills.
- **Product** — a modular FastAPI backend, a React app for customers and a separate console for administrators.
- **Management** — projects follow PM² by default (PMI or custom selectable), with WBS, schedule with critical path, and an internal backlog.

The customer sees only projects, deliverables, input data, requirements, reports and the project plan. Plugins, skills, rules and internal files exist only for the admin role.

## 🧭 What it includes

| Area | Folder | Content | State |
|---|---|---|---|
| Engineering engine | `engine/` | calc, rules, standards, drawing, documents + country packs | ✅ |
| Claude layer | `claude/` | 12 plugins, 14 skills, agents, marketplace | ✅ |
| Backend | `backend/` | 11 modules with enforced boundaries (import-linter) | ✅ |
| Frontend | `frontend/` | `web` (customer), `console` (admin), `packages/ui` | ✅ |
| Database | `database/` | Alembic baseline: organizations, users, projects, deliverables, ledger | ✅ |
| Infrastructure | `infra/` | Docker, compose with PostgreSQL, CI workflow | ✅ |
| Project management | `management/` | project skeleton, methodologies | ✅ |
| Software planning | `planning/` | vision, PRDs, backlog, sprints, board (not shipped) | ✅ |
| Authentication, organizations, billing | — | planned (US-0018) | 🚧 |
| Desktop edition (Rust/Tauri, Windows · macOS · Linux) | `desktop/` | planned (EP-012, ADR-0007) | 🚧 |
| Medium voltage, HVAC, fire, civil | — | after low voltage | 🚧 |

Argentina is the first jurisdiction (AEA 90364, IRAM); other countries plug in as country packs with their own `rules.json` per standard.

## 🚀 Quick start (Windows)

```bash
# Clone and enable the safety hook
git clone https://github.com/291-DAVH/EPC-291.git
cd EPC-291
git config core.hooksPath platform/tools/hooks

# Python environment (from platform/)
cd platform
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pip install -e ../engine/calc -e ../engine/rules -e ../engine/standards -e ../engine/drawing -e ../engine/documents -e "../backend[dev]"
cd ..

# Test battery (20 checks, run before merging anything)
platform\.venv\Scripts\python tools\ci\run_gate.py
```

Run the app with 20 simulated projects (two terminals):

```bash
# 1) demo data and API (from platform/; copy .env.example to platform/.env.demo and set EPC_PROJECTS=../local/projects-demo)
.venv\Scripts\python tools\dev\seed_demo.py
.venv\Scripts\python -m uvicorn epc.main:app --app-dir ..\backend\src --port 8000 --env-file .env.demo

# 2) web app (customers) on :5173, console (admin) on :5174
cd frontend && npm install && npm run dev:web        # npm run dev:console for the console
```

`EPC_ROLE=admin` unlocks the technical API and the console. Full stack with PostgreSQL: see [infra/README.md](infra/README.md).

## 🗂️ Structure

```
EPC-291/
├─ assets/        logo
├─ engine/        calc/ rules/ standards/ drawing/ documents/ jurisdictions/   (pure Python)
├─ claude/        plugins/ skills/ agents/ marketplace/                        (Claude Code layer)
├─ backend/       src/epc/{core, modules/*}   tests/   .importlinter           (FastAPI)
├─ frontend/      web/ console/ packages/ui                                    (React workspace)
├─ database/      migrations/ (Alembic)   tests/
├─ infra/         docker/ compose/        (+ .github/workflows/ci.yml)
├─ management/    templates/project-skeleton: workspace (editable) + deliverables (client-facing)
├─ shared/        schemas/ (JSON Schema)   i18n/
├─ planning/      software planning during development
├─ docs/          architecture, ADRs, explanation, branching policy
├─ platform/      Claude-side build tooling (registry, packaging) and demo seed
├─ tools/         ci/run_gate.py, planning/board.py
└─ local/         GIT-IGNORED: dev-knowledge, legacy, demo and real projects
```

## 🔌 Plugins

| Plugin | Version | Kind | Requires |
|---|---|---|---|
| `aea-calc` | 1.6.0 | calc | — |
| `iec-symbols` | 0.4.16 | knowledge | — |
| `iram-titleblock` | 0.5.1 | generator | — |
| `sld` | 0.1.1 | generator | aea-calc, iec-symbols, iram-titleblock |
| `mld` | 0.1.0 (pending) | generator | sld, iram-titleblock, iec-symbols |
| `standard-ingest` | 0.1.0 | workflow | — |
| `intake-analysis` | 0.1.0 | workflow | — |
| `pm2-docs` | 0.1.0 | workflow | doc-quality |
| `doc-quality` | 0.1.0 | workflow | — |
| `spec-writer` | 0.1.0 | workflow | doc-quality |
| `procurement` | 0.1.0 | connector | equipment-catalog |
| `equipment-catalog` | 0.1.0 | knowledge | — |

The source of truth is `claude/plugins/registry.json` (generated).

## 🛠️ How we work

1. `main` is stable, `dev` integrates, work happens on `feature/*`, `fix/*` and `chore/*`, merged with `--no-ff` ([docs/BRANCHING.md](docs/BRANCHING.md)).
2. The test battery must be green before any merge.
3. Plugins govern skills: a skill defined twice resolves to the plugin copy and raises a warning (an error in production builds).
4. `.svg` is internal only; `.dxf` is edited in the workspace and delivered as a stamped copy.
5. Copyrighted PDFs and anything in `local/dev-knowledge/` never enter the repository (ignore rules and pre-commit hook).
6. Product content is English; Claude explains to the user in Spanish.

## 📚 Documentation

| Document | Content |
|---|---|
| [docs/explanation/what-is-epc.md](docs/explanation/what-is-epc.md) | What an EPC is and why the structure looks like this |
| [docs/architecture/](docs/architecture/README.md) | Target architecture, ADRs, migration phases |
| [planning/README.md](planning/README.md) | Vision, PRDs, backlog, sprints, [board](planning/BOARD.md) |
| [docs/USER_DATA_MODEL.md](docs/USER_DATA_MODEL.md) | What the customer sees and how input becomes requirements |
| [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | Python, system tools and plugin graph |
| [CHANGELOG.md](CHANGELOG.md) · [CONTRIBUTING.md](CONTRIBUTING.md) | Changes and how to contribute |

## 🤝 Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), open a branch from `dev`, run the test battery and send a pull request with the [template](.github/pull_request_template.md).

## 📜 Status and license

Draft 0.1.0. Calculation tables and standards rules are pending validation against the official documents (`engine/calc/docs/11-pendientes.md`). No license has been chosen yet: all rights reserved until the owner decides.

<div align="center">

<sub>Built with ⚡ for engineers who design installations.</sub>

</div>
