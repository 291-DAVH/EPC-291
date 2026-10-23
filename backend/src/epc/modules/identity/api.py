from fastapi import APIRouter

from epc.modules.identity import service

router = APIRouter()


@router.get("/api/me")
def me():
    return service.current_user()
