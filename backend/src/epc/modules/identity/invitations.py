"""Invitations to join an organization."""

import datetime as dt
import secrets
from typing import Tuple

from epc.core.config import settings
from epc.core.errors import Conflict, Invalid, NotFound, Unauthorized
from epc.modules.identity import repository as repo
from epc.modules.identity.models import ORG_ROLES, Principal
from epc.modules.identity.checks import _check_email, _check_username
from epc.modules.identity.passwords import _check_password, hash_password, token_hash, verify_password
from epc.modules.identity.sessions import _only_owner, _open_session, audit, require_manager


INVITATION_DAYS = 7


def _invite_url(token: str) -> str:
    return f"{settings.public_url}/?invite={token}"


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
