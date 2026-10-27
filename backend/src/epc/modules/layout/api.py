from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse

from epc.modules.layout import service, templates
from epc.modules.layout.models import ArchIn, DesignIn, DrawingIn, NewCircuits, TemplateIn
from epc.modules.projects import public as projects

# Internal engineering surface (the organization's own projects): never under /api/app.
router = APIRouter(prefix="/api/projects/{client}/{code}/layout")

templates_router = APIRouter(prefix="/api/projects/{client}/{code}/layout-templates")
layers_router = APIRouter(prefix="/api/projects/{client}/{code}/layout-layers")

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


@router.get("/{level}/history")
def history(client: str, code: str, level: str):
    return service.history(projects.get_project_dir(client, code), level)


@router.get("/{level}/history/{snapshot}")
def history_snapshot(client: str, code: str, level: str, snapshot: str):
    return service.snapshot(projects.get_project_dir(client, code), level, snapshot)


@router.post("/{level}/history/{snapshot}/restore")
def history_restore(client: str, code: str, level: str, snapshot: str):
    return service.restore(projects.get_project_dir(client, code), level, snapshot)


@router.post("/{level}/architecture")
def recognize_architecture(client: str, code: str, level: str, body: ArchIn):
    """Walls, doors and windows of the plan that was uploaded (DXF, PDF or image), found by the architecture engine."""
    return service.recognize_architecture(projects.get_project_dir(client, code), level, body.units_per_metre)


@router.get("/{level}/architecture")
def get_architecture(client: str, code: str, level: str):
    return service.architecture(projects.get_project_dir(client, code), level)


@router.delete("/{level}/architecture")
def delete_architecture(client: str, code: str, level: str):
    return service.remove_architecture(projects.get_project_dir(client, code), level)


@router.post("/{level}/design/runs")
def design_runs(client: str, code: str, level: str, body: DesignIn):
    """Step 1: straight trunks and conduits proposed for the loads of the drawing (nothing is saved)."""
    return service.design_runs(projects.get_project_dir(client, code), level, body)


@router.post("/{level}/design/wiring")
def design_wiring(client: str, code: str, level: str, body: DesignIn):
    """Step 2: circuits by room over the runs already drawn (nothing is saved)."""
    return service.design_wiring(projects.get_project_dir(client, code), level, body)


@router.post("/{level}/design/circuits")
def design_circuits(client: str, code: str, level: str, body: NewCircuits):
    """Create in the board the circuits of an accepted proposal."""
    return service.accept_circuits(projects.get_project_dir(client, code), level, body.circuits)


@router.get("/{level}/changes")
def changes(client: str, code: str, level: str):
    """What changed in the drawing since its files were last made."""
    return service.changes_since_files(projects.get_project_dir(client, code), level)


@router.post("/{level}/generate")
def generate(client: str, code: str, level: str, version: str = ""):
    return service.generate(projects.get_project_dir(client, code), level, version)


@router.get("/{level}/files/{name}")
def get_file(client: str, code: str, level: str, name: str):
    path, media = service.output_file(projects.get_project_dir(client, code), level, name)
    return FileResponse(path, media_type=media, filename=name)


@templates_router.get("")
def list_templates(client: str, code: str):
    return templates.listing(projects.get_project_dir(client, code))


@templates_router.put("/{name}")
def save_template(client: str, code: str, name: str, body: TemplateIn):
    return templates.save(projects.get_project_dir(client, code), name, body)


@templates_router.delete("/{name}", status_code=204)
def delete_template(client: str, code: str, name: str):
    templates.remove(projects.get_project_dir(client, code), name)


@layers_router.get("")
def layers_by_discipline(client: str, code: str):
    """The DXF layers in force for the project, by discipline."""
    return service.layers_by_discipline(projects.get_project_dir(client, code))
