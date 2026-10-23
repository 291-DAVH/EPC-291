# ADR-0002: Three kinds of "management" with three homes

Status: Proposed. Date: 2026-10-23.

## Context
"Management" means three different things in this project and they were getting mixed:
1. **How we build the software**: vision, PRDs, backlog, sprints, roadmap, risks.
2. **What our users do inside the product**: WBS (EDT), project backlog, schedule, risks, change requests, MDR/LME, progress reports, methodology (PM2 or PMI).
3. **How AI is packaged**: plugins, skills, agents (the Claude layer).

## Decision
| Concern | Home | Ships to clients |
|---|---|---|
| 1. Software planning | `planning/` (Markdown with front matter, generated `BOARD.md`) | no |
| 2. Project-management domain | code in `backend/.../modules/management` and `frontend/web/.../management`; knowledge in `management/` (methodologies, templates, WBS catalogs, schemas) | yes |
| 3. Claude layer | `claude/` | yes (plugins) |

The **backlog/WBS/sprint schemas live once** in `management/schemas/` and are used by both `planning/` (our own work) and the product's management module. We use our product's data model to plan our product (dogfooding).

Development-time Claude Code configuration for this repository lives in `.claude/` (settings, developer agents), separate from the product's `claude/`.

## Consequences
- (+) Nothing that is only for developers can leak into the client app.
- (+) The management module is validated daily by our own planning.
- (-) Two similarly named folders (`planning/` vs `management/`); mitigated by their READMEs and by this ADR.
