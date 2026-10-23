from fastapi import APIRouter
from fastapi.responses import FileResponse

from epc.modules.engineering import service
from epc.modules.engineering.models import CriterionIn
from epc.modules.projects import public as projects

# Internal workspace content (SVG previews, calculation lists): admin/engineer role only, never under /api/app.
router = APIRouter(prefix="/api/projects/{client}/{code}/engineering")

# SVG is previewed through <img>; the sandbox policy also stops scripts if the file is opened directly.
SVG_HEADERS = {"Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'", "X-Content-Type-Options": "nosniff"}


@router.get("")
def engineering_overview(client: str, code: str):
    return service.overview(projects.get_project_dir(client, code))


@router.get("/svg")
def engineering_svg(client: str, code: str, path: str):
    return FileResponse(service.svg_file(projects.get_project_dir(client, code), path), media_type="image/svg+xml", headers=SVG_HEADERS)


@router.get("/text")
def engineering_text(client: str, code: str, path: str):
    return service.text_view(projects.get_project_dir(client, code), path)


# ---- design criteria (editable per project) ----
@router.get("/criteria")
def criteria(client: str, code: str, discipline: str = "electrical"):
    return service.criteria_view(projects.get_project_dir(client, code), discipline)


@router.get("/criteria/report")
def criteria_report(client: str, code: str, discipline: str = "electrical", lang: str = "es"):
    return service.report(projects.get_project_dir(client, code), discipline, lang)


@router.put("/criteria/{key}")
def set_criterion(client: str, code: str, key: str, body: CriterionIn, discipline: str = "electrical"):
    return service.set_criterion(projects.get_project_dir(client, code), discipline, key, body)


@router.delete("/criteria/{key}")
def reset_criterion(client: str, code: str, key: str, discipline: str = "electrical"):
    return service.reset_criterion(projects.get_project_dir(client, code), discipline, key)
