import os
from typing import Optional

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from epc.modules.deliverables import service
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/app/projects/{client}/{code}/deliverables")


@router.get("")
def list_deliverables(client: str, code: str):
    return service.list_items(projects.get_project_dir(client, code))


@router.get("/packages")
def list_packages(client: str, code: str):
    return service.packages(projects.get_project_dir(client, code))


@router.get("/package")
def download_package(client: str, code: str, group: Optional[str] = None):
    path, filename = service.package_zip(projects.get_project_dir(client, code), group)
    return FileResponse(path, filename=filename, media_type="application/zip", background=BackgroundTask(os.unlink, path))


@router.get("/{item_id}/download")
def download_deliverable(client: str, code: str, item_id: str, format: Optional[str] = None):
    path, filename = service.file_for(projects.get_project_dir(client, code), item_id, format)
    return FileResponse(path, filename=filename)
