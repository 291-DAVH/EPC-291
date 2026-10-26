"""Sign-in with an external provider: start, callback, completing the account and linked identities."""

import hmac
from typing import List, Optional, Tuple

from epc.core.config import settings
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound, Unauthorized
from epc.modules.identity import oauth
from epc.modules.identity import repository as repo
from epc.modules.identity.models import ORG_KINDS, Principal
from epc.modules.identity.oauth import OAuthError
from epc.modules.identity.checks import _check_username, _slug
from epc.modules.identity.invitations import _open_invitation, invite
from epc.modules.identity.registration import COMPANY_SEATS
from epc.modules.identity.sessions import _open_session, audit, org_name


def oauth_providers() -> List[dict]:
    """The providers with keys configured; in development also the others (shown as not configured, so the buttons can be seen before the keys exist)."""
    return oauth.enabled(include_unconfigured=settings.env != "production")


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
    if kind == "company":
        raise Invalid({"kind": "a company registers with the company form: country, tax identifier, address and the code sent to its e-mail"})
    if kind not in ORG_KINDS:
        errors["kind"] = "individual or company"
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
