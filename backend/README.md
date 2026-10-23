# backend

FastAPI modular monolith (package `epc`). One bounded context per folder under `src/epc/modules/`.

```
src/epc/
  main.py            composition root: builds the app, maps domain errors to HTTP
  core/              config (Settings), errors, filesystem helpers (no business rules)
  modules/<name>/
    api.py           HTTP routes (thin)
    service.py       use cases
    repository.py    storage access (files today, database later)
    models.py        request/response models (optional)
    public.py        the only thing other modules may import
tests/
  integration/       HTTP-level tests per surface
  architecture/      AST checks of the boundaries
```

| Module | Purpose |
|---|---|
| `identity` | current user/role and the role guard |
| `projects` | create and list projects, options |
| `deliverables` | deliverables list and downloads |
| `intake` | customer inputs (voice of customer, stories, documents) |
| `requirements` | structured requirements and their sources |
| `management` | portfolio, project summary, reports |
| `engineering` | read-only view of the engineering workspace for the engineer/admin: SVG diagrams (single-line, multi-line, drawings) and lists/notes as text (CSV, XLSX, Markdown), and the editable design criteria of the project (catalog + overrides + history + generated report) |
| `sld` | data entry for the single-line diagram (board, titleblock, circuits), validation, and execution of the sld plugin generator (`epc_drawing.sld`) unchanged; outputs are published into the engineering folders |
| `wbs` | work breakdown structure (EDT): dotted-number tree, weights, progress rolled up from the leaves |
| `schedule` | activities with dates and finish-to-start dependencies; critical path, slack, conflicts, late work |
| `backlog` | internal project backlog (tasks, changes, risks, questions, defects); never shown to the customer |
| `knowledge` | rules search and checks (via `epc_rules`) |
| `admin` | plugins, skills, overview (admin only) |
| `quality`, `engineering`, `procurement`, `construction`, `billing`, `notifications` | planned (skeletons) |

## Rules
1. Another module is imported only through `epc.modules.<other>.public`.
2. Inside a module: `api -> service -> repository -> models`, never upwards.
3. `epc.core` never imports modules; modules never import `epc.main`; `engine/*` never imports `epc`.

`python tools/ci/gen_importlinter.py` regenerates `.importlinter` when modules change; `lint-imports` and `tests/architecture` enforce the rules.

## Run and test (from the repository root)
```
uvicorn epc.main:app --app-dir backend/src --port 8000
cd backend && python -m unittest discover -s tests -t . && lint-imports
```
Configuration comes from environment variables (`EPC_PROJECTS`, `EPC_ROLE`, `EPC_USER`, `EPC_ORG`, `EPC_ENV`), see `.env.example`.
