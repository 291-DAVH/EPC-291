from fastapi import APIRouter
from fastapi.responses import FileResponse

from epc.modules.deliverables import service
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/app/projects/{client}/{code}/deliverables")


@router.get("")
def list_deliverables(client: str, code: str):
    return service.list_items(projects.get_project_dir(client, code))


@router.get("/{item_id}/download")
def download_deliverable(client: str, code: str, item_id: str):
    path, filename = service.file_for(projects.get_project_dir(client, code), item_id)
    return FileResponse(path, filename=filename)
