"""Who issues and who signs a project: the issuing company (chosen once per project) and, per discipline, who designs, checks and approves.

A board's title block takes these from here, so they are entered once and not on every board."""
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.errors import Invalid
from epc.modules.masterdata import repository, service
from epc.modules.projects import public as projects

BLANK = {"drawn_by": "", "checked_by": "", "approved_by": ""}


def view(d: Path) -> dict:
    meta = projects.read_meta(d)
    raw = repository.load_parties(d)
    iss = service.issuer(raw["issuer"])
    code = meta.get("client_code", "")
    known = service.client(code)
    cl = {**(known or {"id": code, "name": meta.get("client", ""), "tax_id": "", "has_logo": False}), "in_directory": known is not None}
    disciplines = list(meta.get("disciplines") or [])
    team = {disc: {**BLANK, **{k: v for k, v in (raw["team"].get(disc) or {}).items() if k in BLANK}} for disc in disciplines}
    return {"issuer_id": iss["id"] if iss else "", "issuer": iss, "issuers": [{"id": i["id"], "legal_name": i["legal_name"], "default": i["default"]} for i in service.issuers()],
            "client": cl, "disciplines": disciplines, "team": team, "people": [p["name"] for p in service.people()]}


def save(d: Path, body) -> dict:
    meta = projects.read_meta(d)
    disciplines = set(meta.get("disciplines") or [])
    errors: Dict[str, str] = {}
    if body.issuer and not any(i["id"] == body.issuer for i in service.issuers()):
        errors["issuer"] = "unknown issuer"
    team = {}
    for disc, tm in body.team.items():
        if disc not in disciplines:
            errors[f"team.{disc}"] = "not a discipline of this project"
            continue
        row = {k: v.strip() for k, v in tm.model_dump().items()}
        for k, v in row.items():
            if len(v) > 100:
                errors[f"team.{disc}.{k}"] = "up to 100 characters"
        team[disc] = row
    if errors:
        raise Invalid(errors)
    repository.save_parties(d, {"issuer": body.issuer, "team": team})
    return view(d)


def titleblock(d: Path, discipline: str = "electrical") -> dict:
    """The fields of the sheet's title block that belong to the project, not to a board."""
    v = view(d)
    i, c, t = v["issuer"] or {}, v["client"], v["team"].get(discipline, BLANK)
    return {"company": i.get("legal_name", ""), "company_cuit": i.get("tax_id", ""), "client": c.get("name", ""), "client_cuit": c.get("tax_id", ""),
            "drawn_by": t["drawn_by"], "checked_by": t["checked_by"], "approved_by": t["approved_by"]}


def logos(d: Path) -> Dict[str, Optional[Path]]:
    v = view(d)
    prov = repository.logo_path(f"issuer-{v['issuer_id']}") if v["issuer_id"] else None
    return {"provider": prov, "client": repository.logo_path("client-" + (v["client"].get("id") or "-").upper())}


def issuer_in_use(iid: str) -> bool:
    """Whether some project issues in the name of `iid` (an empty choice means the default issuer)."""
    default = (service.issuer("") or {}).get("id")
    for d in projects.list_project_dirs():
        try:
            chosen = repository.load_parties(d)["issuer"] or default
        except Exception:                                   # noqa: BLE001 - unreadable file: it does not count
            continue
        if chosen == iid:
            return True
    return False


def issuer_name(d: Path) -> str:
    return (view(d)["issuer"] or {}).get("legal_name", "")
