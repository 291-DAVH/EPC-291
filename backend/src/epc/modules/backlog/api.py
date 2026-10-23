from fastapi import APIRouter

from epc.modules.backlog import service
from epc.modules.backlog.models import ItemPatch, NewItem
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/projects/{client}/{code}/backlog")


@router.get("")
def list_backlog(client: str, code: str):
    return service.view(projects.get_project_dir(client, code))


@router.post("", status_code=201)
def add_item(client: str, code: str, body: NewItem):
    return service.create(projects.get_project_dir(client, code), body)


@router.patch("/{item_id}")
def patch_item(client: str, code: str, item_id: str, body: ItemPatch):
    return service.update(projects.get_project_dir(client, code), item_id, body)
