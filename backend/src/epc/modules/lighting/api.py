from fastapi import APIRouter

from epc.modules.lighting import service
from epc.modules.lighting.models import CalcIn, LuminairesIn
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/projects/{client}/{code}/lighting")
company = APIRouter(prefix="/api/data")                         # the company's luminaires sit with its master data (office configuration)


@router.get("/options")
def options(client: str, code: str, lang: str = "en"):
    """The choices of the lighting panel: activities, materials, systems, methods and the luminaires in force for the project."""
    return service.options(projects.get_project_dir(client, code), "es" if lang == "es" else "en")


@router.post("/calc")
def calc(client: str, code: str, body: CalcIn):
    """Luminaires for the rooms of a sheet, as a proposal (nothing is saved)."""
    return service.calc(projects.get_project_dir(client, code), body)


@router.get("/luminaires")
def project_luminaires(client: str, code: str):
    return service.luminaires_view("project", projects.get_project_dir(client, code))


@router.put("/luminaires")
def project_luminaires_save(client: str, code: str, body: LuminairesIn):
    return service.luminaires_save("project", body.luminaires, projects.get_project_dir(client, code))


@router.delete("/luminaires")
def project_luminaires_reset(client: str, code: str):
    return service.luminaires_reset("project", projects.get_project_dir(client, code))


@company.get("/luminaires")
def company_luminaires():
    return service.luminaires_view("company")


@company.put("/luminaires")
def company_luminaires_save(body: LuminairesIn):
    return service.luminaires_save("company", body.luminaires)


@company.delete("/luminaires")
def company_luminaires_reset():
    return service.luminaires_reset("company")
