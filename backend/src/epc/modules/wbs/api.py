from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.wbs import service
from epc.modules.wbs.models import WbsIn

router = APIRouter()


@router.get("/api/app/projects/{client}/{code}/wbs")
def get_wbs(client: str, code: str):
    return service.view(projects.get_project_dir(client, code))


@router.put("/api/projects/{client}/{code}/wbs")
def put_wbs(client: str, code: str, body: WbsIn):
    return service.replace(projects.get_project_dir(client, code), body)
