"""Composition root: builds the FastAPI app from the modules.

Run (from the repository root, engine on PYTHONPATH or installed):
  uvicorn epc.main:app --app-dir backend/src --port 8000 [--reload]
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from epc.core.config import settings
from epc.core.errors import DomainError
from epc.modules.admin import api as admin_api
from epc.modules.deliverables import api as deliverables_api
from epc.modules.identity import api as identity_api
from epc.modules.identity import public as identity
from epc.modules.intake import api as intake_api
from epc.modules.knowledge import api as knowledge_api
from epc.modules.management import api as management_api
from epc.modules.projects import api as projects_api
from epc.modules.projects import public as projects
from epc.modules.requirements import api as requirements_api

PUBLIC_PREFIXES = ("/api/app/",)            # the end-user surface


def create_app() -> FastAPI:
    app = FastAPI(title="EPC-291 API", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])
    identity.install_role_guard(app, public_paths=identity.PUBLIC_PATHS | projects.PUBLIC_PATHS,
                                public_prefixes=PUBLIC_PREFIXES, public_post_paths=projects.PUBLIC_POST_PATHS)

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)

    @app.get("/api/health")
    def health():
        return {"ok": True, "env": settings.env}

    for module_api in (identity_api, projects_api, management_api, deliverables_api, intake_api, requirements_api, knowledge_api, admin_api):
        app.include_router(module_api.router)
    return app


app = create_app()
