from fastapi import APIRouter
from fastapi.responses import FileResponse

from epc.modules.management import service
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/app")


@router.get("/portfolio")
def portfolio():
    return service.portfolio()


@router.get("/projects/{client}/{code}")
def project_detail(client: str, code: str):
    return service.detail(projects.get_project_dir(client, code))


@router.get("/projects/{client}/{code}/reports")
def list_reports(client: str, code: str):
    return service.reports(projects.get_project_dir(client, code))


@router.get("/projects/{client}/{code}/reports/{report_id}/download")
def download_report(client: str, code: str, report_id: str):
    path, filename = service.report_file(projects.get_project_dir(client, code), report_id)
    return FileResponse(path, filename=filename)
