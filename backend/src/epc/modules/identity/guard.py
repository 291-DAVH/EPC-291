"""Role guard: end users reach only the public surface; every other /api route needs the admin role."""
from typing import Iterable

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from epc.modules.identity import service


def install_role_guard(app: FastAPI, public_paths: Iterable[str], public_prefixes: Iterable[str], public_post_paths: Iterable[str]) -> None:
    paths, prefixes, posts = set(public_paths), tuple(public_prefixes), set(public_post_paths)

    @app.middleware("http")
    async def role_guard(request, call_next):
        path = request.url.path
        if path.startswith("/api/") and not service.is_admin():
            public = path in paths or path.startswith(prefixes) or (path in posts and request.method == "POST")
            if not public:
                return JSONResponse({"detail": "forbidden"}, status_code=403)
        return await call_next(request)
