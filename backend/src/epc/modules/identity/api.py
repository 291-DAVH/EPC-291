from typing import Optional

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from epc.core.config import settings
from epc.modules.identity import service

router = APIRouter()


class LoginIn(BaseModel):
    email: str
    password: str
    org: str = ""


class SignupIn(BaseModel):
    kind: str = "individual"
    org_name: str = ""
    name: str
    email: str
    password: str


class TokenIn(BaseModel):
    token: str


class AcceptIn(BaseModel):
    token: str
    name: str = ""
    password: str


class PasswordIn(BaseModel):
    current_password: str
    new_password: str


class InviteIn(BaseModel):
    email: str
    role: str = "member"


class MemberIn(BaseModel):
    role: Optional[str] = None
    active: Optional[bool] = None


class NewOrgIn(BaseModel):
    name: str
    kind: str = "company"
    seats: Optional[int] = None
    owner_email: str


class OrgPatch(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    seats: Optional[int] = None
    active: Optional[bool] = None


class UserPatch(BaseModel):
    active: Optional[bool] = None
    platform_role: Optional[str] = None


class PasswordSet(BaseModel):
    password: str


def _start(response: Response, token: str, principal) -> dict:
    response.set_cookie(service.COOKIE, token, max_age=settings.session_hours * 3600, httponly=True, samesite="lax", secure=settings.cookie_secure, path="/")
    return service.me(principal)


@router.get("/api/me")
def me():
    return service.current_user()


# ---- sign in / out (anonymous allowed where listed in guard.ANONYMOUS_PATHS)
@router.post("/api/auth/login")
def login(body: LoginIn, request: Request, response: Response):
    token, p = service.login(body.email, body.password, body.org, request.client.host if request.client else "")
    return _start(response, token, p)


@router.post("/api/auth/signup", status_code=201)
def signup(body: SignupIn, response: Response):
    token, p = service.signup(body.kind, body.org_name, body.name, body.email, body.password)
    return _start(response, token, p)


@router.post("/api/auth/invitation")
def invitation(body: TokenIn):
    return service.invitation_info(body.token)


@router.post("/api/auth/accept-invitation")
def accept_invitation(body: AcceptIn, response: Response):
    token, p = service.accept_invitation(body.token, body.name, body.password)
    return _start(response, token, p)


@router.post("/api/auth/logout")
def logout(request: Request, response: Response):
    service.logout(request.cookies.get(service.COOKIE))
    response.delete_cookie(service.COOKIE, path="/")
    return {"ok": True}


@router.post("/api/auth/password")
def change_password(body: PasswordIn, request: Request):
    service.change_password(service.current(), body.current_password, body.new_password, request.cookies.get(service.COOKIE))
    return {"ok": True}


# ---- the owner of an organization manages its people (customer surface)
@router.get("/api/app/org")
def organization():
    return service.organization(service.current())


@router.post("/api/app/org/invitations", status_code=201)
def invite(body: InviteIn):
    return service.invite(service.current(), body.email, body.role)


@router.delete("/api/app/org/invitations/{inv_id}")
def cancel_invitation(inv_id: str):
    service.cancel_invitation(service.current(), inv_id)
    return {"ok": True}


@router.patch("/api/app/org/members/{user_id}")
def update_member(user_id: str, body: MemberIn):
    service.update_member(service.current(), user_id, body.role, body.active)
    return {"ok": True}


@router.delete("/api/app/org/members/{user_id}")
def remove_member(user_id: str):
    service.remove_member(service.current(), user_id)
    return {"ok": True}


# ---- platform staff (never reachable by customers: not under /api/app)
@router.get("/api/identity/orgs")
def staff_orgs():
    return service.staff_orgs()


@router.post("/api/identity/orgs", status_code=201)
def staff_create_org(body: NewOrgIn):
    return service.staff_create_org(body.name, body.kind, body.seats, body.owner_email)


@router.patch("/api/identity/orgs/{slug}")
def staff_update_org(slug: str, body: OrgPatch):
    return service.staff_update_org(slug, body.name, body.seats, body.active, body.kind)


@router.get("/api/identity/users")
def staff_users():
    return service.staff_users()


@router.patch("/api/identity/users/{user_id}")
def staff_update_user(user_id: str, body: UserPatch):
    service.staff_update_user(service.current(), user_id, body.active, body.platform_role)
    return {"ok": True}


@router.put("/api/identity/users/{user_id}/password")
def staff_set_password(user_id: str, body: PasswordSet):
    service.staff_set_password(user_id, body.password)
    return {"ok": True}
