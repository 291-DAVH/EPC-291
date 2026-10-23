# api

FastAPI service over the hub registry, skills, rules engine and projects folder (read-only for now).

```
# from platform/
.venv\Scripts\python -m uvicorn apps.api.main:app --reload --port 8000
```
Env: `EPC_ENV` (dev|production; production hides draft rules), `EPC_DEV_KNOWLEDGE`, `EPC_PROJECTS`.
Endpoints: `/api/overview`, `/api/plugins[/{id}]`, `/api/skills`, `/api/rules`, `/api/rules/{id}`, `/api/rules/standards`, `/api/rules/topics`, `POST /api/rules/check`, `/api/projects`, `POST /api/projects` (create from _template + plugins.lock), `/api/projects/options`, `/api/projects/{id}/tree`, `/api/policy`.

## Roles
`EPC_ROLE=user` (default): only `/api/app/*`, `/api/me`, `/api/health`, project options and `POST /api/projects`. Plugins, skills, rules, workspace trees and the rest answer 403 and are invisible in the web app.
`EPC_ROLE=admin`: everything, and the web app shows the technical console under `/admin`.
Demo data: `python tools/dev/seed_demo.py` creates 20 simulated projects in `../projects-demo`; run the API with `--env-file .env.demo` (user) or `.env.admin`.
