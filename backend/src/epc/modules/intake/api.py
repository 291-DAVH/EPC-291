from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile

from epc.modules.intake import service
from epc.modules.projects import public as projects

router = APIRouter(prefix="/api/app/projects/{client}/{code}/inputs")


@router.get("")
def list_inputs(client: str, code: str):
    return service.list_inputs(projects.get_project_dir(client, code))


@router.post("", status_code=201)
async def add_input(client: str, code: str, kind: str = Form(...), title: str = Form(...), text: str = Form(""),
                    source: str = Form(""), files: Optional[List[UploadFile]] = File(None)):
    d = projects.get_project_dir(client, code)
    payload = [(f.filename, await f.read()) for f in (files or []) if f.filename]
    return service.add_input(d, kind, title, text, source, payload)
