import re
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.errors import Conflict, Invalid, NotFound, TooLarge
from epc.modules.masterdata import repository
from epc.modules.identity import public as identity
from epc.modules.masterdata.models import ClientIn, IssuerIn, OrganizationIn, PersonIn

PERSON_ROLES = ("designer", "checker", "approver", "responsible", "project_manager", "product_owner", "inspector", "auditor")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,23}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_LOGO = 1_000_000
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
FORBIDDEN_SVG = re.compile(rb"<\s*script|on[a-z]+\s*=|javascript:|<\s*foreignObject|<!ENTITY", re.I)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text.strip()).strip("-")[:24] or "item"


def _check_contact(data: dict, errors: Dict[str, str]) -> None:
    if data.get("email") and not EMAIL_RE.match(data["email"]):
        errors["email"] = "invalid e-mail"
    for k in ("legal_name", "name", "address", "website", "role", "registration"):
        if len(str(data.get(k, ""))) > 200:
            errors[k] = "up to 200 characters"


# ---- issuers (the companies documents are issued in the name of) ----
ISSUER_FIELDS = tuple(IssuerIn.model_fields)
ISSUER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")


def _issuer_defaults() -> dict:
    return {k: v for k, v in IssuerIn().model_dump().items() if k != "id"}


def _issuer_items() -> List[dict]:
    """The stored list. A project from before several issuers has one `organization.json`: it becomes the first issuer, with its logo."""
    if not repository.exists("issuers.json") and repository.exists("organization.json"):
        org = repository.load_organization()
        repository.save_list("issuers", [{"id": "principal", **{k: org[k] for k in _issuer_defaults() if k in org}}])
        repository.move_logo("organization", "issuer-principal")
    items = repository.load_list("issuers")
    if not items:                                           # a new account: its own company is the first issuer, with what it declared when it registered (it can be changed later)
        own = _account_company()
        if own.get("name"):
            items = [{"id": _slug_id(own["name"]), **_issuer_defaults(), "legal_name": own["name"], "tax_id": own.get("tax_id", ""), "email": own.get("contact_email", ""),
                      "address": own.get("address_line", "")}]
            repository.save_list("issuers", items)
    return items


def _account_company() -> dict:
    """The organization whose data this is: its name and, if it registered as a company, its tax id, contact e-mail and fiscal address."""
    try:
        slug = repository.current_scope()
        prof = identity.org_profile(slug) or {"name": (identity.org_name(slug) or "").strip()}
        a = prof.get("address") or {}
        line = ", ".join(x for x in (f"{a.get('street', '')} {a.get('number', '')}".strip(), a.get("locality", ""), a.get("region", ""), a.get("postal_code", "")) if x)
        return {**prof, "address_line": line}
    except Exception:                                       # noqa: BLE001 - no session (command line, tests)
        return {}


def _slug_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:32] or "emisor"


def issuers() -> List[dict]:
    items = _issuer_items()
    return [{**_issuer_defaults(), **it, "default": n == 0, "has_logo": repository.logo_path(f"issuer-{it['id']}") is not None} for n, it in enumerate(items)]


def issuer(iid: str = "") -> Optional[dict]:
    """The issuer asked for; the default (first) one when `iid` is empty or unknown; None when there are none."""
    items = issuers()
    return next((i for i in items if i["id"] == iid), items[0] if items else None)


def _validate_issuer(data: dict) -> None:
    errors: Dict[str, str] = {}
    if not data["legal_name"].strip():
        errors["legal_name"] = "required"
    _check_contact(data, errors)
    if errors:
        raise Invalid(errors)


def add_issuer(body: IssuerIn) -> dict:
    data = body.model_dump()
    _validate_issuer(data)
    items = _issuer_items()
    base, n = _slug_id(data["id"] or data["legal_name"]), 1
    data["id"] = base
    while any(i["id"] == data["id"] for i in items):
        n += 1
        data["id"] = f"{base}-{n}"
    repository.save_list("issuers", items + [data])
    return issuer(data["id"])


def update_issuer(iid: str, body: IssuerIn) -> dict:
    data = body.model_dump()
    data["id"] = iid
    _validate_issuer(data)
    items = _issuer_items()
    k = next((n for n, i in enumerate(items) if i["id"] == iid), None)
    if k is None:
        raise NotFound("issuer not found")
    items[k] = data
    repository.save_list("issuers", items)
    return issuer(iid)


def make_default_issuer(iid: str) -> List[dict]:
    items = _issuer_items()
    k = next((n for n, i in enumerate(items) if i["id"] == iid), None)
    if k is None:
        raise NotFound("issuer not found")
    repository.save_list("issuers", [items[k]] + items[:k] + items[k + 1:])
    return issuers()


def delete_issuer(iid: str, in_use) -> None:
    """`in_use(id)` says whether a project issues in its name (the caller knows the projects)."""
    items = _issuer_items()
    kept = [i for i in items if i["id"] != iid]
    if len(kept) == len(items):
        raise NotFound("issuer not found")
    if in_use(iid):
        raise Conflict({"issuer": "projects issue in the name of this company: change them first"})
    repository.save_list("issuers", kept)
    repository.delete_logo(f"issuer-{iid}")


def organization() -> dict:
    """The default issuer (kept for the code that asks for the office profile)."""
    i = issuer("")
    return {**OrganizationIn().model_dump(), **{k: i[k] for k in OrganizationIn.model_fields if i and k in i}, "has_logo": bool(i and i["has_logo"])}


def save_organization(body: OrganizationIn) -> dict:
    data = body.model_dump()
    _validate_issuer({**data, "id": ""})
    items = _issuer_items()
    if items:
        items[0] = {**items[0], **data}
        repository.save_list("issuers", items)
    else:
        repository.save_list("issuers", [{"id": _slug_id(data["legal_name"]), **data}])
    return organization()


# ---- clients ----
def clients() -> List[dict]:
    return [{**c, "has_logo": repository.logo_path(f"client-{c['id']}") is not None} for c in sorted(repository.load_list("clients"), key=lambda c: c["name"].lower())]


def client(cid: str) -> Optional[dict]:
    return next((c for c in clients() if c["id"].upper() == cid.upper()), None)


def _validate_client(data: dict) -> None:
    errors: Dict[str, str] = {}
    if not ID_RE.match(data["id"]):
        errors["id"] = "1-24 letters, digits, - or _"
    if not data["name"].strip():
        errors["name"] = "required"
    _check_contact(data, errors)
    if errors:
        raise Invalid(errors)


def add_client(body: ClientIn) -> dict:
    data = body.model_dump()
    data["id"] = data["id"].strip().upper()
    _validate_client(data)
    items = repository.load_list("clients")
    if any(c["id"].upper() == data["id"] for c in items):
        raise Conflict({"id": "a client with this code already exists"})
    repository.save_list("clients", items + [data])
    return client(data["id"])


def update_client(cid: str, body: ClientIn) -> dict:
    data = body.model_dump()
    data["id"] = cid.upper()
    _validate_client(data)
    items = repository.load_list("clients")
    i = next((k for k, c in enumerate(items) if c["id"].upper() == cid.upper()), None)
    if i is None:
        raise NotFound("client not found")
    items[i] = data
    repository.save_list("clients", items)
    return client(cid)


def delete_client(cid: str) -> None:
    items = repository.load_list("clients")
    kept = [c for c in items if c["id"].upper() != cid.upper()]
    if len(kept) == len(items):
        raise NotFound("client not found")
    repository.save_list("clients", kept)
    repository.delete_logo(f"client-{cid.upper()}")


# ---- people ----
def people() -> List[dict]:
    return sorted(({**p, "roles": p.get("roles", [])} for p in repository.load_list("people")), key=lambda p: p["name"].lower())


def person(pid: str) -> Optional[dict]:
    return next((p for p in people() if p["id"] == pid), None)


def save_person(body: PersonIn, pid: Optional[str] = None) -> dict:
    data = body.model_dump()
    errors: Dict[str, str] = {}
    if not data["name"].strip():
        errors["name"] = "required"
    if any(r not in PERSON_ROLES for r in data["roles"]):
        errors["roles"] = "one of " + ", ".join(PERSON_ROLES)
    data["roles"] = [r for r in PERSON_ROLES if r in data["roles"]]
    _check_contact(data, errors)
    if errors:
        raise Invalid(errors)
    items = repository.load_list("people")
    if pid is None:
        base = _slug(data["name"])
        data["id"], n = base, 1
        while any(p["id"] == data["id"] for p in items):
            n += 1
            data["id"] = f"{base}-{n}"
        items.append(data)
    else:
        i = next((k for k, p in enumerate(items) if p["id"] == pid), None)
        if i is None:
            raise NotFound("person not found")
        data["id"] = pid
        items[i] = data
    repository.save_list("people", items)
    return data


def delete_person(pid: str) -> None:
    items = repository.load_list("people")
    kept = [p for p in items if p["id"] != pid]
    if len(kept) == len(items):
        raise NotFound("person not found")
    repository.save_list("people", kept)


# ---- logos ----
def _logo_key(kind: str) -> str:
    if kind == "organization":                                      # the default issuer
        i = issuer("")
        if i is None:
            raise NotFound("no issuer")
        return f"issuer-{i['id']}"
    if kind.startswith("issuer-"):
        if not any(i["id"] == kind[7:] for i in issuers()):
            raise NotFound("issuer not found")
        return kind
    if kind.startswith("client-") and ID_RE.match(kind[7:]):
        if client(kind[7:]) is None:
            raise NotFound("client not found")
        return "client-" + kind[7:].upper()
    raise Invalid({"kind": "organization or client-<ID>"})


def save_logo(kind: str, filename: str, content: bytes) -> dict:
    key = _logo_key(kind)
    ext = Path(filename).suffix.lower()
    if ext not in repository.LOGO_EXT:
        raise Invalid({"file": "use an SVG or PNG logo"})
    if len(content) > MAX_LOGO:
        raise TooLarge({"file": "the logo must be 1 MB or less"})
    if ext == ".png" and not content.startswith(PNG_MAGIC):
        raise Invalid({"file": "not a valid PNG"})
    if ext == ".svg" and (b"<svg" not in content[:4000].lower() or FORBIDDEN_SVG.search(content)):
        raise Invalid({"file": "the SVG is not valid or contains active content (scripts)"})
    repository.save_logo(key, ext, content)
    return {"kind": kind, "file": f"{key}{ext}"}


def logo_file(kind: str) -> Path:
    p = repository.logo_path(_logo_key(kind))
    if not p:
        raise NotFound("no logo")
    return p


def delete_logo(kind: str) -> None:
    repository.delete_logo(_logo_key(kind))
