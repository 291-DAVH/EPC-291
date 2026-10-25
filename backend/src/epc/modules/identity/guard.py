"""Request guard: resolves who is calling, then decides what they may reach from the permission matrix (permissions.py).

* Anonymous callers reach only health, `/api/me` and the sign-in, sign-up and invitation endpoints (401 otherwise, when accounts are required).
* Everyone signed in reaches `/api/auth/*` (their own session and password).
* Anything else needs the matching ability: staff everything, the norm reviewer the norms, an inspector or auditor the customer surface in read-only (and observations),
  a customer the customer surface and, if they manage the organization, its people.
"""
from typing import Iterable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from epc.core.config import settings
from epc.modules.identity import permissions, service

ANONYMOUS_PATHS = {"/api/health", "/api/me", "/api/auth/login", "/api/auth/signup", "/api/auth/accept-invitation", "/api/auth/invitation", "/api/auth/providers",
                   "/api/auth/countries", "/api/auth/terms", "/api/auth/company/register", "/api/auth/company/verify", "/api/auth/company/resend"}
ANONYMOUS_PREFIXES = ("/api/auth/oauth/",)           # sign-in and sign-up with a provider: the routes decide what each step needs


def install_role_guard(app: FastAPI, public_paths: Iterable[str], public_prefixes: Iterable[str], public_post_paths: Iterable[str]) -> None:
    app_paths, app_posts = set(public_paths), set(public_post_paths)

    @app.middleware("http")
    async def role_guard(request, call_next):
        principal = await run_in_threadpool(service.principal_for_request, request.cookies.get(service.COOKIE), request.headers.get("authorization"))
        handle = service.activate(principal)
        try:
            path = request.url.path
            if path.startswith("/api/") and request.method != "OPTIONS" and path not in ANONYMOUS_PATHS and not path.startswith(ANONYMOUS_PREFIXES):
                if settings.auth == "required" and not principal.authenticated:
                    return JSONResponse({"detail": "authentication required"}, status_code=401)
                subject = permissions.subject_of(path, request.method, app_paths, app_posts)
                if subject is not None and not permissions.allowed(service.account_type(principal), subject, request.method):
                    return JSONResponse({"detail": "forbidden"}, status_code=403)
            return await call_next(request)
        finally:
            service.deactivate(handle)
