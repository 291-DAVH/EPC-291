"""Request guard: resolves who is calling, then decides what they may reach.

* Staff (`admin`) reach everything.
* A signed-in customer reaches only the public surface (`/api/app/*`, `/api/auth/*`, a few shared paths).
* With `EPC_AUTH=required` an anonymous caller reaches only health, `/api/me` and the sign-in/sign-up/invitation endpoints (401 otherwise).
"""
from typing import Iterable

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from epc.core.config import settings
from epc.modules.identity import service

ANONYMOUS_PATHS = {"/api/health", "/api/me", "/api/auth/login", "/api/auth/signup", "/api/auth/accept-invitation", "/api/auth/invitation"}


def install_role_guard(app: FastAPI, public_paths: Iterable[str], public_prefixes: Iterable[str], public_post_paths: Iterable[str]) -> None:
    paths, prefixes, posts = set(public_paths), tuple(public_prefixes), set(public_post_paths)

    @app.middleware("http")
    async def role_guard(request, call_next):
        principal = await run_in_threadpool(service.principal_for_request, request.cookies.get(service.COOKIE), request.headers.get("authorization"))
        handle = service.activate(principal)
        try:
            path = request.url.path
            if path.startswith("/api/") and request.method != "OPTIONS":
                if settings.auth == "required" and not principal.authenticated and path not in ANONYMOUS_PATHS:
                    return JSONResponse({"detail": "authentication required"}, status_code=401)
                if principal.role != "admin":
                    public = path in paths or path in ANONYMOUS_PATHS or path.startswith(prefixes) or (path in posts and request.method == "POST")
                    if not public:
                        return JSONResponse({"detail": "forbidden"}, status_code=403)
            return await call_next(request)
        finally:
            service.deactivate(handle)
