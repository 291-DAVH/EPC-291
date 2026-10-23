from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.schedule import service
from epc.modules.schedule.models import ScheduleIn

router = APIRouter()


@router.get("/api/app/projects/{client}/{code}/schedule")
def get_schedule(client: str, code: str):
    return service.view(projects.get_project_dir(client, code))


@router.put("/api/projects/{client}/{code}/schedule")
def put_schedule(client: str, code: str, body: ScheduleIn):
    return service.replace(projects.get_project_dir(client, code), body)
