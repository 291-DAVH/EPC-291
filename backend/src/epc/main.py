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
from epc.modules.backlog import api as backlog_api
from epc.modules.deliverables import api as deliverables_api
from epc.modules.engineering import api as engineering_api
from epc.modules.identity import api as identity_api
from epc.modules.identity import public as identity
from epc.modules.intake import analysis_api as intake_analysis_api
from epc.modules.intake import api as intake_api
from epc.modules.issuing import api as issuing_api
from epc.modules.knowledge import api as knowledge_api
from epc.modules.management import api as management_api
from epc.modules.masterdata import api as masterdata_api
from epc.modules.norms import api as norms_api
from epc.modules.projects import api as projects_api
from epc.modules.projects import public as projects
from epc.modules.registers import api as registers_api
from epc.modules.reporting import api as reporting_api
from epc.modules.requirements import api as requirements_api
from epc.modules.schedule import api as schedule_api
from epc.modules.layout import api as layout_api
from epc.modules.sld import api as sld_api
from epc.modules.wbs import api as wbs_api

PUBLIC_PREFIXES = ("/api/app/", "/api/auth/")            # the end-user surface (plus sign-in and account endpoints)


def create_app() -> FastAPI:
    app = FastAPI(title="EPC-291 API", version="0.3.0")
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
                       allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
    identity.install_role_guard(app, public_paths=identity.PUBLIC_PATHS | projects.PUBLIC_PATHS,
                                public_prefixes=PUBLIC_PREFIXES, public_post_paths=projects.PUBLIC_POST_PATHS)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.path.startswith(("/api/auth/", "/api/me", "/api/identity/", "/api/norms/")):
            response.headers["Cache-Control"] = "no-store"                    # account data is never kept by a cache
        if settings.cookie_secure:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response

    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)

    @app.get("/api/health")
    def health():
        return {"ok": True, "env": settings.env}

    for module_api in (identity_api, projects_api, management_api, deliverables_api, intake_api, intake_analysis_api, requirements_api, engineering_api, issuing_api, registers_api, reporting_api, sld_api, layout_api, masterdata_api, norms_api, wbs_api, schedule_api, backlog_api, knowledge_api, admin_api):
        app.include_router(module_api.router)
    app.include_router(masterdata_api.parties_router)             # who issues and who signs each project (staff)
    app.include_router(registers_api.observations)               # customer-surface routes of the registers module
    return app


app = create_app()
