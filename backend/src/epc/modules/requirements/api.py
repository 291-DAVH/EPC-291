from fastapi import APIRouter
from pydantic import BaseModel

from epc.modules.projects import public as projects
from epc.modules.requirements import service

router = APIRouter(prefix="/api/app/projects/{client}/{code}/requirements")


class AnswerIn(BaseModel):
    question: str
    answer: str


@router.get("")
def list_requirements(client: str, code: str):
    return service.list_requirements(projects.get_project_dir(client, code))


@router.post("/{req_id}/answer")
def answer_question(client: str, code: str, req_id: str, body: AnswerIn):
    """Answer an open question: the answer is stored with who answered and when."""
    return service.answer_question(projects.get_project_dir(client, code), req_id, body.question, body.answer)
