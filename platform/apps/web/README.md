# web

React + TypeScript (Vite) front for the EPC platform. Reads from the `backend` API.

Pages: Dashboard, Plugins, Skills, Rules (browser + detail), Checker (run rules against installation data), Projects (workspace vs deliverables tree).
UI strings: `src/i18n.tsx` (es, en). Theme follows the system and can be toggled.

```
cd apps/web
npm install
npm run dev          # http://localhost:5173 (proxies /api to :8000)
npm run build        # type-check + production build
```

## What the end user sees
Projects dashboard (KPIs, filters, cards/table) and a project page with Overview, Deliverables (downloads), Input data (send voice of customer, user stories, notes, files), Requirements and Reports. Plugins, skills, rules and internal files are never shown; the technical console exists only for the admin role (`/admin`).
