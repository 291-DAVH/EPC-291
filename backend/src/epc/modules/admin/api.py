from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from epc.modules.admin import service

router = APIRouter(prefix="/api")      # every route here is admin-only (the role guard blocks end users)


@router.get("/overview")
def overview():
    return service.overview()


@router.get("/plugins")
def plugins():
    return service.plugins()


@router.get("/plugins/{pid}")
def plugin(pid: str):
    return service.plugin(pid)


@router.get("/skills")
def skills():
    return service.skills()


@router.get("/policy")
def policy():
    return service.policy()


@router.get("/projects/{project_id:path}/tree")
def project_tree(project_id: str, area: str = "workspace", depth: int = 3):
    return service.project_tree(project_id, area, depth)


class LayersIn(BaseModel):
    layers: Dict[str, Dict[str, Any]]


@router.get("/layers")
def layers():
    return service.layers()


@router.put("/layers")
def save_layers(body: LayersIn):
    return service.save_layers(body.layers)


@router.delete("/layers")
def reset_layers():
    return service.reset_layers()
