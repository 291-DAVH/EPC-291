import os
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse

from epc.modules.projects import public as projects
from epc.modules.reporting import service
from epc.modules.reporting.models import GenerateIn

# Management reports are produced by the engineer/admin; the client only sees the ones published to the Reports list (under /api/app).
router = APIRouter(prefix="/api/projects/{client}/{code}/reporting")


@router.get("")
def overview(client: str, code: str, lang: Optional[str] = None):
    return service.overview(projects.get_project_dir(client, code), lang)


@router.post("", status_code=201)
def generate(client: str, code: str, body: GenerateIn):
    return service.generate(projects.get_project_dir(client, code), body)


@router.get("/{rid}/file")
def download(client: str, code: str, rid: str, format: str = "pdf"):
    path, name = service.file_for(projects.get_project_dir(client, code), rid, format)
    return FileResponse(path, filename=name, media_type="application/pdf" if format == "pdf" else "text/markdown; charset=utf-8")


@router.post("/{rid}/publish")
def publish(client: str, code: str, rid: str):
    return service.publish(projects.get_project_dir(client, code), rid)
