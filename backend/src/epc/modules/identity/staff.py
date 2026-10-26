"""What the engineering team does on the platform: organizations, internal and customer accounts, assignments of inspectors and auditors."""

import datetime as dt
import secrets
from typing import List, Optional

from epc.core.config import settings
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound
from epc.modules.identity import repository as repo
from epc.modules.identity.models import ASSIGNED_ROLES, MASTER_EMAIL, NO_ORG_ROLES, ORG_KINDS, PLATFORM_ROLES, Principal
from epc.modules.identity.checks import _check_email, _check_username, _slug
from epc.modules.identity.invitations import INVITATION_DAYS, _invite_url
from epc.modules.identity.passwords import _check_password, hash_password, token_hash
from epc.modules.identity.registration import COMPANY_SEATS
from epc.modules.identity.sessions import audit, current


def _org_view(o: dict) -> dict:
    prof = o.get("profile") or {}
    return {"slug": o["slug"], "name": o["name"], "kind": o["kind"], "seats": o["seats"], "active": bool(o["active"]), "members": o.get("members", 0),
            "created_at": repo.as_utc(o["created_at"]).isoformat(), "validation": o.get("validation") or "validated", "country": o.get("country") or "", "tax_id": o.get("tax_id") or "",
            "contact_email": prof.get("contact_email", ""), "address": prof.get("address") or {}, "registered_by": prof.get("registered_by", ""), "validation_note": prof.get("validation_note", "")}


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


VALIDATIONS = ("pending", "validated", "rejected")


def staff_update_org(slug: str, name: Optional[str] = None, seats: Optional[int] = None, active: Optional[bool] = None, kind: Optional[str] = None,
                     validation: Optional[str] = None, note: Optional[str] = None) -> dict:
    org = repo.org_by_slug(slug)
    if not org:
        raise NotFound("organization not found")
    values: dict = {}
    if validation is not None:                                    # the team confirmed (or not) that the company is who it says it is
        if validation not in VALIDATIONS:
            raise Invalid({"validation": ", ".join(VALIDATIONS)})
        who = current()
        values["validation"] = validation
        values["profile"] = {**(org.get("profile") or {}), "validation_note": (note or "").strip()[:500], "validated_by": who.email, "validated_at": repo.now().isoformat()}
        if validation == "rejected":
            active = False                                       # a rejected registration cannot work; the people are signed out
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


def org_profile(slug: str) -> dict:
    """What the company declared when it registered (for the documents it issues): name, tax id, address, contact e-mail. Empty for the organizations that did not register."""
    o = repo.org_by_slug(slug) if slug else None
    if not o:
        return {}
    prof = o.get("profile") or {}
    return {"name": o["name"], "country": o.get("country") or "", "tax_id": o.get("tax_id") or "", "address": prof.get("address") or {}, "contact_email": prof.get("contact_email", "")}


def staff_users() -> List[dict]:
    out = []
    for u in repo.list_users():
        if u["email"] == MASTER_EMAIL:
            continue                                                  # the development MASTER is invisible to everyone else
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


def reset_accounts(include_audit: bool = False) -> dict:
    """Delete every account and organization (command line, development only). Projects on disk are not touched."""
    if settings.env == "production":
        raise Forbidden("this is never allowed in production")
    counts = repo.delete_all_accounts(include_audit)
    if not include_audit:
        repo.insert_audit(None, "command line", "accounts_reset", "", None, counts, "")
    return counts
