# Target architecture

Status: **proposed** (not yet applied to the folders). Decisions are recorded in [decisions/](decisions/). Background on the domain: [What is an EPC?](../explanation/what-is-epc.md).

## 1. Principles
1. **Modular monolith first.** One deployable backend, split into bounded contexts with explicit public interfaces; extract services only when a module needs independent scaling. (ADR-0001)
2. **Three kinds of "management", three homes.** Software planning (how we build), project-management domain (what users do), Claude layer (how AI is packaged). Never mixed. (ADR-0002)
3. **Engine without web.** Calculation, drawing, rules and document generation are pure Python libraries; the backend orchestrates them and Claude plugins expose them. (ADR-0003)
4. **The client sees only what concerns them.** Deliverables, input data, requirements, reports. Everything else needs the admin role. (ADR-0004)
5. **Private material stays out of git.** Standards, third-party reports, client data. (ADR-0005)
6. **Docs and planning live in the repository** (docs-as-code), with the planning schema reused by the product's own management module (dogfooding).

## 2. Layers

```
                       ┌──────────────── CLIENTS ─────────────────┐
                       │ frontend/web (portal)   frontend/console │   desktop deferred (ADR-0007)
                       └───────────────┬──────────────────────────┘
                                       │ HTTPS / OpenAPI
        ┌──────────────────────────────▼──────────────────────────────┐
        │ backend/  FastAPI modular monolith (bounded contexts)       │
        │  projects · deliverables · intake · requirements · quality  │
        │  engineering · management · procurement · construction      │
        │  knowledge · identity · billing · notifications             │
        └───────┬──────────────────┬──────────────────┬───────────────┘
                │                  │                  │
       ┌────────▼───────┐  ┌───────▼────────┐  ┌──────▼───────────────┐
       │ database/      │  │ engine/        │  │ claude/              │
       │ PostgreSQL     │  │ calc, drawing, │  │ plugins, skills,     │
       │ (platform      │  │ rules, docs,   │  │ agents, MCP, evals   │
       │  state)        │  │ standards      │  │ (uses engine)        │
       └────────────────┘  └────────────────┘  └──────────────────────┘
   management/  methodologies, templates, WBS catalogs (data shipped with the product)
   planning/    vision, PRD, backlog, sprints, roadmap (development stage only, not shipped)
```

Files remain the system of record for **engineering artifacts** (they are versioned, diffable, deliverable); the database holds **platform state** (users, organizations, project index, jobs, ledger, subscriptions).

## 3. Top-level folders

| Folder | Purpose | Shipped to clients | Language |
|---|---|---|---|
| `frontend/` | React apps: `web` (client portal), `console` (admin), shared `ui` package | yes (`web`) | TypeScript |
| `backend/` | FastAPI modular monolith, workers, API tests | yes | Python |
| `database/` | Schema, migrations (Alembic), seeds, ERD | yes (migrations) | SQL / Python |
| `engine/` | Engineering libraries: `calc`, `drawing`, `rules`, `standards`, `documents`, `jurisdictions` | yes | Python |
| `management/` | Project-management knowledge: methodologies (PM2, PMI, custom), templates, WBS/EDT catalogs, schemas | yes | Markdown / JSON |
| `claude/` | AI layer: `plugins/`, `skills/`, `agents/`, `mcp/`, `prompts/`, `evals/`, `marketplace/` | yes (plugins) | Markdown / JSON / Python |
| `planning/` | Software planning during development: vision, PRD, backlog, sprints, roadmap, releases, risks | **no** | Markdown |
| `docs/` | Technical documentation (Diataxis) and architecture (C4 + ADRs) | no | Markdown |
| `infra/` | Docker, compose, CI/CD, on-prem packaging | n/a | YAML |
| `shared/` | Contracts used by several parts: JSON schemas, i18n catalogs, design tokens | yes | JSON |
| `tools/` | Developer and CI scripts (registry, hooks, seeding, migrations) | no | Python |
| `local/` | **Git-ignored**: `dev-knowledge/`, `legacy/`, `projects-demo/`, `projects/` | never | n/a |

Root files: `README.md`, `README.es.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `.editorconfig`, `.gitattributes`, `.gitignore`, `.env.example`, `.github/` (CI), `.claude/` (Claude Code settings for developing this repository; not the product's `claude/`).

## 4. Backend modules (bounded contexts)

| Module | Responsibility | Talks to |
|---|---|---|
| `projects` | Projects, clients, disciplines, phases, project skeleton, plugin lock | identity |
| `deliverables` | MDR/LME, documents, revisions, review/audit workflow, transmittals, one-way publish | projects, quality, engine |
| `intake` | Customer input (voice of customer, user stories, documents) and its status | requirements, claude |
| `requirements` | Structured requirements, acceptance criteria, open questions, traceability | intake, deliverables |
| `quality` | Review packages, audits, findings, document verifier | deliverables, engine |
| `engineering` | Orchestrates calculations and drawing generation per discipline | engine |
| `management` | WBS/EDT, backlog, schedule (CCPM), risks, change requests, reports; methodology packs | projects, deliverables |
| `procurement` | MTO/BOM, quotations, vendors, purchase tracking | engineering |
| `construction` | Site RFIs, redlines, punch list, commissioning protocols, as-built | deliverables |
| `knowledge` | Standards, rules per jurisdiction, equipment catalog | engine |
| `identity` | Users, organizations, roles, SSO | all |
| `billing` | Plans, entitlements, metering | identity |
| `notifications` | E-mail, in-app | all |

Each module has the same internal shape: `api/` (routers), `application/` (use cases), `domain/` (entities, rules), `infrastructure/` (repositories, adapters) and a single `public.py` facade. Other modules may import only `public.py`; an import-linter contract in CI enforces it.

## 5. What each audience sees

| Audience | Sees | Never sees |
|---|---|---|
| Client user | Projects, deliverables (PDF/DXF/XLSX), input data, requirements, reports | Plugins, skills, rules, SVG/JSON internals, workspace trees, Claude |
| Admin | Technical console: plugins, rules, checker, files | Private material of other tenants |
| Developer (us) | Everything, plus `planning/`, `docs/`, `claude/`, `engine/` | Client data (never in git) |

## 6. Roadmap to get there
See [target-structure.md](target-structure.md) for the full tree, the mapping from today's folders and the migration phases.
