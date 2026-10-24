from typing import Optional

from fastapi import APIRouter, Body

from epc.modules.projects import public as projects
from epc.modules.registers import service

# Registers are kept by the engineer/admin; the client sees their effect through the reports that are published to them.
router = APIRouter(prefix="/api/projects/{client}/{code}/registers")


@router.get("")
def view(client: str, code: str, lang: Optional[str] = None):
    return service.view(projects.get_project_dir(client, code), lang)


@router.get("/{kind}")
def items(client: str, code: str, kind: str):
    return service.items(projects.get_project_dir(client, code), kind)


@router.post("/{kind}", status_code=201)
def create(client: str, code: str, kind: str, body: dict = Body(...)):
    return service.create(projects.get_project_dir(client, code), kind, body)


@router.patch("/{kind}/{item_id}")
def update(client: str, code: str, kind: str, item_id: str, body: dict = Body(...)):
    return service.update(projects.get_project_dir(client, code), kind, item_id, body)


# Observations live on the customer surface: inspectors and auditors (assigned organizations only) write them, the customer's managers answer.
observations = APIRouter(prefix="/api/app/projects/{client}/{code}/observations")


@observations.get("/definition")
def observation_definition(client: str, code: str, lang: Optional[str] = None):
    return service.observation_definition(projects.get_project_dir(client, code), lang)


@observations.get("")
def list_observations(client: str, code: str):
    return service.items(projects.get_project_dir(client, code), "observation")


@observations.post("", status_code=201)
def create_observation(client: str, code: str, body: dict = Body(...)):
    return service.create_observation(projects.get_project_dir(client, code), body)


@observations.patch("/{item_id}")
def update_observation(client: str, code: str, item_id: str, body: dict = Body(...)):
    return service.update_observation(projects.get_project_dir(client, code), item_id, body)
