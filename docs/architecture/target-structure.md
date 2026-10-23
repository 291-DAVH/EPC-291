# Target structure and migration plan

Status: **in progress**. Phases 1 to 4 are done; the rest are pending.

| Phase | Content | State |
|---|---|---|
| 1 | Planning, docs, ADRs | done |
| 2 | `local/` and `shared/` | done |
| 3 | `claude/` layer and validated marketplace | done |
| 4 | `engine/` packages (calc, rules, standards, drawing, documents) | done |
| 5 | Backend modules | pending |
| 6 | Frontend split | pending |
| 7 | Database and infrastructure | pending |
| 8 | Management module | pending |

## 1. Full tree

```
EPC-291/
├─ README.md  README.es.md  CHANGELOG.md  CONTRIBUTING.md  LICENSE  .editorconfig  .gitattributes  .gitignore  .env.example
├─ .github/                      CI workflows, issue and PR templates
├─ .claude/                      Claude Code settings for developing THIS repository (settings.json, dev agents, commands)
│
├─ frontend/                     ───────────── CLIENT SIDE
│  ├─ web/                          client portal (React + TypeScript + Vite)
│  │  └─ src/ app/ pages/ features/{portfolio,project,deliverables,inputs,requirements,reports}/ entities/ shared/
│  ├─ console/                      admin console (plugins, rules, checker, files): separate app, role-gated
│  ├─ ui/                           design system (components, tokens, themes)
│  └─ i18n/                         UI catalogs (es, en)
│
├─ backend/                      ───────────── SERVER SIDE
│  ├─ pyproject.toml  Dockerfile
│  ├─ src/epc/
│  │  ├─ core/                      config, security, errors, events, logging
│  │  ├─ modules/
│  │  │  ├─ projects/  deliverables/  intake/  requirements/  quality/  engineering/
│  │  │  ├─ management/  procurement/  construction/  knowledge/  identity/  billing/  notifications/
│  │  │  └─ <module>/ api/ application/ domain/ infrastructure/ public.py
│  │  └─ main.py
│  ├─ workers/                      background jobs (generation, analysis, publishing)
│  └─ tests/ unit/ integration/ architecture/ (import-linter contracts)
│
├─ database/                     ───────────── DATA
│  ├─ migrations/                   Alembic revisions
│  ├─ schema/                       DDL snapshots, ERD
│  ├─ seeds/                        reference and demo data
│  └─ README.md                     what lives in DB vs in project files
│
├─ engine/                       ───────────── ENGINEERING LIBRARIES (pure Python, no web)
│  ├─ calc/                         electrical LV (AEA), later MV, HVAC, fire, civil...
│  ├─ drawing/                      sld, mld, iec-symbols, iram-titleblock
│  ├─ rules/                        rules engine (epc_rules)
│  ├─ standards/                    ingestion pipeline (extract, validate, promote)
│  ├─ documents/                    quality verifiers, specification builder, exporters
│  └─ jurisdictions/                AR/, _template/  (rules.json per standard)
│
├─ management/                   ───────────── PROJECT-MANAGEMENT KNOWLEDGE (shipped)
│  ├─ methodologies/                pm2/, pmi/, custom/
│  ├─ templates/                    charter, WBS/EDT, MDR/LME, schedule, risk register, reports, project-skeleton/
│  ├─ wbs/                          EDT catalogs per discipline and phase
│  └─ schemas/                      backlog, WBS, schedule, risk (shared with planning/)
│
├─ claude/                       ───────────── AI LAYER
│  ├─ plugins/                      one folder per plugin (manifest + wiring to engine/)
│  ├─ skills/                       all skills (plugins govern them)
│  ├─ agents/                       specialist agents
│  ├─ mcp/                          MCP servers (one per capability)
│  ├─ prompts/                      reusable prompts and style rules
│  ├─ evals/                        evaluation cases per skill
│  └─ marketplace/                  .claude-plugin/marketplace.json
│
├─ planning/                     ───────────── SOFTWARE PLANNING (development stage, not shipped)
│  ├─ vision.md  BOARD.md (generated)
│  ├─ roadmap/  prd/  risks/  releases/  templates/
│  ├─ backlog/ epics/ stories/ bugs/ spikes/
│  └─ sprints/ SPRINT-01/ plan.md review.md retro.md
│
├─ docs/                         explanation/ how-to/ reference/ tutorials/ architecture/ (C4 + decisions/)
├─ infra/                        docker/ compose/ ci/ k8s-helm/ onprem/
├─ shared/                       schemas/ (plugin, rules, deliverable policy) · i18n/ · design-tokens/
├─ tools/                        registry, hooks, ci, seeding, one-off migrations
│
└─ local/                        GIT-IGNORED
   ├─ dev-knowledge/  legacy/  projects-demo/  projects/<client>/
```

## 2. Mapping from today's folders

| Today | Target |
|---|---|
| `platform/apps/web` | `frontend/web` (admin pages -> `frontend/console`) |
| `platform/apps/api` | `backend/src/epc` (split into modules: `projects`, `deliverables`, `intake`, `requirements`, `identity`) |
| `platform/core/rules` | `engine/rules` |
| `platform/core/workflow` | `backend/src/epc/modules/deliverables` (state machine) + `docs/explanation` (rules prose) |
| `platform/hub/aea-calc/scripts` | `engine/calc/aea` |
| `platform/hub/{sld,mld,iec-symbols,iram-titleblock}` | `engine/drawing/*` (code, data) |
| `platform/hub/standard-ingest/scripts` | `engine/standards` |
| `platform/hub/{doc-quality,pm2-docs,spec-writer}` scripts | `engine/documents` and `management/` |
| `platform/hub/intake-analysis/scripts` | `backend/src/epc/modules/intake` |
| `platform/hub/*/plugin.json`, skills | `claude/plugins/<id>`, `claude/skills/<id>` |
| `platform/agents` | `claude/agents` |
| `platform/methodologies` | `management/methodologies` |
| `platform/jurisdictions` | `engine/jurisdictions` |
| `platform/schemas`, `platform/i18n` | `shared/schemas`, `shared/i18n` |
| `platform/tools` | `tools/` |
| `projects/_template` | `management/templates/project-skeleton` |
| `dev-knowledge`, `_legacy`, `projects-demo`, `projects/*` | `local/...` |
| `docs/` | `docs/` (reorganized by Diataxis) |
| (new) | `planning/`, `database/`, `infra/`, `.github/` |

## 3. Migration phases (each one a branch merged into `dev`)
1. **Planning and docs** (this branch): `planning/`, architecture docs and ADRs. No code moves.
2. **Local and shared**: create `local/`, move the private folders; move `schemas/` and `i18n/` to `shared/`; update ignore rules, hook and scripts.
3. **Claude layer**: move manifests, skills, agents to `claude/`; keep plugin code in place temporarily; add `marketplace.json`; update `epc_build.py`.
4. **Engine extraction**: move plugin code into `engine/` packages with `pyproject.toml` each; plugins call the engine; rules engine and standards pipeline included.
5. **Backend**: restructure `apps/api` into modules with `public.py` facades; add import-linter contract and architecture tests.
6. **Frontend**: split `web` and `console`; feature-sliced folders; shared `ui` package.
7. **Database and infra**: Alembic baseline, Postgres in compose, Dockerfiles, CI workflow.
8. **Management module**: WBS/EDT, backlog and schedule in backend + frontend, reusing the schemas that `planning/` already uses.

After every phase the same gate runs: registry check, skill-conflict check, API tests, engine tests, web type-check and build.

## 4. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Large moves break imports and paths | One phase per branch; `git mv` to keep history; the gate above after each phase |
| Over-engineering too early | Modular monolith, 3-5 engine packages at first, services extracted only on need |
| Boundaries erode over time | import-linter contracts and architecture tests in CI |
| Plugin layout drifts from Claude Code | `claude plugin validate` in CI against the official layout |
| Private material leaks | `local/` git-ignored, pre-commit hook, CI check for PDF/DWG |
