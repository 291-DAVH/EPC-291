from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.receptacles import service, study
from epc.modules.receptacles.models import CalcIn, ReceptaclesIn

router = APIRouter(prefix="/api/projects/{client}/{code}/receptacles")
company = APIRouter(prefix="/api/data")                         # the company's outlets sit with its master data (office configuration)


@router.get("/options")
def options(client: str, code: str, lang: str = "en"):
    """The choices of the receptacles panel: the uses of a room, the outlets in force for the project and the sections of the norm."""
    return service.options(projects.get_project_dir(client, code), "es" if lang == "es" else "en")


@router.post("/calc")
def calc(client: str, code: str, body: CalcIn):
    """Outlets for the rooms of a sheet, as a proposal (nothing is saved)."""
    return service.calc(projects.get_project_dir(client, code), body)


@router.get("/study/{sheet}")
def study_view(client: str, code: str, sheet: str):
    """The study kept with the sheet and whether it is still good for the rooms as they are drawn now."""
    return study.view(projects.get_project_dir(client, code), sheet)


@router.put("/study/{sheet}")
def study_save(client: str, code: str, sheet: str, body: CalcIn):
    """Calculate and keep the study of the sheet (and make its report)."""
    return study.save(projects.get_project_dir(client, code), sheet, body)


@router.post("/study/{sheet}/remake")
def study_remake(client: str, code: str, sheet: str, lang: str = "en"):
    """Calculate the study of the sheet again from the drawing as it is saved, keep it and make its report: what the Memorias screen asks."""
    return study.remake(projects.get_project_dir(client, code), sheet, "es" if lang == "es" else "en")


@router.post("/study/{sheet}/report")
def study_report(client: str, code: str, sheet: str, lang: str = "en"):
    """The report of the study as a Markdown document among the documents of the project (its PDF is made when it is issued)."""
    return study.make_report(projects.get_project_dir(client, code), sheet, "es" if lang == "es" else "en")


@router.get("/catalogue")
def project_catalogue(client: str, code: str):
    return service.receptacles_view("project", projects.get_project_dir(client, code))


@router.put("/catalogue")
def project_catalogue_save(client: str, code: str, body: ReceptaclesIn):
    return service.receptacles_save("project", body.receptacles, projects.get_project_dir(client, code))


@router.delete("/catalogue")
def project_catalogue_reset(client: str, code: str):
    return service.receptacles_reset("project", projects.get_project_dir(client, code))


@company.get("/receptacles")
def company_catalogue():
    return service.receptacles_view("company")


@company.put("/receptacles")
def company_catalogue_save(body: ReceptaclesIn):
    return service.receptacles_save("company", body.receptacles)


@company.delete("/receptacles")
def company_catalogue_reset():
    return service.receptacles_reset("company")
