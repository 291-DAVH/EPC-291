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
| `identity` | accounts and sessions (US-0018, ADR-0009): sign-in, individual and corporate organizations with seats, invitations, owner/member roles, platform staff, the request guard (401/403) and the tenant filter used by `projects`; `EPC_AUTH=simulated` keeps the role-from-environment mode for development |
| `projects` | create and list projects, options |
| `deliverables` | deliverables list, downloads (several formats per drawing, e.g. DXF + PDF) and the ZIP delivery package |
| `intake` | customer inputs (voice of customer, stories, documents) and their automatic analysis with the Claude API (admin/engineer, explicit confirmation, amounts removed, validated by the plugin's own validator, usage recorded) |
| `requirements` | structured requirements and their sources |
| `management` | portfolio, project summary, reports |
| `engineering` | read-only view of the engineering workspace for the engineer/admin: SVG diagrams (single-line, multi-line, drawings) and lists/notes as text (CSV, XLSX, Markdown), and the editable design criteria of the project (catalog + overrides + history + generated report) |
| `sld` | data entry for the board (board, titleblock, circuits), validation, and execution of the `board-design` pipeline (`epc_drawing.board_design`): the project's design criteria govern the calculation (`epc_calc.aea_pipeline`) and that calculation feeds the single-line (SLD) and multi-line (MLD) diagrams; outputs are published into the engineering folders |
| `registers` | project registers of the methodology (risks, changes, issues, decisions, assumptions, stakeholders): fields and options defined by `management/methodologies/<id>/registers.json`, validation, derived risk level, history of who changed what and when, never deleted (admin/engineer) |
| `norms` | review of the norm data by the norm reviewer role: every rule, calculation table or constant and design criterion can be corrected and approved or flagged; values are rewritten in the engine's data files, review state in `jurisdictions/AR/review.json`, every action in `review-log.jsonl` (reviewer and staff only) |
| `reporting` | management reports of the project's methodology (PM²: D11 status, D12 progress, D13 risks, D14 effort, D15 changes): catalog from `management/methodologies/<id>/reports.json`, content from the project's data and registers, Markdown + PDF in `workspace/05-management`, published to the client's Reports list on demand (admin/engineer) |
| `masterdata` | information entered once and reused: company profile (legal name, tax id...), saved clients, people (who draws, checks, approves) and logos (SVG/PNG); files in `EPC_DATA` (default `local/data`) |
| `issuing` | turns engineering outputs into client deliverables: stamped DXF + PDF + workbooks under `deliverables/<emission>/<TR>_Rev<NN>/`, transmittal, ledger, then *confirm sent* |
| `wbs` | work breakdown structure (EDT): dotted-number tree, weights, progress rolled up from the leaves |
| `schedule` | activities with dates and finish-to-start dependencies; critical path, slack, conflicts, late work |
| `backlog` | internal project backlog (tasks, changes, risks, questions, defects); never shown to the customer |
| `knowledge` | API over the knowledge extracted from standards: rules search, topics and checks (via `epc_rules`); see docs/explanation/knowledge.md |
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
Configuration comes from environment variables (`EPC_PROJECTS`, `EPC_ROLE`, `EPC_USER`, `EPC_ORG`, `EPC_ENV`, and for accounts `EPC_AUTH`, `EPC_SIGNUP`, `EPC_DATABASE_URL`, `EPC_SESSION_HOURS`, `EPC_COOKIE_SECURE`, `EPC_PUBLIC_URL`), see `.env.example`.

With `EPC_AUTH=required` (the default when `EPC_ENV=production`) create the first staff account on the server and sign in from the web:
```
python -m epc.modules.identity.cli create-admin --email you@office.com --name "Your Name"
```
