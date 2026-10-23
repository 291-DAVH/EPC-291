from fastapi import APIRouter
from pydantic import BaseModel

from epc.modules.projects import service
from epc.modules.projects.models import NewProject

router = APIRouter()


@router.get("/api/projects")
def list_projects():
    """Admin console: every project with file counts."""
    return service.admin_list()


@router.get("/api/projects/options")
def project_options():
    return service.options()


@router.post("/api/projects", status_code=201)
def create_project(p: NewProject):
    return service.create(p)


class OrgIn(BaseModel):
    org: str = ""


@router.put("/api/projects/{client}/{code}/org")
def set_project_org(client: str, code: str, body: OrgIn):
    """Staff: assign the project to an organization (empty = unassigned)."""
    return service.set_org(client, code, body.org)
