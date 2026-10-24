import re
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.errors import Conflict, Invalid, NotFound, TooLarge
from epc.modules.masterdata import repository
from epc.modules.masterdata.models import ClientIn, OrganizationIn, PersonIn

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


# ---- organization ----
def organization() -> dict:
    org = repository.load_organization()
    return {**OrganizationIn().model_dump(), **org, "has_logo": repository.logo_path("organization") is not None}


def save_organization(body: OrganizationIn) -> dict:
    data = body.model_dump()
    errors: Dict[str, str] = {}
    if not data["legal_name"].strip():
        errors["legal_name"] = "required"
    _check_contact(data, errors)
    if errors:
        raise Invalid(errors)
    repository.save_organization(data)
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
    return sorted(repository.load_list("people"), key=lambda p: p["name"].lower())


def person(pid: str) -> Optional[dict]:
    return next((p for p in people() if p["id"] == pid), None)


def save_person(body: PersonIn, pid: Optional[str] = None) -> dict:
    data = body.model_dump()
    errors: Dict[str, str] = {}
    if not data["name"].strip():
        errors["name"] = "required"
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
    if kind == "organization":
        return "organization"
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
