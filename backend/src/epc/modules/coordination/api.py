from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from epc.modules.coordination import detection, exchanges, rules, service, threads
from epc.modules.projects import public as projects

# Internal engineering surface (the organization's own projects): never under /api/app.
router = APIRouter(prefix="/api/projects/{client}/{code}/coordination")
company = APIRouter(prefix="/api/data")


class EmitIn(BaseModel):
    discipline: str
    note: str = ""


class StatusIn(BaseModel):
    status: str
    reason: str = ""


class RulesIn(BaseModel):
    rules: List[Dict[str, Any]]


class MembersIn(BaseModel):
    members: Dict[str, List[str]]


class SettingsIn(BaseModel):
    story_height_m: float


class ThreadIn(BaseModel):
    kind: str
    from_discipline: str
    to_discipline: str = ""
    title: str = ""
    text: str = ""
    sheet: str = ""
    level: str = ""
    point_m: Optional[List[float]] = None
    geom: Optional[Dict[str, Any]] = None


class AnswerIn(BaseModel):
    status: str = ""
    comment: str = ""


class ExchangeIn(BaseModel):
    owner: str
    consumers: List[str]
    tag: str
    field: str
    value: Any
    unit: str = ""


class AckIn(BaseModel):
    discipline: str


def _dir(client: str, code: str):
    return projects.get_project_dir(client, code)


@router.get("")
def overview(client: str, code: str):
    return service.overview(_dir(client, code))


@router.post("/emit")
def emit(client: str, code: str, body: EmitIn):
    return service.emit(_dir(client, code), body.discipline, body.note)


@router.get("/clashes")
def clashes(client: str, code: str, source: str = "auto"):
    return detection.detect(_dir(client, code), source)


@router.put("/clashes/{clash_id}")
def clash_status(client: str, code: str, clash_id: str, body: StatusIn):
    return detection.set_status(_dir(client, code), clash_id, body.status, body.reason)


@router.get("/reference")
def reference(client: str, code: str, discipline: str, level: str, source: str = "auto"):
    """What the other disciplines occupy on a level (footprints only), for the editor to show behind the drawing."""
    return {"items": detection.reference(_dir(client, code), discipline, level, source), "settings": detection.settings(_dir(client, code))}


@router.get("/notifications")
def notifications(client: str, code: str, discipline: str):
    return service.notifications(_dir(client, code), discipline)


@router.get("/settings")
def get_settings(client: str, code: str):
    return detection.settings(_dir(client, code))


@router.put("/settings")
def put_settings(client: str, code: str, body: SettingsIn):
    return detection.save_settings(_dir(client, code), body.story_height_m)


@router.get("/members")
def get_members(client: str, code: str):
    return service.members(_dir(client, code))


@router.put("/members")
def put_members(client: str, code: str, body: MembersIn):
    return service.set_members(_dir(client, code), body.members)


@router.get("/rules")
def project_rules(client: str, code: str):
    return rules.view("project", _dir(client, code))


@router.put("/rules")
def project_rules_save(client: str, code: str, body: RulesIn):
    return rules.save("project", body.rules, _dir(client, code))


@router.delete("/rules")
def project_rules_reset(client: str, code: str):
    return rules.save("project", [], _dir(client, code))


@router.get("/threads")
def list_threads(client: str, code: str, level: str = "", discipline: str = "", status: str = ""):
    return threads.listing(_dir(client, code), level, discipline, status)


@router.post("/threads", status_code=201)
def create_thread(client: str, code: str, body: ThreadIn):
    return threads.create(_dir(client, code), body.model_dump())


@router.patch("/threads/{thread_id}")
def answer_thread(client: str, code: str, thread_id: str, body: AnswerIn):
    return threads.update(_dir(client, code), thread_id, body.model_dump())


@router.delete("/threads/{thread_id}", status_code=204)
def delete_thread(client: str, code: str, thread_id: str):
    threads.remove(_dir(client, code), thread_id)


@router.get("/exchanges")
def list_exchanges(client: str, code: str):
    return {"items": exchanges.listing(_dir(client, code)), "matrix": exchanges.matrix(_dir(client, code))}


@router.post("/exchanges", status_code=201)
def publish_exchange(client: str, code: str, body: ExchangeIn):
    return exchanges.publish(_dir(client, code), body.model_dump())


@router.post("/exchanges/{exchange_id}/take")
def take_exchange(client: str, code: str, exchange_id: str, body: AckIn):
    return exchanges.acknowledge(_dir(client, code), exchange_id, body.discipline)


@router.delete("/exchanges/{exchange_id}", status_code=204)
def delete_exchange(client: str, code: str, exchange_id: str):
    exchanges.remove(_dir(client, code), exchange_id)


@company.get("/clash-rules")
def company_rules():
    return rules.view("company")


@company.put("/clash-rules")
def company_rules_save(body: RulesIn):
    return rules.save("company", body.rules)


@company.delete("/clash-rules")
def company_rules_reset():
    return rules.save("company", [])
