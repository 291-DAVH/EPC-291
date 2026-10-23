from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from epc.modules.masterdata import service
from epc.modules.masterdata.models import ClientIn, OrganizationIn, PersonIn

# Master data is configuration of the office: admin/engineer role only (never under /api/app).
router = APIRouter(prefix="/api/data")
LOGO_HEADERS = {"Content-Security-Policy": "sandbox; default-src 'none'; style-src 'unsafe-inline'", "X-Content-Type-Options": "nosniff"}


@router.get("/organization")
def get_organization():
    return service.organization()


@router.put("/organization")
def put_organization(body: OrganizationIn):
    return service.save_organization(body)


@router.get("/clients")
def list_clients():
    return service.clients()


@router.post("/clients", status_code=201)
def add_client(body: ClientIn):
    return service.add_client(body)


@router.put("/clients/{cid}")
def update_client(cid: str, body: ClientIn):
    return service.update_client(cid, body)


@router.delete("/clients/{cid}", status_code=204)
def delete_client(cid: str):
    service.delete_client(cid)


@router.get("/people")
def list_people():
    return service.people()


@router.post("/people", status_code=201)
def add_person(body: PersonIn):
    return service.save_person(body)


@router.put("/people/{pid}")
def update_person(pid: str, body: PersonIn):
    return service.save_person(body, pid)


@router.delete("/people/{pid}", status_code=204)
def delete_person(pid: str):
    service.delete_person(pid)


@router.post("/logos/{kind}", status_code=201)
async def upload_logo(kind: str, file: UploadFile = File(...)):
    return service.save_logo(kind, file.filename or "", await file.read())


@router.get("/logos/{kind}")
def get_logo(kind: str):
    path = service.logo_file(kind)
    return FileResponse(path, media_type="image/svg+xml" if path.suffix == ".svg" else "image/png", headers=LOGO_HEADERS)


@router.delete("/logos/{kind}", status_code=204)
def delete_logo(kind: str):
    service.delete_logo(kind)
