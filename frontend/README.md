# frontend

React + TypeScript (Vite) in an npm workspace. Two apps over one shared package; both read from the `backend` API.

```
frontend/
  packages/ui/        @epc/ui: API client and types, i18n (es, en), components, theme, Shell, shared form, WbsTree, Gantt, styles
  web/                @epc/web: what the customer sees (port 5173)
    src/features/     portfolio/  project/ (incl. read-only Plan tab: Gantt + WBS; Engineering tab for the admin/engineer role: Files = SVG diagrams and text lists, SLD data = board, titleblock and circuits form that runs the SLD generator; Design criteria = quick editing with origin and history)  new-project/  data/ (Datos: company, clients, people, logos; admin/engineer)
  console/            @epc/console: technical console, admin role only (port 5174)
    src/features/     overview/  plugins/  skills/  rules/  checker/  planning/ (backlog + WBS + schedule)  project-files/
```

## Rules
1. Apps import only `@epc/ui`; `@epc/ui` imports no app; a feature never imports another feature (checked by `tools/ci/check_frontend_boundaries.py`).
2. The end-user app never shows plugins, skills, rules or internal files (ADR-0004); those pages live only in the console, which the API refuses with 403 unless `EPC_ROLE=admin`.
3. UI strings live in `packages/ui/src/i18n.tsx` (es, en). The theme follows the system and can be toggled.

## Run
```
cd frontend
npm install
npm run dev:web        # http://localhost:5173 (proxies /api to :8000)
npm run dev:console    # http://localhost:5174 (run the API with EPC_ROLE=admin)
npm run typecheck      # both apps and the ui package
npm run build          # type-check + production build of both apps
```

## What the end user sees
Projects dashboard (KPIs, filters, cards/table) and a project page with Overview, Deliverables (downloads), Input data (send voice of customer, user stories, notes, files), Requirements and Reports.
