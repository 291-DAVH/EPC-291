from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from epc.modules.layout import service
from epc.modules.layout.models import DrawingIn
from epc.modules.projects import public as projects

# Internal engineering surface (the organization's own projects): never under /api/app.
router = APIRouter(prefix="/api/projects/{client}/{code}/layout")

# The plan underlay may be an SVG: it is shown through <img>, and the policy also stops scripts if the file is opened directly.
SAFE_HEADERS = {"Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'", "X-Content-Type-Options": "nosniff"}


@router.get("")
def overview(client: str, code: str):
    return service.overview(projects.get_project_dir(client, code))


@router.get("/{level}")
def get_level(client: str, code: str, level: str):
    return service.view(projects.get_project_dir(client, code), level)


@router.put("/{level}")
def put_level(client: str, code: str, level: str, body: DrawingIn):
    return service.save(projects.get_project_dir(client, code), level, body)


@router.delete("/{level}")
def delete_level(client: str, code: str, level: str):
    return service.remove(projects.get_project_dir(client, code), level)


@router.post("/{level}/derive")
def derive(client: str, code: str, level: str, body: DrawingIn):
    """What the engine derives from the drawing as it is on the screen, without saving it (tables and warnings while drawing)."""
    return service.derive(projects.get_project_dir(client, code), level, body)


@router.post("/{level}/underlay")
async def post_underlay(client: str, code: str, level: str, file: UploadFile):
    return service.upload_underlay(projects.get_project_dir(client, code), level, file.filename or "", await file.read())


@router.get("/{level}/underlay")
def get_underlay(client: str, code: str, level: str):
    path, media = service.underlay_file(projects.get_project_dir(client, code), level)
    return FileResponse(path, media_type=media, headers=SAFE_HEADERS)


@router.post("/{level}/generate")
def generate(client: str, code: str, level: str, version: str = ""):
    return service.generate(projects.get_project_dir(client, code), level, version)


@router.get("/{level}/files/{name}")
def get_file(client: str, code: str, level: str, name: str):
    path, media = service.output_file(projects.get_project_dir(client, code), level, name)
    return FileResponse(path, media_type=media, filename=name)
