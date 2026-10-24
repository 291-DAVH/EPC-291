import os
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from epc.modules.issuing import service
from epc.modules.issuing.models import IssueIn
from epc.modules.projects import public as projects

# Issuing is an engineer action: admin/engineer role only (the client only sees the result under /api/app/.../deliverables).
router = APIRouter(prefix="/api/projects/{client}/{code}/issuing")


@router.get("")
def candidates(client: str, code: str):
    return service.candidates(projects.get_project_dir(client, code))


@router.post("", status_code=201)
def issue(client: str, code: str, body: IssueIn):
    return service.issue(projects.get_project_dir(client, code), body)


@router.get("/{tr_id}")
def transmittal(client: str, code: str, tr_id: str):
    return service.get(projects.get_project_dir(client, code), tr_id)


@router.post("/{tr_id}/sent")
def sent(client: str, code: str, tr_id: str):
    return service.mark_sent(projects.get_project_dir(client, code), tr_id)


@router.get("/{tr_id}/message")
def message(client: str, code: str, tr_id: str, lang: Optional[str] = None):
    """Email text for sending the delivery (subject and body, formal third person)."""
    return service.message(projects.get_project_dir(client, code), tr_id, lang)


@router.get("/{tr_id}/document")
def document(client: str, code: str, tr_id: str, lang: Optional[str] = None):
    path, name = service.transmittal_pdf(projects.get_project_dir(client, code), tr_id, lang)
    return FileResponse(path, filename=name, media_type="application/pdf", background=BackgroundTask(os.unlink, path))


@router.get("/{tr_id}/package")
def package(client: str, code: str, tr_id: str, lang: Optional[str] = None):
    """ZIP with the transmittal's files, the transmittal document and INDICE.csv."""
    path, name = service.package(projects.get_project_dir(client, code), tr_id, lang)
    return FileResponse(path, filename=name, media_type="application/zip", background=BackgroundTask(os.unlink, path))
