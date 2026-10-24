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
