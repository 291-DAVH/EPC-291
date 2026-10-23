from fastapi import APIRouter

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
