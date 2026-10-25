from typing import Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from epc.core.config import settings
from epc.modules.identity import oauth, service

router = APIRouter()


class LoginIn(BaseModel):
    login: Optional[str] = None          # email or alias
    email: Optional[str] = None          # older clients send the email here
    password: str
    org: str = ""


class SignupIn(BaseModel):
    kind: str = "individual"
    org_name: str = ""
    name: str
    email: str
    password: str
    username: str = ""


class CompanyRegisterIn(BaseModel):
    country: str = ""
    org_name: str = ""
    tax_id: str = ""
    street: str = ""
    number: str = ""
    locality: str = ""
    region: str = ""
    postal_code: str = ""
    contact_email: str = ""
    name: str = ""
    username: str = ""
    password: str = ""
    accept_terms: bool = False
    terms_version: str = ""
    lang: str = "es"


class CompanyVerifyIn(BaseModel):
    registration: str
    code: str


class RegistrationIn(BaseModel):
    registration: str


class CompleteIn(BaseModel):
    kind: str = "individual"
    org_name: str = ""
    username: str = ""


class TokenIn(BaseModel):
    token: str


class AcceptIn(BaseModel):
    token: str
    name: str = ""
    password: str
    username: str = ""


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
    validation: Optional[str] = None          # pending | validated | rejected: the team's decision on a company's registration
    validation_note: Optional[str] = None


class UserPatch(BaseModel):
    active: Optional[bool] = None
    platform_role: Optional[str] = None


class NewUserIn(BaseModel):
    email: str
    name: str
    password: str
    username: str = ""
    platform_role: str = "standards"                      # standards | inspector | auditor | admin


class AssignmentsIn(BaseModel):
    orgs: list = []


class PasswordSet(BaseModel):
    password: str


def _start(response: Response, token: str, principal) -> dict:
    response.set_cookie(service.COOKIE, token, max_age=settings.session_hours * 3600, httponly=True, samesite="lax", secure=settings.cookie_secure, path="/")
    return service.me(principal, with_orgs=True)


@router.get("/api/me")
def me():
    return service.me(service.current(), with_orgs=True)


# ---- sign in / out (anonymous allowed where listed in guard.ANONYMOUS_PATHS)
@router.post("/api/auth/login")
def login(body: LoginIn, request: Request, response: Response):
    token, p = service.login(body.login or body.email or "", body.password, body.org, request.client.host if request.client else "")
    return _start(response, token, p)


@router.post("/api/auth/signup", status_code=201)
def signup(body: SignupIn, response: Response):
    token, p = service.signup(body.kind, body.org_name, body.name, body.email, body.password, body.username)
    return _start(response, token, p)


@router.get("/api/auth/countries")
def countries():
    from epc.modules.identity import countries as C
    return C.catalog()


@router.get("/api/auth/terms")
def terms(lang: str = "es"):
    return service.terms(lang)


@router.post("/api/auth/company/register", status_code=201)
def company_register(body: CompanyRegisterIn, request: Request):
    return service.company_register(body.model_dump(), request.client.host if request.client else "")


@router.post("/api/auth/company/verify", status_code=201)
def company_verify(body: CompanyVerifyIn, request: Request, response: Response):
    token, p = service.company_verify(body.registration, body.code, request.client.host if request.client else "")
    return _start(response, token, p)


@router.post("/api/auth/company/resend")
def company_resend(body: RegistrationIn):
    return service.company_resend(body.registration)


@router.post("/api/auth/invitation")
def invitation(body: TokenIn):
    return service.invitation_info(body.token)


@router.post("/api/auth/accept-invitation")
def accept_invitation(body: AcceptIn, response: Response):
    token, p = service.accept_invitation(body.token, body.name, body.password, body.username)
    return _start(response, token, p)


# ---- sign-in and sign-up with an external provider (Google, GitHub, Facebook, LinkedIn)
def _cookie(response: Response, name: str, value: str, max_age: int) -> None:
    response.set_cookie(name, value, max_age=max_age, httponly=True, samesite="lax", secure=settings.cookie_secure, path=oauth.PATH)       # Lax: the provider sends the person back with a GET


@router.get("/api/auth/providers")
def providers():
    return service.oauth_providers()


@router.get("/api/auth/oauth/pending")
def oauth_pending(request: Request):
    return service.oauth_pending(request.cookies.get(oauth.PENDING_COOKIE))


@router.post("/api/auth/oauth/complete", status_code=201)
def oauth_complete(body: CompleteIn, request: Request, response: Response):
    token, p = service.oauth_complete(request.cookies.get(oauth.PENDING_COOKIE), body.kind, body.org_name, body.username, request.client.host if request.client else "")
    response.delete_cookie(oauth.PENDING_COOKIE, path=oauth.PATH)
    return _start(response, token, p)


@router.get("/api/auth/oauth/{provider}/start")
def oauth_start(provider: str, mode: str = "login", invite: str = ""):
    try:
        url, flow = service.oauth_start(provider, mode, invite, service.current())
    except service.OAuthError as e:
        return RedirectResponse(f"/?auth_error={e.code}", status_code=302)
    r = RedirectResponse(url, status_code=302)
    _cookie(r, oauth.COOKIE, flow, 600)
    return r


@router.get("/api/auth/oauth/{provider}/callback")
def oauth_callback(provider: str, request: Request, code: str = "", state: str = "", error: str = ""):
    try:
        res = service.oauth_callback(provider, "" if error else code, state, request.cookies.get(oauth.COOKIE), request.client.host if request.client else "")
    except service.OAuthError as e:
        r = RedirectResponse(f"/?auth_error={e.code}", status_code=302)
    else:
        if res.get("token"):
            r = RedirectResponse("/", status_code=302)
            r.set_cookie(service.COOKIE, res["token"], max_age=settings.session_hours * 3600, httponly=True, samesite="lax", secure=settings.cookie_secure, path="/")
        elif res.get("pending"):
            r = RedirectResponse("/?social=pending", status_code=302)
            _cookie(r, oauth.PENDING_COOKIE, res["pending"], 900)
        else:
            r = RedirectResponse(res["to"], status_code=302)
    r.delete_cookie(oauth.COOKIE, path=oauth.PATH)
    return r


@router.get("/api/auth/identities")
def identities():
    return service.identities_of(service.current())


@router.delete("/api/auth/identities/{provider}")
def unlink_identity(provider: str):
    service.unlink_identity(service.current(), provider)
    return {"ok": True}


@router.post("/api/auth/logout")
def logout(request: Request, response: Response):
    service.logout(request.cookies.get(service.COOKIE), service.current())
    response.delete_cookie(service.COOKIE, path="/")
    return {"ok": True}


class OrgIn(BaseModel):
    org: str


class ViewAsIn(BaseModel):
    org: str = ""
    role: str = ""          # owner | admin | member; empty = back to the team's own view


@router.post("/api/auth/view-as")
def view_as(body: ViewAsIn, request: Request):
    token = service.token_from(request.cookies.get(service.COOKIE), request.headers.get("authorization"))
    return service.me(service.view_as(service.current(), token, body.org, body.role), with_orgs=True)


@router.post("/api/auth/switch-org")
def switch_org(body: OrgIn, request: Request):
    token = service.token_from(request.cookies.get(service.COOKIE), request.headers.get("authorization"))
    return service.me(service.switch_org(service.current(), token, body.org), with_orgs=True)


class UsernameIn(BaseModel):
    username: str = ""


@router.put("/api/auth/username")
def set_username(body: UsernameIn):
    return service.me(service.set_username(service.current(), body.username), with_orgs=True)


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
    return service.staff_update_org(slug, body.name, body.seats, body.active, body.kind, body.validation, body.validation_note)


@router.get("/api/identity/users")
def staff_users():
    return service.staff_users()


@router.post("/api/identity/users", status_code=201)
def staff_create_user(body: NewUserIn):
    return service.staff_create_user(body.email, body.name, body.password, body.platform_role, body.username)


@router.patch("/api/identity/users/{user_id}")
def staff_update_user(user_id: str, body: UserPatch):
    service.staff_update_user(service.current(), user_id, body.active, body.platform_role)
    return {"ok": True}


@router.put("/api/identity/users/{user_id}/assignments")
def staff_set_assignments(user_id: str, body: AssignmentsIn):
    """Organizations an inspector or external auditor may see (exactly this list)."""
    return service.staff_set_assignments(service.current(), user_id, [str(x) for x in body.orgs])


@router.get("/api/identity/audit")
def staff_audit(limit: int = 100, action: Optional[str] = None, actor: Optional[str] = None, org: Optional[str] = None):
    """Who did what, to what and when (sign-ins, failed sign-ins, accounts, roles, invitations, assignments)."""
    return service.audit_log(limit, action, actor, org)


@router.put("/api/identity/users/{user_id}/password")
def staff_set_password(user_id: str, body: PasswordSet):
    service.staff_set_password(user_id, body.password)
    return {"ok": True}
