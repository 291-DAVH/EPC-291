"""Who is calling and what they may see (US-0018).

Two modes (`EPC_AUTH`):
* `simulated` (development default): nobody logs in; the role comes from EPC_ROLE, exactly as before. No database is touched.
* `required` (production default): every request carries a session (cookie `epc_session` or `Authorization: Bearer`). Accounts live in the database.

Accounts: a *user* belongs to one or more *organizations*. An organization is an individual subscription (one seat) or a company
subscription (a group of people, `seats`). Inside an organization a member is `owner` (manages the people) or `member`. The platform staff
(the engineering office) are users with platform role `admin`; they see every organization. A customer sees only the projects of the active
organization of the session. Code running outside a request (background jobs) is trusted and is not filtered.
"""
import base64
import contextvars
import datetime as dt
import hashlib
import hmac
import os
import re
import secrets
import threading
import time
from typing import Dict, List, Optional, Tuple

from epc.core.config import settings
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound, TooManyRequests, Unauthorized
from epc.modules.identity import repository as repo
from epc.modules.identity import oauth, permissions
from epc.modules.identity.oauth import OAuthError
from epc.modules.identity.models import ASSIGNED_ROLES, NO_ORG_ROLES, ORG_KINDS, ORG_ROLES, PLATFORM_ROLES, Principal

COOKIE = "epc_session"
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME = re.compile(r"^[a-z0-9][a-z0-9._-]{2,29}$")
RESERVED_ALIASES = {"admin", "administrator", "root", "support", "staff", "system", "soporte", "ayuda", "help", "null", "none", "me", "api"}
MIN_PASSWORD = 10
INVITATION_DAYS = 7
COMPANY_SEATS = 5

_ctx: contextvars.ContextVar = contextvars.ContextVar("epc_principal", default=None)
_fails: Dict[str, List[float]] = {}
_fails_lock = threading.Lock()
_DUMMY_HASH = None


# ---------------------------------------------------------------- passwords and tokens
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    h = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(h).decode()


def verify_password(password: str, stored: Optional[str]) -> bool:
    global _DUMMY_HASH
    if not stored:                                   # same work as a real check: no timing difference between unknown and wrong
        _DUMMY_HASH = _DUMMY_HASH or hash_password("x")
        verify_password(password, _DUMMY_HASH)
        return False
    try:
        _, n, r, p, salt, want = stored.split("$")
        got = hashlib.scrypt(password.encode("utf-8"), salt=base64.b64decode(salt), n=int(n), r=int(r), p=int(p), dklen=32)
        return hmac.compare_digest(got, base64.b64decode(want))
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _check_password(password: str, email: str = "") -> None:
    if len(password or "") < MIN_PASSWORD:
        raise Invalid({"password": f"at least {MIN_PASSWORD} characters"})
    if email and password.lower() == email.lower():
        raise Invalid({"password": "must not be the email"})


def _check_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL.match(email) or len(email) > 254:
        raise Invalid({"email": "not a valid email address"})
    return email


def _invite_url(token: str) -> str:
    return f"{settings.public_url}/?invite={token}"


def _check_username(raw: Optional[str], exclude=None) -> Optional[str]:
    """An optional alias to sign in with instead of the email: lowercase, 3 to 30 characters, never an '@' (that is how the two are told apart)."""
    u = (raw or "").strip().lower()
    if not u:
        return None
    if "@" in u or not USERNAME.match(u) or u in RESERVED_ALIASES:
        raise Invalid({"username": "3 to 30 letters, digits, dot, dash or underscore, starting with a letter or digit, no @"})
    other = repo.user_by_username(u)
    if other and str(other["id"]) != str(exclude):
        raise Conflict({"username": "this alias is already taken"})
    return u


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "org"
    slug, n = base, 1
    while repo.org_by_slug(slug):
        n += 1
        slug = f"{base}-{n}"
    return slug


# ---------------------------------------------------------------- the principal of a request
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
                acting = dict(org_id=str(org["id"]), org_slug=org["slug"], org_name=org["name"], org_kind=org["kind"], org_role="owner")
        return Principal(role=user["platform_role"], assigned=assigned, **base, **acting)
    org = repo.org_by_id(row["organization_id"]) if row["organization_id"] else None
    mem = repo.membership(org["id"], user["id"]) if org else None
    if not org or not org["active"] or not mem or not mem["active"]:
        return None
    return Principal(role="user", org_id=str(org["id"]), org_slug=org["slug"], org_name=org["name"], org_kind=org["kind"], org_role=mem["role"], **base)


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
    if p.authenticated and not p.simulated and p.user_id and p.role == "admin":              # the engineering team can enter any organization
        return [{"slug": o["slug"], "name": o["name"], "kind": o["kind"], "role": "owner", "current": o["slug"] == p.org_slug} for o in repo.list_orgs()]
    if not p.authenticated or p.simulated or not p.user_id or p.role in NO_ORG_ROLES:
        return []
    return [{"slug": o["slug"], "name": o["name"], "kind": o["kind"], "role": o["role"], "current": o["slug"] == p.org_slug}
            for o in repo.memberships_of_user(p.user_id) if o["member_active"] and o["active"]]


def me(p: Principal, with_orgs: bool = False) -> dict:
    out = {"auth": settings.auth, "authenticated": p.authenticated, "role": p.role, "account_type": account_type(p), "name": p.name, "email": p.email, "username": p.username, "has_password": p.has_password,
           "org": p.org_name, "org_slug": p.org_slug, "org_kind": p.org_kind, "org_role": p.org_role, "signup": settings.signup == "open",
           "landing": "/norms" if p.role == "standards" else "/", "app_url": settings.public_url, "console_url": settings.console_url, "abilities": permissions.abilities_of(account_type(p)),
           "assigned": list(p.assigned)}
    if with_orgs:
        out["organizations"] = _organizations(p)
    return out


def current_user() -> dict:
    return me(current())


def switch_org(p: Principal, token: Optional[str], slug: str) -> Principal:
    """A person who belongs to several organizations changes the one the session works in, without signing in again."""
    if not p.authenticated or p.simulated or not p.user_id or not token or p.role not in ("user", "admin"):
        raise Forbidden("this account does not belong to organizations")
    if p.role == "admin":                                         # staff: any organization, or none (the whole platform)
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


# ---------------------------------------------------------------- audit log
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
             "detail": r["detail"], "ip": r["ip"]} for r in repo.list_audit(min(max(limit, 1), 500), action, actor, o["id"] if o else None)]


# ---------------------------------------------------------------- sessions
def _throttle(key: str, limit: int, add: bool = False) -> None:
    now = time.time()
    with _fails_lock:
        hits = [t for t in _fails.get(key, []) if now - t < 900]
        if add:
            hits.append(now)
        _fails[key] = hits
        if len(hits) >= limit and not add:
            raise TooManyRequests({"errors": {"login": "too many attempts, try again in a few minutes"}})


def reset_throttle() -> None:
    with _fails_lock:
        _fails.clear()


def _open_session(user: dict, org: Optional[dict]) -> Tuple[str, Principal]:
    token = secrets.token_urlsafe(32)
    repo.insert_session(user["id"], org["id"] if org else None, token_hash(token), repo.now() + dt.timedelta(hours=settings.session_hours))
    repo.update_user(user["id"], last_login_at=repo.now())
    repo.purge_expired_sessions()
    p = _from_session(token)
    if p is None:
        raise Forbidden("this account has no active organization")
    return token, p


def login(identifier: str, password: str, org_slug: str = "", ip: str = "") -> Tuple[str, Principal]:
    """`identifier` is the email or the alias: the person types one box."""
    email = (identifier or "").strip().lower()
    _throttle(f"e:{email}", 5)
    _throttle(f"i:{ip}", 30)
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


# ---------------------------------------------------------------- creating accounts
def signup(kind: str, org_name: str, name: str, email: str, password: str, username: str = "") -> Tuple[str, Principal]:
    if settings.signup != "open":
        raise Forbidden("self-registration is closed: ask for an invitation")
    email = _check_email(email)
    errors = {}
    if kind not in ORG_KINDS:
        errors["kind"] = "individual or company"
    if not (name or "").strip():
        errors["name"] = "required"
    if kind == "company" and not (org_name or "").strip():
        errors["org_name"] = "required"
    if errors:
        raise Invalid(errors)
    _check_password(password, email)
    alias = _check_username(username)
    if repo.user_by_email(email):
        raise Conflict({"email": "this email is already registered"})
    label = name.strip() if kind == "individual" else org_name.strip()
    org = repo.insert_org(_slug(label), label, kind, 1 if kind == "individual" else COMPANY_SEATS)
    user = repo.insert_user(email, name.strip(), hash_password(password), username=alias)
    repo.insert_membership(org["id"], user["id"], "owner")
    token, p = _open_session(user, org)
    audit("signup", target=f"{kind}:{org['slug']}", org=str(org["id"]), actor=p)
    return token, p


def bootstrap_admin(email: str, name: str, password: str, role: str = "admin") -> dict:
    """First internal account (command line). Updates the password and role when the account already exists."""
    if role not in NO_ORG_ROLES:
        raise Invalid({"role": ", ".join(NO_ORG_ROLES)})
    email = _check_email(email)
    _check_password(password, email)
    user = repo.user_by_email(email)
    if user:
        repo.update_user(user["id"], password_hash=hash_password(password), platform_role=role, active=True)
        out = repo.user_by_id(user["id"])
    else:
        out = repo.insert_user(email, name.strip() or email, hash_password(password), platform_role=role)
    audit("account_bootstrapped", target=f"{email}:{role}", actor=Principal(), email="command line")
    return out


# ---------------------------------------------------------------- invitations
def _seats_left(org: dict) -> int:
    return org["seats"] - repo.count_members(org["id"]) - len(repo.pending_invitations(org["id"]))


def _new_invitation(org: dict, email: str, role: str, invited_by) -> dict:
    email = _check_email(email)
    if role not in ORG_ROLES:
        raise Invalid({"role": "owner, admin or member"})
    if org["kind"] == "individual":
        raise Conflict({"seats": "an individual subscription has one seat: it cannot invite people"})
    if _seats_left(org) < 1:
        raise Conflict({"seats": "no seats left: remove a person or ask for more seats"})
    user = repo.user_by_email(email)
    if user and repo.membership(org["id"], user["id"]):
        raise Conflict({"email": "this person already belongs to the organization"})
    if any(i["email"] == email for i in repo.pending_invitations(org["id"])):
        raise Conflict({"email": "this person already has a pending invitation"})
    token = secrets.token_urlsafe(32)
    inv = repo.insert_invitation(org["id"], email, role, token_hash(token), invited_by, repo.now() + dt.timedelta(days=INVITATION_DAYS))
    return {"id": str(inv["id"]), "email": email, "role": role, "expires_at": inv["expires_at"].isoformat(), "token": token, "url": _invite_url(token)}


def invite(p: Principal, email: str, role: str) -> dict:
    require_manager(p)
    if role == "owner":
        _only_owner(p, "invite another owner")
    inv = _new_invitation(repo.org_by_id(p.org_id), email, role, p.user_id)
    audit("invitation_created", target=inv["email"], org=p.org_id, detail={"role": role}, actor=p)
    return inv


def cancel_invitation(p: Principal, inv_id: str) -> None:
    require_manager(p)
    inv = repo.invitation_by_id(p.org_id, inv_id)
    if not inv:
        raise NotFound("invitation not found")
    repo.delete_invitation(inv["id"])
    audit("invitation_cancelled", target=inv["email"], org=p.org_id, actor=p)


def _open_invitation(token: str) -> dict:
    inv = repo.invitation_by_hash(token_hash(token or ""))
    if not inv or inv["accepted_at"] or repo.as_utc(inv["expires_at"]) <= repo.now():
        raise NotFound("this invitation is not valid or has expired")
    org = repo.org_by_id(inv["organization_id"])
    if not org or not org["active"]:
        raise NotFound("this invitation is not valid or has expired")
    return {**inv, "org": org}


def invitation_info(token: str) -> dict:
    inv = _open_invitation(token)
    return {"email": inv["email"], "role": inv["role"], "org": inv["org"]["name"], "kind": inv["org"]["kind"], "existing_account": repo.user_by_email(inv["email"]) is not None}


def accept_invitation(token: str, name: str, password: str, username: str = "") -> Tuple[str, Principal]:
    inv = _open_invitation(token)
    org = inv["org"]
    user = repo.user_by_email(inv["email"])
    if user:
        if not verify_password(password or "", user["password_hash"]) or not user["active"]:
            raise Unauthorized({"errors": {"login": "wrong email or password"}})
    else:
        if not (name or "").strip():
            raise Invalid({"name": "required"})
        _check_password(password, inv["email"])
    alias = _check_username(username) if not user else None
    taken = repo.count_members(org["id"])
    if taken >= org["seats"]:
        raise Conflict({"seats": "the organization has no seats left: ask its owner"})
    if not user:
        user = repo.insert_user(inv["email"], name.strip(), hash_password(password), username=alias)
    if not repo.membership(org["id"], user["id"]):
        repo.insert_membership(org["id"], user["id"], inv["role"])
    repo.accept_invitation(inv["id"])
    token, p = _open_session(user, org)
    audit("invitation_accepted", target=inv["email"], org=str(org["id"]), detail={"role": inv["role"]}, actor=p)
    return token, p


# ---------------------------------------------------------------- organization management (owner)
def _member_view(m: dict, me_id: Optional[str]) -> dict:
    return {"user_id": str(m["user_id"]), "email": m["email"], "name": m["display_name"], "role": m["role"], "active": bool(m["active"]),
            "last_login_at": repo.as_utc(m["last_login_at"]).isoformat() if m["last_login_at"] else None, "me": str(m["user_id"]) == me_id}


def organization(p: Principal) -> dict:
    require_manager(p)
    org = repo.org_by_id(p.org_id)
    pending = repo.pending_invitations(org["id"])
    return {"slug": org["slug"], "name": org["name"], "kind": org["kind"], "seats": org["seats"], "seats_used": repo.count_members(org["id"]),
            "seats_pending": len(pending), "members": [_member_view(m, p.user_id) for m in repo.members(org["id"])],
            "invitations": [{"id": str(i["id"]), "email": i["email"], "role": i["role"], "expires_at": repo.as_utc(i["expires_at"]).isoformat()} for i in pending]}


def _last_owner(org_id, user_id) -> bool:
    mem = repo.membership(org_id, user_id)
    return bool(mem and mem["role"] == "owner" and mem["active"] and repo.count_members(org_id, role="owner") <= 1)


def update_member(p: Principal, user_id: str, role: Optional[str] = None, active: Optional[bool] = None) -> None:
    require_manager(p)
    mem = repo.membership(p.org_id, user_id)
    if not mem:
        raise NotFound("person not found")
    if role is not None and role not in ORG_ROLES:
        raise Invalid({"role": "owner, admin or member"})
    if mem["role"] == "owner" or role == "owner":
        _only_owner(p, "change an owner or make someone an owner")
    if (role in ("member", "admin") or active is False) and _last_owner(p.org_id, user_id):
        raise Conflict({"role": "the organization needs at least one owner"})
    if active is True and not mem["active"] and repo.count_members(p.org_id) >= repo.org_by_id(p.org_id)["seats"]:
        raise Conflict({"seats": "no seats left"})
    values = {k: v for k, v in (("role", role), ("active", active)) if v is not None}
    if values:
        repo.update_membership(p.org_id, user_id, **values)
        audit("member_updated", target=_email_of(user_id), org=p.org_id, detail={"from": {"role": mem["role"], "active": bool(mem["active"])}, "to": values}, actor=p)
    if active is False:
        repo.delete_org_user_sessions(p.org_id, user_id)          # a role change needs nothing: the role is read on every request


def remove_member(p: Principal, user_id: str) -> None:
    require_manager(p)
    mem = repo.membership(p.org_id, user_id)
    if not mem:
        raise NotFound("person not found")
    if mem["role"] == "owner":
        _only_owner(p, "remove an owner")
    if _last_owner(p.org_id, user_id):
        raise Conflict({"role": "the organization needs at least one owner"})
    email = _email_of(user_id)
    repo.delete_org_user_sessions(p.org_id, user_id)
    repo.delete_membership(p.org_id, user_id)
    audit("member_removed", target=email, org=p.org_id, detail={"role": mem["role"]}, actor=p)


# ---------------------------------------------------------------- platform staff
def _org_view(o: dict) -> dict:
    return {"slug": o["slug"], "name": o["name"], "kind": o["kind"], "seats": o["seats"], "active": bool(o["active"]), "members": o.get("members", 0),
            "created_at": repo.as_utc(o["created_at"]).isoformat()}


def staff_orgs() -> List[dict]:
    return [_org_view(o) for o in repo.list_orgs()]


def staff_create_org(name: str, kind: str, seats: Optional[int], owner_email: str) -> dict:
    if kind not in ORG_KINDS:
        raise Invalid({"kind": "individual or company"})
    if not (name or "").strip():
        raise Invalid({"name": "required"})
    seats = 1 if kind == "individual" else int(seats or COMPANY_SEATS)
    if seats < 1:
        raise Invalid({"seats": "at least 1"})
    email = _check_email(owner_email)
    org = repo.insert_org(_slug(name.strip()), name.strip(), kind, seats)
    token = secrets.token_urlsafe(32)
    repo.insert_invitation(org["id"], email, "owner", token_hash(token), None, repo.now() + dt.timedelta(days=INVITATION_DAYS))
    audit("organization_created", target=org["slug"], org=str(org["id"]), detail={"kind": kind, "seats": seats, "owner": email})
    return {"org": _org_view({**org, "members": 0}), "invitation": {"email": email, "role": "owner", "token": token, "url": _invite_url(token)}}


def staff_update_org(slug: str, name: Optional[str] = None, seats: Optional[int] = None, active: Optional[bool] = None, kind: Optional[str] = None) -> dict:
    org = repo.org_by_slug(slug)
    if not org:
        raise NotFound("organization not found")
    values: dict = {}
    if name is not None:
        if not name.strip():
            raise Invalid({"name": "required"})
        values["name"] = name.strip()
    new_kind = kind if kind is not None else org["kind"]
    if new_kind not in ORG_KINDS:
        raise Invalid({"kind": "individual or company"})
    new_seats = 1 if new_kind == "individual" else (seats if seats is not None else org["seats"])
    if new_seats < max(1, repo.count_members(org["id"])):
        raise Conflict({"seats": "fewer seats than people in the organization"})
    if new_kind != org["kind"]:
        values["kind"] = new_kind
    if new_seats != org["seats"]:
        values["seats"] = new_seats
    if active is not None:
        values["active"] = active
    if values:
        repo.update_org(org["id"], **values)
        audit("organization_updated", target=slug, org=str(org["id"]), detail=values)
        if active is False:
            repo.delete_org_sessions(org["id"])
    return _org_view({**repo.org_by_slug(slug), "members": repo.count_members(org["id"])})


def staff_users() -> List[dict]:
    out = []
    for u in repo.list_users():
        orgs = [{"slug": o["slug"], "name": o["name"], "role": o["role"]} for o in repo.memberships_of_user(u["id"])]
        assigned = [{"slug": o["slug"], "name": o["name"]} for o in repo.assigned_orgs(u["id"])] if u["platform_role"] in ASSIGNED_ROLES else []
        out.append({"id": str(u["id"]), "email": u["email"], "username": u["username"] or "", "name": u["display_name"], "active": bool(u["active"]), "platform_role": u["platform_role"],
                    "last_login_at": repo.as_utc(u["last_login_at"]).isoformat() if u["last_login_at"] else None, "organizations": orgs, "assignments": assigned})
    return out


def staff_update_user(p: Principal, user_id: str, active: Optional[bool] = None, platform_role: Optional[str] = None) -> None:
    user = repo.user_by_id(user_id)
    if not user:
        raise NotFound("user not found")
    if platform_role is not None and platform_role not in PLATFORM_ROLES:
        raise Invalid({"platform_role": ", ".join(PLATFORM_ROLES)})
    losing_staff = user["platform_role"] == "admin" and (active is False or (platform_role is not None and platform_role != "admin"))
    if losing_staff and (str(user["id"]) == p.user_id or repo.count_staff() <= 1):
        raise Conflict({"platform_role": "you cannot remove the last staff account or your own"})
    values = {k: v for k, v in (("active", active), ("platform_role", platform_role)) if v is not None}
    if values:
        repo.update_user(user["id"], **values)
        audit("user_updated", target=user["email"], detail={"from": {"role": user["platform_role"], "active": bool(user["active"])}, "to": values}, actor=p)
    if platform_role is not None and platform_role not in ASSIGNED_ROLES:
        repo.set_assignments(user["id"], [], p.user_id)                    # leaving the inspector or auditor role ends its assignments
    if active is False or platform_role is not None:
        repo.delete_user_sessions(user["id"])


def staff_set_password(user_id: str, password: str) -> None:
    user = repo.user_by_id(user_id)
    if not user:
        raise NotFound("user not found")
    _check_password(password, user["email"])
    repo.update_user(user["id"], password_hash=hash_password(password))
    repo.delete_user_sessions(user["id"])
    audit("password_set_by_staff", target=user["email"])


def staff_create_user(email: str, name: str, password: str, platform_role: str, username: str = "") -> dict:
    """Staff create an account that belongs to no customer organization: staff, norm reviewer, inspector or external auditor."""
    if platform_role not in NO_ORG_ROLES:
        raise Invalid({"platform_role": ", ".join(NO_ORG_ROLES)})
    email = _check_email(email)
    if not (name or "").strip():
        raise Invalid({"name": "required"})
    _check_password(password, email)
    if repo.user_by_email(email):
        raise Conflict({"email": "this email is already registered"})
    u = repo.insert_user(email, name.strip(), hash_password(password), platform_role=platform_role, username=_check_username(username))
    audit("user_created", target=email, detail={"role": platform_role})
    return {"id": str(u["id"]), "email": u["email"], "name": u["display_name"], "platform_role": platform_role}


def staff_set_assignments(p: Principal, user_id: str, slugs: List[str]) -> List[dict]:
    """The organizations an inspector or an external auditor may see: exactly this list."""
    user = repo.user_by_id(user_id)
    if not user:
        raise NotFound("user not found")
    if user["platform_role"] not in ASSIGNED_ROLES:
        raise Invalid({"user": "only inspectors and external auditors have assigned organizations"})
    orgs, errors = [], {}
    for s in dict.fromkeys(slugs or []):
        o = repo.org_by_slug(s)
        if o:
            orgs.append(o)
        else:
            errors[s] = "unknown organization"
    if errors:
        raise Invalid(errors)
    before = {o["slug"]: o for o in repo.assigned_orgs(user["id"])}
    repo.set_assignments(user["id"], [o["id"] for o in orgs], p.user_id)
    now = {o["slug"]: o for o in orgs}
    for s in sorted(set(now) - set(before)):
        audit("assignment_granted", target=user["email"], org=str(now[s]["id"]), detail={"org": s}, actor=p)
    for s in sorted(set(before) - set(now)):
        audit("assignment_revoked", target=user["email"], org=str(before[s]["id"]), detail={"org": s}, actor=p)
    return [{"slug": o["slug"], "name": o["name"]} for o in orgs]


# ---------------------------------------------------------------- sign-in and sign-up with an external provider
# Rules that keep it safe:
#  * only customer accounts can use a provider: the engineering team, norm reviewers, inspectors and auditors always use their password;
#  * an existing account is linked to a provider automatically only when the provider vouches for the email (Google, GitHub verified email, LinkedIn); otherwise the person
#    must sign in with their password first and link the provider from their account page (Facebook never vouches for an address);
#  * a new account needs the subscription type (asked after the provider answers) and only exists when sign-up is open or through an invitation addressed to that email;
#  * an account created through a provider has no password until its owner sets one, and its last way to sign in cannot be removed.
def oauth_providers() -> List[dict]:
    return oauth.enabled()


def oauth_start(provider: str, mode: str, invite: str, actor: Principal) -> Tuple[str, str]:
    oauth.require(provider)
    extra: dict = {"m": "login"}
    if mode == "link":
        if not actor.authenticated or actor.simulated or not actor.user_id or actor.role != "user":
            raise Unauthorized({"errors": {"login": "sign in to link a provider"}})
        extra = {"m": "link", "u": actor.user_id}
    elif invite:
        try:
            _open_invitation(invite)
        except NotFound:
            raise OAuthError("invalid_invitation")
        extra = {"m": "login", "inv": invite}
    return oauth.start(provider, extra)


def _customer_session(user: dict, provider: str, ip: str) -> Tuple[str, Principal]:
    if user["platform_role"] != "user":
        raise OAuthError("internal_account_password_only")
    if not user["active"]:
        raise OAuthError("account_disabled")
    orgs = [o for o in repo.memberships_of_user(user["id"]) if o["member_active"] and o["active"]]
    if not orgs:
        raise OAuthError("no_organization")
    token, p = _open_session(user, orgs[0])
    audit("social_login", target=provider, actor=p, ip=ip)
    return token, p


def _display_name(profile: dict) -> str:
    return (profile.get("name") or "").strip() or profile["email"].split("@")[0]


def oauth_callback(provider: str, code: str, state: str, cookie: Optional[str], ip: str = "") -> dict:
    """Result: {"token": session token} (signed in), {"pending": cookie} (authenticated at the provider, no account yet) or {"to": path} (linked)."""
    flow = oauth.unsign(cookie or "")
    if not flow or flow.get("p") != provider or not state or not hmac.compare_digest(str(flow.get("s", "")), state):
        raise OAuthError("invalid_state")
    if not code:
        raise OAuthError("cancelled")
    prof = oauth.profile(provider, code, flow.get("v", ""))
    if not prof["subject"]:
        raise OAuthError("provider_error")
    ident = repo.identity_find(provider, prof["subject"])

    if flow.get("m") == "link":
        user = repo.user_by_id(flow.get("u"))
        if not user or user["platform_role"] != "user":
            raise OAuthError("invalid_state")
        if ident and str(ident["user_id"]) != str(user["id"]):
            raise OAuthError("identity_in_use")
        if not ident:
            repo.insert_identity(user["id"], provider, prof["subject"], prof["email"])
            audit("identity_linked", target=provider, actor=Principal(authenticated=True, user_id=str(user["id"]), email=user["email"]))
        return {"to": f"/account?linked={provider}"}

    if flow.get("inv"):
        return _social_invitation(provider, prof, ident, flow["inv"], ip)

    if ident:
        token, _ = _customer_session(repo.user_by_id(ident["user_id"]), provider, ip)
        return {"token": token}
    if not prof["email"]:
        raise OAuthError("no_email")
    existing = repo.user_by_email(prof["email"])
    if existing:
        if existing["platform_role"] != "user":
            raise OAuthError("internal_account_password_only")
        if not prof["email_verified"]:
            raise OAuthError("email_exists_login_first")
        repo.insert_identity(existing["id"], provider, prof["subject"], prof["email"])
        audit("identity_linked", target=f"{provider} (same verified email)", actor=Principal(authenticated=True, user_id=str(existing["id"]), email=existing["email"]))
        token, _ = _customer_session(existing, provider, ip)
        return {"token": token}
    if settings.signup != "open":
        raise OAuthError("signup_closed")
    return {"pending": oauth.sign({"p": provider, "sub": prof["subject"], "email": prof["email"], "name": _display_name(prof)}, ttl=900)}


def _social_invitation(provider: str, prof: dict, ident: Optional[dict], token: str, ip: str) -> dict:
    try:
        inv = _open_invitation(token)
    except NotFound:
        raise OAuthError("invalid_invitation")
    if not prof["email"] or not prof["email_verified"] or prof["email"] != inv["email"]:
        raise OAuthError("invitation_email_mismatch")
    org = inv["org"]
    user = repo.user_by_email(inv["email"])
    if ident and (not user or str(ident["user_id"]) != str(user["id"])):
        raise OAuthError("identity_in_use")
    if user and user["platform_role"] != "user":
        raise OAuthError("internal_account_password_only")
    if repo.count_members(org["id"]) >= org["seats"] and not (user and repo.membership(org["id"], user["id"])):
        raise OAuthError("no_seats")
    if not user:
        user = repo.insert_user(inv["email"], _display_name(prof), None)
    if not repo.identity_find(provider, prof["subject"]):
        repo.insert_identity(user["id"], provider, prof["subject"], prof["email"])
    if not repo.membership(org["id"], user["id"]):
        repo.insert_membership(org["id"], user["id"], inv["role"])
    repo.accept_invitation(inv["id"])
    session, p = _open_session(user, org)
    audit("invitation_accepted", target=inv["email"], org=str(org["id"]), detail={"role": inv["role"], "via": provider}, actor=p, ip=ip)
    return {"token": session}


def oauth_pending(cookie: Optional[str]) -> dict:
    d = oauth.unsign(cookie or "")
    if not d or "sub" not in d:
        raise NotFound("there is no sign-up in progress")
    return {"provider": d["p"], "email": d["email"], "name": d["name"]}


def oauth_complete(cookie: Optional[str], kind: str, org_name: str, username: str, ip: str = "") -> Tuple[str, Principal]:
    """The person authenticated at the provider chooses the type of subscription and the account is created (no password: the provider vouches for them)."""
    d = oauth.unsign(cookie or "")
    if not d or "sub" not in d:
        raise Invalid({"social": "the sign-up expired: start again"})
    if settings.signup != "open":
        raise Forbidden("self-registration is closed: ask for an invitation")
    errors = {}
    if kind not in ORG_KINDS:
        errors["kind"] = "individual or company"
    if kind == "company" and not (org_name or "").strip():
        errors["org_name"] = "required"
    if errors:
        raise Invalid(errors)
    alias = _check_username(username)
    if repo.user_by_email(d["email"]) or repo.identity_find(d["p"], d["sub"]):
        raise Conflict({"email": "this email is already registered"})
    label = d["name"] if kind == "individual" else org_name.strip()
    org = repo.insert_org(_slug(label), label, kind, 1 if kind == "individual" else COMPANY_SEATS)
    user = repo.insert_user(d["email"], d["name"], None, username=alias)
    repo.insert_membership(org["id"], user["id"], "owner")
    repo.insert_identity(user["id"], d["p"], d["sub"], d["email"])
    token, p = _open_session(user, org)
    audit("social_signup", target=f"{d['p']}:{kind}:{org['slug']}", org=str(org["id"]), actor=p, ip=ip)
    return token, p


def identities_of(p: Principal) -> dict:
    if not p.authenticated or p.simulated or not p.user_id:
        return {"has_password": False, "identities": []}
    return {"has_password": p.has_password, "identities": [{"provider": i["provider"], "email": i["email"], "created_at": repo.as_utc(i["created_at"]).isoformat()} for i in repo.identities_of(p.user_id)]}


def unlink_identity(p: Principal, provider: str) -> None:
    if not p.authenticated or p.simulated or not p.user_id:
        raise Forbidden("not available without an account")
    mine = repo.identities_of(p.user_id)
    if not any(i["provider"] == provider for i in mine):
        raise NotFound("this provider is not linked")
    if not p.has_password and len(mine) <= 1:
        raise Conflict({"identity": "it is your only way to sign in: set a password first"})
    repo.delete_identity(p.user_id, provider)
    audit("identity_unlinked", target=provider, actor=p)

