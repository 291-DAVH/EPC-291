from typing import Optional

from fastapi import APIRouter, Query

from epc.modules.knowledge import service
from epc.modules.knowledge.models import CheckRequest

router = APIRouter(prefix="/api/rules")      # admin console only (the role guard blocks end users)


@router.get("/standards")
def standards():
    return service.standards()


@router.get("/topics")
def topics():
    return service.topics()


@router.get("")
def search(standard: Optional[str] = None, topic: Optional[str] = None, q: Optional[str] = None, type: Optional[str] = None,
           installation: Optional[str] = None, only_checks: bool = False, limit: int = Query(300, le=1000)):
    return service.search(standard, topic, q, type, installation, only_checks, limit)


@router.post("/check")
def check(req: CheckRequest):
    return service.check(req)


@router.get("/{rule_id}")
def rule(rule_id: str):
    return service.rule(rule_id)
