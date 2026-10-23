from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.sld import service
from epc.modules.sld.models import SldIn

# Internal engineering surface: admin/engineer role only (never under /api/app).
router = APIRouter(prefix="/api/projects/{client}/{code}/sld")


@router.get("")
def get_sld(client: str, code: str):
    return service.view(projects.get_project_dir(client, code))


@router.put("")
def put_sld(client: str, code: str, body: SldIn):
    return service.save(projects.get_project_dir(client, code), body)


@router.get("/example")
def get_example(client: str, code: str):
    projects.get_project_dir(client, code)
    return service.example()


@router.post("/generate", status_code=202)
def generate(client: str, code: str):
    return service.generate(projects.get_project_dir(client, code))


@router.get("/status")
def get_status(client: str, code: str):
    return service.status(projects.get_project_dir(client, code))
