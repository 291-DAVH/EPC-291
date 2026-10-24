from typing import Optional

from fastapi import APIRouter, Body
from pydantic import BaseModel

from epc.modules.norms import service

# Norm review: norm reviewer and engineering staff only (the guard blocks customers).
router = APIRouter(prefix="/api/norms")


class EditIn(BaseModel):
    patch: dict
    note: str = ""
    approve: bool = False


class NoteIn(BaseModel):
    note: str = ""


@router.get("/units")
def units():
    return service.units()


@router.get("/log")
def log(limit: int = 100):
    return service.log(limit)


@router.get("/units/{unit_id}/points")
def points(unit_id: str, status: Optional[str] = None, q: Optional[str] = None):
    return service.points(unit_id, status, q)


@router.get("/units/{unit_id}/points/{key}")
def point(unit_id: str, key: str):
    return service.point(unit_id, key)


@router.put("/units/{unit_id}/points/{key}")
def edit(unit_id: str, key: str, body: EditIn):
    return service.edit(unit_id, key, body.patch, body.note, body.approve)


@router.post("/units/{unit_id}/points/{key}/approve")
def approve(unit_id: str, key: str, body: NoteIn = Body(default=NoteIn())):
    return service.approve(unit_id, key, body.note)


@router.post("/units/{unit_id}/points/{key}/reject")
def reject(unit_id: str, key: str, body: NoteIn):
    return service.reject(unit_id, key, body.note)
