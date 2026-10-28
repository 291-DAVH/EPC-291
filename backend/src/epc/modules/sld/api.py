from fastapi import APIRouter

from epc.modules.projects import public as projects
from epc.modules.sld import service
from epc.modules.sld.models import BoardIn, SldIn

# Internal engineering surface: admin/engineer role only (never under /api/app).
router = APIRouter(prefix="/api/projects/{client}/{code}/sld")


# Every route works on one board of the project: `?board=<id>` (without it, the first board).
@router.get("/boards")
def list_boards(client: str, code: str):
    return service.boards(projects.get_project_dir(client, code))


@router.post("/boards", status_code=201)
def add_board(client: str, code: str, body: BoardIn):
    return service.create_board(projects.get_project_dir(client, code), body.name, body.supplied_from, body.supply_tag, body.level, body.location)


@router.delete("/boards/{board}")
def delete_board(client: str, code: str, board: str):
    return service.remove_board(projects.get_project_dir(client, code), board)


@router.get("")
def get_sld(client: str, code: str, board: str = ""):
    return service.view(projects.get_project_dir(client, code), board)


@router.put("")
def put_sld(client: str, code: str, body: SldIn, board: str = ""):
    return service.save(projects.get_project_dir(client, code), body, board)


@router.get("/example")
def get_example(client: str, code: str):
    projects.get_project_dir(client, code)
    return service.example()


@router.post("/generate", status_code=202)
def generate(client: str, code: str, diagrams: str = "sld", board: str = ""):
    """diagrams: sld (default), mld or sld,mld. The calculation, governed by the design criteria, is redone every time."""
    return service.generate(projects.get_project_dir(client, code), diagrams=diagrams, bid=board)


@router.get("/calculation")
def get_calculation(client: str, code: str, board: str = ""):
    return service.calculation(projects.get_project_dir(client, code), board)


@router.get("/memo")
def get_memo(client: str, code: str, board: str = ""):
    return service.memo(projects.get_project_dir(client, code), board)


@router.get("/status")
def get_status(client: str, code: str, board: str = ""):
    return service.status(projects.get_project_dir(client, code), board)
