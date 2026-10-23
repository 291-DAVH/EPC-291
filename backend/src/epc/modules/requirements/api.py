from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.requirements import service

router = APIRouter(prefix="/api/app/projects/{client}/{code}/requirements")


@router.get("")
def list_requirements(client: str, code: str):
    return service.list_requirements(projects.get_project_dir(client, code))
