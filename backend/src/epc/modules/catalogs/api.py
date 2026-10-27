from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from epc.modules.catalogs import service
from epc.modules.projects import public as projects

# The company's catalogs sit with its master data (office configuration) and the project's with the project: the role guard that covers those prefixes covers these.
company = APIRouter(prefix="/api/data")
project = APIRouter(prefix="/api/projects/{client}/{code}")


class LayersIn(BaseModel):
    layers: Dict[str, Dict[str, Any]]


class SolutionsIn(BaseModel):
    solutions: Optional[Dict[str, Dict[str, Any]]] = None
    add_ons: Optional[Dict[str, Dict[str, Any]]] = None
    groups: Optional[Dict[str, Dict[str, Any]]] = None


@company.get("/drawing-layers")
def company_layers():
    return service.layers_view("company")


@company.put("/drawing-layers")
def company_layers_save(body: LayersIn):
    return service.layers_save("company", body.layers)


@company.delete("/drawing-layers")
def company_layers_reset():
    return service.layers_reset("company")


@company.get("/standard-solutions")
def company_solutions():
    return service.solutions_view("company")


@company.put("/standard-solutions")
def company_solutions_save(body: SolutionsIn):
    return service.solutions_save("company", body.model_dump())


@company.delete("/standard-solutions")
def company_solutions_reset():
    return service.solutions_reset("company")


@project.get("/drawing-layers")
def project_layers(client: str, code: str):
    return service.layers_view("project", projects.get_project_dir(client, code))


@project.put("/drawing-layers")
def project_layers_save(client: str, code: str, body: LayersIn):
    return service.layers_save("project", body.layers, projects.get_project_dir(client, code))


@project.delete("/drawing-layers")
def project_layers_reset(client: str, code: str):
    return service.layers_reset("project", projects.get_project_dir(client, code))


@project.get("/standard-solutions")
def project_solutions(client: str, code: str):
    return service.solutions_view("project", projects.get_project_dir(client, code))


@project.put("/standard-solutions")
def project_solutions_save(client: str, code: str, body: SolutionsIn):
    return service.solutions_save("project", body.model_dump(), projects.get_project_dir(client, code))


@project.delete("/standard-solutions")
def project_solutions_reset(client: str, code: str):
    return service.solutions_reset("project", projects.get_project_dir(client, code))
