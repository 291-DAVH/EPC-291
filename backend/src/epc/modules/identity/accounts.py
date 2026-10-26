"""Creating accounts and the people of an organization: self-registration, the first internal account, members and their roles."""

from typing import Optional, Tuple

from epc.core.config import settings
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound
from epc.modules.identity import repository as repo
from epc.modules.identity.models import NO_ORG_ROLES, ORG_KINDS, ORG_ROLES, Principal
from epc.modules.identity.checks import _check_email, _check_username, _slug
from epc.modules.identity.passwords import _check_password, hash_password
from epc.modules.identity.registration import COMPANY_SEATS
from epc.modules.identity.sessions import _email_of, _only_owner, _open_session, audit, org_name, require_manager


def signup(kind: str, org_name: str, name: str, email: str, password: str, username: str = "") -> Tuple[str, Principal]:
    if settings.signup != "open":
        raise Forbidden("self-registration is closed: ask for an invitation")
    if kind == "company":
        raise Invalid({"kind": "a company registers with the company form: country, tax identifier, address and the code sent to its e-mail"})
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
