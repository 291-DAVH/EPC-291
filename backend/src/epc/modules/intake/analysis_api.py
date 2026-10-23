from fastapi import APIRouter
from pydantic import BaseModel

from epc.core.errors import Invalid
from epc.modules.intake import analyzer
from epc.modules.projects import public as projects

# Admin/engineer surface (never under /api/app): the customer's text leaves the server for the Claude API, so it needs an explicit confirmation.
router = APIRouter(prefix="/api/projects/{client}/{code}/analysis")


class AnalyzeIn(BaseModel):
    confirm: bool = False


@router.get("")
def analysis_status(client: str, code: str):
    d = projects.get_project_dir(client, code)
    return {"configured": analyzer.configured(), "model": analyzer.model(), "pending": len(analyzer.pending(d)), "usage": analyzer.usage_total(d)}


@router.post("")
def run_analysis(client: str, code: str, body: AnalyzeIn):
    if not body.confirm:
        raise Invalid({"confirm": "the customer's text will be sent to the Claude API: confirm to continue"})
    d = projects.get_project_dir(client, code)
    return analyzer.analyze(d, projects.read_meta(d))
