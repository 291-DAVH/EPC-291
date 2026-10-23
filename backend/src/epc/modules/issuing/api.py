from fastapi import APIRouter

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
