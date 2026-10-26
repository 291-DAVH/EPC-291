"""Registration of a company: terms, the code sent to its e-mail and the validation that follows."""

import datetime as dt
import hmac
import secrets
import uuid
from typing import Tuple

from epc.core.config import settings
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound, TooManyRequests
from epc.modules.identity import repository as repo
from epc.modules.identity.models import Principal
from epc.modules.identity.checks import _check_email, _check_username, _slug
from epc.modules.identity.passwords import _check_password, hash_password, token_hash
from epc.modules.identity.sessions import _open_session, audit, org_name
from epc.modules.identity.throttle import _throttle


COMPANY_SEATS = 5


CODE_MINUTES, CODE_ATTEMPTS, RESEND_SECONDS, RESEND_MAX = 30, 5, 60, 3


def terms(lang: str = "es") -> dict:
    from epc.modules.identity import terms as T
    return {"version": T.VERSION, "text": T.TEXT.get(lang, T.TEXT["es"])}


def _mask(email: str) -> str:
    user, _, domain = email.partition("@")
    return (user[:2] + "*" * max(len(user) - 2, 1)) + "@" + domain


def _code_hash(rid: str, code: str) -> str:
    return token_hash(f"{rid}:{code}")


def _send_code(email: str, code: str, org_name: str, lang: str) -> None:
    from epc.core import mail
    if lang == "en":
        mail.send(email, "Your verification code", f"Code to register {org_name}: {code}\n\nIt expires in {CODE_MINUTES} minutes. If you did not request it, ignore this message.")
    else:
        mail.send(email, "Tu código de verificación", f"Código para registrar a {org_name}: {code}\n\nVence en {CODE_MINUTES} minutos. Si no lo pediste, ignora este mensaje.")


def company_register(b: dict, ip: str = "") -> dict:
    """First step: the form is checked as a whole and a code goes to the company's e-mail. Nothing is created as an account until the code comes back."""
    from epc.modules.identity import countries as C
    from epc.modules.identity import terms as T
    if settings.signup != "open":
        raise Forbidden("self-registration is closed: ask for an invitation")
    _throttle(f"reg:{ip}", 15)
    _throttle(f"reg:{ip}", 15, add=True)
    e: dict = {}
    country = (b.get("country") or "").upper()
    if country not in C.COUNTRIES:
        raise Invalid({"country": "choose the country of the company"})
    name = (b.get("org_name") or "").strip()
    if not 2 <= len(name) <= 200:
        e["org_name"] = "2 to 200 characters"
    tax = C.check_tax_id(country, b.get("tax_id", ""))
    if tax is None:
        e["tax_id"] = f"not a valid {C.tax_label(country)}"
    addr = {k: (b.get(k) or "").strip() for k in ("street", "number", "locality", "region")}
    for k, v in addr.items():
        if not v or len(v) > 100:
            e[k] = "required, up to 100 characters"
    postal = C.check_postal(country, b.get("postal_code", ""))
    if postal is None:
        e["postal_code"] = f"not a valid postal code for {C.COUNTRIES[country]['name']['en']}"
    addr["postal_code"] = postal or ""
    try:
        email = _check_email(b.get("contact_email", ""))
    except Invalid as x:
        e["contact_email"] = x.detail["errors"]["email"]
        email = ""
    if email and C.is_free_mail(email):
        e["contact_email"] = "use the company's own e-mail address, not a free mailbox: the code and the validation go there"
    person = (b.get("name") or "").strip()
    if not person:
        e["name"] = "required"
    if not b.get("accept_terms") or b.get("terms_version") != T.VERSION:
        e["accept_terms"] = "accept the current terms"
    alias = None
    try:
        alias = _check_username(b.get("username"))
    except (Invalid, Conflict) as x:
        e["username"] = next(iter(x.detail["errors"].values()))
    try:
        _check_password(b.get("password", ""), email)
    except Invalid as x:
        e["password"] = next(iter(x.detail["errors"].values()))
    if e:
        raise Invalid(e)
    _conflicts_company(email, country, tax)
    code = f"{secrets.randbelow(10 ** 6):06d}"
    rid = uuid.uuid4()
    payload = {"country": country, "org_name": name, "tax_id": tax, "address": addr, "contact_email": email, "name": person, "username": alias, "password_hash": hash_password(b["password"]),
               "terms": {"version": T.VERSION, "accepted_at": repo.now().isoformat(), "ip": ip}, "lang": "en" if b.get("lang") == "en" else "es"}
    repo.purge_expired_registrations()
    _send_code(email, code, name, payload["lang"])                      # before storing: a company whose code cannot be delivered has no pending registration
    repo.insert_registration(rid, email, _code_hash(str(rid), code), payload, repo.now() + dt.timedelta(minutes=CODE_MINUTES))
    audit("company_registration_started", target=f"{country}:{tax}", ip=ip, email=email)
    return {"registration": str(rid), "email": _mask(email), "expires_minutes": CODE_MINUTES}


def _conflicts_company(email: str, country: str, tax: str) -> None:
    if repo.user_by_email(email):
        raise Conflict({"contact_email": "this e-mail is already registered"})
    if repo.org_by_tax(country, tax):
        raise Conflict({"tax_id": "this company is already registered: ask its administrator for an invitation"})


def _registration(rid: str) -> dict:
    try:
        row = repo.registration_by_id(rid)
    except (ValueError, TypeError):
        row = None
    if not row or repo.as_utc(row["expires_at"]) <= repo.now():
        raise NotFound("the registration expired: start again")
    return row


def company_verify(rid: str, code: str, ip: str = "") -> Tuple[str, Principal]:
    """Second step: the code from the company's e-mail creates the organization (pending the team's validation), its first account and the session."""
    row = _registration(rid)
    if row["attempts"] >= CODE_ATTEMPTS:
        repo.delete_registration(rid)
        raise TooManyRequests({"errors": {"code": "too many wrong codes: start the registration again"}})
    if not hmac.compare_digest(_code_hash(str(row["id"]), (code or "").strip()), row["code_hash"]):
        repo.update_registration(rid, attempts=row["attempts"] + 1)
        raise Invalid({"code": "wrong code"})
    pl = row["payload"]
    _conflicts_company(pl["contact_email"], pl["country"], pl["tax_id"])
    profile = {"address": pl["address"], "contact_email": pl["contact_email"], "registered_by": pl["name"], "terms": pl["terms"]}
    org = repo.insert_org(_slug(pl["org_name"]), pl["org_name"], "company", COMPANY_SEATS, country=pl["country"], tax_id=pl["tax_id"], validation="pending", profile=profile)
    user = repo.insert_user(pl["contact_email"], pl["name"], pl["password_hash"], username=pl.get("username"))
    repo.insert_membership(org["id"], user["id"], "owner")
    repo.delete_registration(rid)
    token, p = _open_session(user, org)
    audit("company_registered", target=f"{pl['country']}:{pl['tax_id']}", org=str(org["id"]), actor=p, ip=ip, detail={"validation": "pending", "terms": pl["terms"]["version"]})
    return token, p


def company_resend(rid: str) -> dict:
    row = _registration(rid)
    if row["sends"] >= RESEND_MAX:
        raise TooManyRequests({"errors": {"code": "too many codes requested: start the registration again"}})
    if (repo.now() - repo.as_utc(row["last_sent_at"])).total_seconds() < RESEND_SECONDS:
        raise TooManyRequests({"errors": {"code": f"wait {RESEND_SECONDS} seconds before asking for another code"}})
    code = f"{secrets.randbelow(10 ** 6):06d}"
    pl = row["payload"]
    _send_code(row["email"], code, pl["org_name"], pl.get("lang", "es"))
    repo.update_registration(rid, code_hash=_code_hash(str(row["id"]), code), sends=row["sends"] + 1, last_sent_at=repo.now(), attempts=0)
    return {"registration": rid, "email": _mask(row["email"]), "expires_minutes": CODE_MINUTES}
