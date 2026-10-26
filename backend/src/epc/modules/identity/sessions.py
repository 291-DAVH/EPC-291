"""Who is making the request: the principal of the current request, the session behind a cookie or token, sign-in, view-as, audit trail and the account's own settings."""

import contextvars
import datetime as dt
import hmac
import secrets
from typing import List, Optional, Tuple

from epc.core.config import settings
from epc.core.errors import Forbidden, Invalid, NotFound, Unauthorized
from epc.modules.identity import permissions
from epc.modules.identity import repository as repo
from epc.modules.identity.models import ASSIGNED_ROLES, MASTER_EMAIL, NO_ORG_ROLES, Principal
from epc.modules.identity.checks import _check_username
from epc.modules.identity.passwords import _check_password, hash_password, token_hash, verify_password
from epc.modules.identity.throttle import _throttle


COOKIE = "epc_session"


_ctx: contextvars.ContextVar = contextvars.ContextVar("epc_principal", default=None)


def simulated_principal() -> Principal:
    return Principal(authenticated=True, role=settings.role if settings.role in ("admin", "standards", "inspector", "auditor") else "user", name=settings.user, org_name=settings.org, simulated=True)


def activate(p: Optional[Principal]):
    return _ctx.set(p)


def deactivate(handle) -> None:
    _ctx.reset(handle)


def current() -> Principal:
    p = _ctx.get()
    return p if p is not None else simulated_principal()


def is_admin() -> bool:
    return current().role == "admin"


def visible_orgs() -> Optional[frozenset]:
    """Slugs of the organizations whose projects the caller may see; None = no restriction (staff, simulated mode, trusted code).
    A customer sees their active organization, an inspector or auditor the organizations assigned to them, the norm reviewer none."""
    if settings.auth != "required":
        return None
    p = _ctx.get()
    if p is None or p.role == "admin":
        return None
    if p.role in ASSIGNED_ROLES:
        return frozenset(p.assigned)
    if not p.authenticated or p.role != "user" or not p.org_slug:
        return frozenset()
    return frozenset([p.org_slug])


def org_for_new_project(requested: str = "") -> str:
    """Organization that owns a project being created: the caller's own, or (staff only) the one they name."""
    if settings.auth != "required":
        return ""
    p = current()
    if p.role == "admin":
        if requested and not repo.org_by_slug(requested):
            raise Invalid({"org": "unknown organization"})
        return requested or p.org_slug                              # a project created while working inside an organization belongs to it
    return p.org_slug


def active_org_slug() -> str:
    """Slug of the organization the caller works in ("" for the platform team outside any organization, and in simulated mode)."""
    return current().org_slug or ""


def org_name(slug: str) -> str:
    o = repo.org_by_slug(slug) if slug else None
    return o["name"] if o else ""


def org_exists(slug: str) -> bool:
    return repo.org_by_slug(slug) is not None


def _from_session(token: str) -> Optional[Principal]:
    row = repo.session_by_hash(token_hash(token))
    if not row:
        return None
    if repo.as_utc(row["expires_at"]) <= repo.now():
        repo.delete_session(token_hash(token))
        return None
    user = repo.user_by_id(row["user_id"])
    if not user or not user["active"]:
        return None
    base = dict(authenticated=True, name=user["display_name"], email=user["email"], user_id=str(user["id"]), username=user["username"] or "", has_password=bool(user["password_hash"]))
    if user["platform_role"] in NO_ORG_ROLES:
        assigned = tuple(o["slug"] for o in repo.assigned_orgs(user["id"]) if o["active"]) if user["platform_role"] in ASSIGNED_ROLES else ()
        acting = {}
        if user["platform_role"] == "admin" and row["organization_id"]:                # staff working inside an organization: they act as its owner
            org = repo.org_by_id(row["organization_id"])
            if org:
                acting = dict(org_id=str(org["id"]), org_slug=org["slug"], org_name=org["name"], org_kind=org["kind"], org_role="owner", org_validation=org.get("validation") or "validated")
                if row.get("view_as") in VIEW_AS_ROLES:                                  # looking at the platform as that organization sees it: the same rights and the same data, nothing more
                    return Principal(role="user", org_id=str(org["id"]), org_slug=org["slug"], org_name=org["name"], org_kind=org["kind"], org_role=row["view_as"], org_validation=org.get("validation") or "validated",
                                     can_view_as=True, viewing_as=row["view_as"], **base)
        return Principal(role=user["platform_role"], assigned=assigned, can_view_as=user["platform_role"] == "admin", **base, **acting)
    org = repo.org_by_id(row["organization_id"]) if row["organization_id"] else None
    mem = repo.membership(org["id"], user["id"]) if org else None
    if not org or not org["active"] or not mem or not mem["active"]:
        return None
    return Principal(role="user", org_id=str(org["id"]), org_slug=org["slug"], org_name=org["name"], org_kind=org["kind"], org_role=mem["role"], org_validation=org.get("validation") or "validated", **base)


def token_from(cookie: Optional[str], authorization: Optional[str]) -> Optional[str]:
    if cookie:
        return cookie
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def principal_for_request(cookie: Optional[str], authorization: Optional[str]) -> Principal:
    if settings.auth != "required":
        return simulated_principal()
    token = token_from(cookie, authorization)
    return (_from_session(token) if token else None) or Principal()


def account_type(p: Principal) -> str:
    """What kind of account this is, worked out from the account itself (the person only types email and password):
    staff | reviewer | inspector | auditor | individual | corporate_owner | corporate_admin | corporate_member (see permissions.py)."""
    if not p.authenticated:
        return ""
    if p.role == "admin":
        return "staff"
    if p.role == "standards":
        return "reviewer"
    if p.role in ASSIGNED_ROLES:
        return p.role
    if p.org_kind == "company":
        return {"owner": "corporate_owner", "admin": "corporate_admin"}.get(p.org_role, "corporate_member")
    return "individual"


def _organizations(p: Principal) -> List[dict]:
    if p.authenticated and not p.simulated and p.user_id and (p.role == "admin" or p.can_view_as):              # the engineering team can enter any organization
        return [{"slug": o["slug"], "name": o["name"], "kind": o["kind"], "role": "owner", "current": o["slug"] == p.org_slug} for o in repo.list_orgs()]
    if not p.authenticated or p.simulated or not p.user_id or p.role in NO_ORG_ROLES:
        return []
    return [{"slug": o["slug"], "name": o["name"], "kind": o["kind"], "role": o["role"], "current": o["slug"] == p.org_slug}
            for o in repo.memberships_of_user(p.user_id) if o["member_active"] and o["active"]]


def me(p: Principal, with_orgs: bool = False) -> dict:
    out = {"auth": settings.auth, "authenticated": p.authenticated, "role": p.role, "account_type": account_type(p), "name": p.name, "email": p.email, "username": p.username, "has_password": p.has_password,
           "org": p.org_name, "org_validation": p.org_validation, "org_slug": p.org_slug, "org_kind": p.org_kind, "org_role": p.org_role, "signup": settings.signup == "open",
           "landing": "/norms" if p.role == "standards" else "/", "app_url": settings.public_url, "console_url": settings.console_url, "abilities": permissions.abilities_of(account_type(p)),
           "assigned": list(p.assigned), "can_view_as": p.can_view_as, "viewing_as": p.viewing_as}
    if with_orgs:
        out["organizations"] = _organizations(p)
    return out


def current_user() -> dict:
    return me(current())


VIEW_AS_ROLES = ("owner", "admin", "member")


def view_as(p: Principal, token: Optional[str], slug: str, role: str) -> Principal:
    """The engineering team looks at the platform as an organization sees it: as its owner, its administrator, one of its members, or, for an organization of one person,
    as that independent professional. The server then applies exactly what that account may do and see. `role` empty goes back to the team's own view."""
    row = repo.session_by_hash(token_hash(token)) if token else None
    user = repo.user_by_id(row["user_id"]) if row else None
    if not user or user["platform_role"] != "admin" or not p.authenticated or p.simulated:                 # decided on the stored account, not on how the session looks now
        raise Forbidden("only the engineering team can look at the platform as another account")
    if not role:
        repo.update_session_view(token_hash(token), row["organization_id"], None)
        audit("view_as_ended", target=slug or "", actor=p)
        return _from_session(token) or p
    org = repo.org_by_slug(slug or "")
    if not org or not org["active"]:
        raise NotFound("organization not found")
    if role not in VIEW_AS_ROLES or (org["kind"] == "individual" and role != "owner"):
        raise Invalid({"role": "owner, admin or member (an independent professional is its own owner)"})
    repo.update_session_view(token_hash(token), org["id"], role)
    audit("view_as_started", target=f"{slug}:{role}", org=str(org["id"]), actor=p)
    return _from_session(token) or p


def switch_org(p: Principal, token: Optional[str], slug: str) -> Principal:
    """A person who belongs to several organizations changes the one the session works in, without signing in again."""
    if not p.authenticated or p.simulated or not p.user_id or not token or p.role not in ("user", "admin"):
        raise Forbidden("this account does not belong to organizations")
    if p.role == "admin" or p.can_view_as:                                         # staff: any organization, or none (the whole platform)
        org = repo.org_by_slug(slug) if slug else None
        if slug and not org:
            raise NotFound("organization not found")
        repo.update_session_org(token_hash(token), org["id"] if org else None)
        audit("organization_entered" if org else "organization_left", target=slug or "", org=str(org["id"]) if org else None, actor=p)
        return _from_session(token) or p
    org = repo.org_by_slug(slug or "")
    mem = repo.membership(org["id"], p.user_id) if org else None
    if not org or not org["active"] or not mem or not mem["active"]:
        raise NotFound("organization not found")
    repo.update_session_org(token_hash(token), org["id"])
    audit("organization_switched", target=slug, org=str(org["id"]), actor=p)
    return _from_session(token) or p


def require_manager(p: Principal) -> Principal:
    """The owner or an administrator of the organization."""
    allowed = p.role == "admin" or (p.role == "user" and p.org_role in ("owner", "admin"))          # staff inside an organization act as its owner
    if not p.authenticated or p.simulated or not allowed or not p.org_id:
        raise Forbidden("only the owner or an administrator of the organization can do this")
    return p


def _only_owner(p: Principal, what: str) -> None:
    if p.org_role != "owner":
        raise Forbidden(f"only an owner can {what}")


def audit(action: str, target: str = "", org=None, detail: Optional[dict] = None, actor: Optional[Principal] = None, email: str = "", ip: str = "") -> None:
    """Record who did what to what and when. Never pass passwords or tokens."""
    a = actor if actor is not None else current()
    repo.insert_audit(a.user_id, a.email or email, action, target, org if org is not None else (a.org_id or None), detail or {}, ip)


def can(subject: str, action: str) -> bool:
    """Whether the account making the current request has this ability (the matrix of permissions.py)."""
    return permissions.can(account_type(current()), subject, action)


def audit_event(action: str, target: str = "", org_slug: str = "", detail: Optional[dict] = None) -> None:
    """For other modules: record an event of the current account, optionally tied to an organization (by slug)."""
    o = repo.org_by_slug(org_slug) if org_slug else None
    audit(action, target=target, org=str(o["id"]) if o else None, detail=detail)


def _email_of(user_id) -> str:
    u = repo.user_by_id(user_id)
    return u["email"] if u else str(user_id)


def audit_log(limit: int = 100, action: Optional[str] = None, actor: Optional[str] = None, org: Optional[str] = None) -> List[dict]:
    o = repo.org_by_slug(org) if org else None
    names = {str(x["id"]): x["slug"] for x in repo.list_orgs()}
    return [{"at": repo.as_utc(r["at"]).isoformat(), "actor": r["actor_email"], "action": r["action"], "target": r["target"], "org": names.get(str(r["organization_id"]), ""),
             "detail": r["detail"], "ip": r["ip"]} for r in repo.list_audit(min(max(limit, 1), 500), action, actor, o["id"] if o else None) if r["actor_email"] != MASTER_EMAIL]


def _open_session(user: dict, org: Optional[dict]) -> Tuple[str, Principal]:
    token = secrets.token_urlsafe(32)
    repo.insert_session(user["id"], org["id"] if org else None, token_hash(token), repo.now() + dt.timedelta(hours=settings.session_hours))
    repo.update_user(user["id"], last_login_at=repo.now())
    repo.purge_expired_sessions()
    p = _from_session(token)
    if p is None:
        raise Forbidden("this account has no active organization")
    return token, p


LOOPBACK = {"127.0.0.1", "::1", "localhost", "testclient"}


def master_enabled() -> bool:
    """The MASTER account exists only when the environment is explicitly `dev`, accounts are required and its password is set in the environment. The repository
    carries no password and no default: in production, staging or any deployment where the variable is not set, it is inert."""
    return settings.env == "dev" and settings.auth == "required" and bool(settings.dev_master_password)


def _master_user(identifier: str, password: str, ip: str) -> Optional[dict]:
    """A development shortcut for the maintainer: one fixed account of the engineering team, reachable only from this machine, with the password of the environment.
    It has no password of its own in the database, is hidden from every list and from the staff counts, and cannot be registered or reached in production."""
    if not master_enabled() or ip not in LOOPBACK or identifier not in (settings.dev_master_user, MASTER_EMAIL):
        return None
    if not hmac.compare_digest(password.encode("utf-8"), settings.dev_master_password.encode("utf-8")):
        return None
    user = repo.user_by_email(MASTER_EMAIL) or repo.insert_user(MASTER_EMAIL, "MASTER (desarrollo)", None, platform_role="admin")
    if not user["active"] or user["platform_role"] != "admin":
        repo.update_user(user["id"], active=True, platform_role="admin")
        user = repo.user_by_id(user["id"])
    return user


def login(identifier: str, password: str, org_slug: str = "", ip: str = "") -> Tuple[str, Principal]:
    """`identifier` is the email or the alias: the person types one box."""
    email = (identifier or "").strip().lower()
    _throttle(f"e:{email}", 5)
    _throttle(f"i:{ip}", 30)
    master = _master_user(email, password or "", ip)
    if master:
        token, p = _open_session(master, None)
        audit("login", target="master", actor=p, ip=ip)
        return token, p
    user = repo.user_by_login(email)
    ok = verify_password(password or "", user["password_hash"] if user else None)
    if not user or not ok or not user["active"]:
        _throttle(f"e:{email}", 5, add=True)
        _throttle(f"i:{ip}", 30, add=True)
        audit("login_failed", target=email, actor=Principal(), email=email, ip=ip)
        raise Unauthorized({"errors": {"login": "wrong email or password"}})
    org = None
    if user["platform_role"] not in NO_ORG_ROLES:
        orgs = [o for o in repo.memberships_of_user(user["id"]) if o["member_active"] and o["active"] and (not org_slug or o["slug"] == org_slug)]
        if not orgs:
            raise Forbidden("this account has no active organization")
        org = orgs[0]
    token, p = _open_session(user, org)
    audit("login", target=account_type(p), actor=p, ip=ip)
    return token, p


def logout(token: Optional[str], actor: Optional[Principal] = None) -> None:
    if token:
        if actor is not None and actor.user_id:
            audit("logout", actor=actor)
        repo.delete_session(token_hash(token))


def change_password(p: Principal, current_password: str, new_password: str, keep_token: Optional[str]) -> None:
    if not p.authenticated or p.simulated or not p.user_id:
        raise Forbidden("not available without an account")
    user = repo.user_by_id(p.user_id)
    if not user or (user["password_hash"] and not verify_password(current_password or "", user["password_hash"])):
        raise Invalid({"current_password": "wrong password"})                              # an account created through a provider has none yet: it just sets one
    _check_password(new_password, user["email"])
    repo.update_user(user["id"], password_hash=hash_password(new_password))
    repo.delete_user_sessions(user["id"], keep_hash=token_hash(keep_token) if keep_token else None)       # other devices must log in again
    audit("password_changed", target=user["email"], actor=p)


def set_username(p: Principal, username: str) -> Principal:
    """The person chooses (or clears) the alias they can sign in with."""
    if not p.authenticated or p.simulated or not p.user_id:
        raise Forbidden("not available without an account")
    alias = _check_username(username, exclude=p.user_id)
    repo.update_user(p.user_id, username=alias)
    audit("username_changed", target=alias or "", actor=p)
    return replace_principal(p, username=alias or "")


def replace_principal(p: Principal, **changes) -> Principal:
    import dataclasses
    return dataclasses.replace(p, **changes)
