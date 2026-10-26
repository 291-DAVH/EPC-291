"""Project registers of the methodology (PM²: risks, changes, issues, decisions, assumptions, stakeholders).

They are platform data, not documents: each record has an id (RIE-001), validated fields defined by the methodology pack, and a history of who changed what and when.
Records are never deleted (PM² keeps the trail): they change status. The reports (D11 to D15) read from here.
"""
import datetime as dt
from pathlib import Path
from typing import Callable, Dict, List, Optional

from epc.core import clock, ids
from epc.core.errors import Conflict, Forbidden, Invalid, NotFound
from epc.core.fsutil import today
from epc.modules.identity import public as identity
from epc.modules.projects import public as projects
from epc.modules.registers import repository

TEXT_MAX, LONGTEXT_MAX = 300, 4000


def _defs(d: Path) -> dict:
    meta = projects.read_meta(d)
    defs = repository.definitions(meta.get("methodology") or "pm2")
    if not defs:
        raise Conflict({"methodology": "this methodology has no registers"})
    return defs


def _kind(d: Path, kind: str) -> dict:
    r = next((x for x in _defs(d)["registers"] if x["id"] == kind), None)
    if not r:
        raise NotFound("register not found")
    return r


def _lang(d: Path, lang: Optional[str]) -> str:
    if lang in ("es", "en"):
        return lang
    return "es" if (projects.read_meta(d).get("locale") or "es").lower().startswith("es") else "en"


def _view_field(f: dict, lang: str) -> dict:
    out = {"id": f["id"], "type": f["type"], "required": bool(f.get("required")), "label": f["label"].get(lang) or f["label"]["es"]}
    for k in ("min", "max", "default"):
        if k in f:
            out[k] = f[k]
    if f["type"] == "enum":
        out["options"] = [{"id": o["id"], "label": o.get(lang) or o["es"]} for o in f["options"]]
    return out


def view(d: Path, lang: Optional[str] = None) -> dict:
    lg = _lang(d, lang)
    meta = projects.read_meta(d)
    defs = repository.definitions(meta.get("methodology") or "pm2")
    if not defs:                                                    # a methodology without registers (for example one that is not available yet): say so, do not fail
        return {"methodology": meta.get("methodology") or "pm2", "available": False, "language": lg, "registers": []}
    regs = []
    for r in defs["registers"]:
        items = repository.load(d, r["id"])
        closed = sum(1 for i in items if i.get("status") in r["closed_states"])
        regs.append({"id": r["id"], "prefix": r["prefix"], "name": r["name"].get(lg) or r["name"]["es"], "columns": r["columns"], "closed_states": r["closed_states"],
                     "fields": [_view_field(f, lg) for f in r["fields"]], "derived": r.get("derive"), "counts": {"total": len(items), "active": len(items) - closed}})
    return {"methodology": defs["methodology"], "available": True, "language": lg, "registers": regs}


def items(d: Path, kind: str) -> List[dict]:
    _kind(d, kind)
    return repository.load(d, kind)


def _clean(r: dict, data: dict, creating: bool) -> dict:
    fields = {f["id"]: f for f in r["fields"]}
    errors: Dict[str, str] = {}
    out: dict = {}
    for k in data:
        if k not in fields:
            errors[k] = "unknown field"
    for fid, f in fields.items():
        if fid not in data:
            if creating and f.get("required") and "default" not in f:
                errors[fid] = "required"
            continue
        v = data[fid]
        if v is None or (isinstance(v, str) and not v.strip()):
            if f.get("required"):
                errors[fid] = "required"
            else:
                out[fid] = None if f["type"] in ("number", "date") else ""
            continue
        t = f["type"]
        if t in ("text", "longtext"):
            v = str(v).strip()
            if len(v) > (TEXT_MAX if t == "text" else LONGTEXT_MAX):
                errors[fid] = f"at most {TEXT_MAX if t == 'text' else LONGTEXT_MAX} characters"
                continue
        elif t == "number":
            try:
                v = int(v)
            except (TypeError, ValueError):
                errors[fid] = "a whole number"
                continue
            if v < f.get("min", v) or v > f.get("max", v):
                errors[fid] = f"between {f.get('min')} and {f.get('max')}"
                continue
        elif t == "date":
            try:
                dt.date.fromisoformat(str(v))
            except ValueError:
                errors[fid] = "ISO date, e.g. 2026-10-23"
                continue
            v = str(v)
        elif t == "enum":
            if v not in [o["id"] for o in f["options"]]:
                errors[fid] = "one of " + ", ".join(o["id"] for o in f["options"])
                continue
        out[fid] = v
    if errors:
        raise Invalid(errors)
    return out


def _derive(r: dict, rec: dict) -> None:
    if r.get("derive") == "risk_level":                       # PM²: level = probability x impact; low <= 2, medium 3 to 16, high >= 20
        lv = (rec.get("probability") or 0) * (rec.get("impact") or 0)
        rec["level"] = lv
        rec["level_name"] = "high" if lv >= 20 else "medium" if lv >= 3 else "low"


def _who() -> str:
    u = identity.current_user()
    return u.get("name") or u.get("email") or "-"


def _now() -> str:
    return clock.now_aware()


def _close_date(r: dict, rec: dict) -> None:
    if rec.get("status") in r["closed_states"] and any(f["id"] == "closed_on" for f in r["fields"]) and not rec.get("closed_on"):
        rec["closed_on"] = today().isoformat()


def create(d: Path, kind: str, data: dict) -> dict:
    r = _kind(d, kind)
    rec = {f["id"]: ("" if f["type"] not in ("number", "date") else None) for f in r["fields"]}
    rec.update({f["id"]: f["default"] for f in r["fields"] if "default" in f})
    rec.update(_clean(r, data, creating=True))
    all_items = repository.load(d, kind)
    n = ids.max_seq(all_items) + 1
    _derive(r, rec)
    _close_date(r, rec)
    now, who = _now(), _who()
    rec = {"id": f"{r['prefix']}-{n:03d}", **rec, "opened": today().isoformat(), "created_by": who, "updated_at": now,
           "history": [{"at": now, "by": who, "action": "created"}]}
    repository.save(d, kind, all_items + [rec])
    return rec


def update(d: Path, kind: str, item_id: str, data: dict) -> dict:
    r = _kind(d, kind)
    all_items = repository.load(d, kind)
    rec = next((i for i in all_items if i["id"] == item_id), None)
    if rec is None:
        raise NotFound("record not found")
    clean = _clean(r, data, creating=False)
    changes = {k: [rec.get(k), v] for k, v in clean.items() if rec.get(k) != v}
    if not changes:
        return rec
    rec.update({k: v[1] for k, v in changes.items()})
    _derive(r, rec)
    _close_date(r, rec)
    now = _now()
    rec["updated_at"] = now
    rec["history"].append({"at": now, "by": _who(), "action": "updated", "changes": changes})
    repository.save(d, kind, all_items)
    return rec


# ---- read helpers for other modules (reports)
def closed_states(d: Path, kind: str) -> List[str]:
    return _kind(d, kind)["closed_states"]


def labeler(d: Path, lang: Optional[str] = None) -> Callable[[str, str, str], str]:
    lg = _lang(d, lang)
    fields = {(r["id"], f["id"]): f for r in _defs(d)["registers"] for f in r["fields"]}

    def label(kind: str, field: str, value) -> str:
        f = fields.get((kind, field))
        if f and f["type"] == "enum":
            o = next((o for o in f["options"] if o["id"] == value), None)
            return (o.get(lg) or o["es"]) if o else str(value or "")
        return "" if value is None else str(value)
    return label


# ---- observations: written by inspectors, auditors and staff; the customer can only answer
def _org_of(d: Path) -> str:
    return projects.read_meta(d).get("org", "")


def observation_definition(d: Path, lang: Optional[str] = None) -> dict:
    """Fields and option labels of the observation register (defined by the methodology) for the customer-surface screen."""
    return next(r for r in view(d, lang)["registers"] if r["id"] == "observation")


def create_observation(d: Path, data: dict) -> dict:
    if not identity.can("observation", "write"):
        raise Forbidden("only inspectors, auditors and the engineering team record observations")
    data = {k: v for k, v in data.items() if k not in ("status", "response", "closed_on")}      # a new observation is open and unanswered
    rec = create(d, "observation", data)
    identity.audit_event("observation_created", target=f"{projects.project_id(d)}:{rec['id']}", org_slug=_org_of(d), detail={"severity": rec["severity"], "type": rec["type"]})
    return rec


def update_observation(d: Path, item_id: str, data: dict) -> dict:
    if identity.can("observation", "write"):
        rec = update(d, "observation", item_id, data)
    elif identity.can("observation", "respond"):
        extra = set(data) - {"response"}
        if extra:
            raise Forbidden("the customer can only answer an observation")
        current = next((i for i in repository.load(d, "observation") if i["id"] == item_id), None)
        if current is None:
            raise NotFound("record not found")
        if current["status"] == "closed":
            raise Conflict({"status": "the observation is closed"})
        rec = update(d, "observation", item_id, {"response": data.get("response", ""), "status": "answered" if (data.get("response") or "").strip() else "open"})
    else:
        raise Forbidden("not allowed")
    identity.audit_event("observation_updated", target=f"{projects.project_id(d)}:{item_id}", org_slug=_org_of(d), detail={"status": rec["status"]})
    return rec

