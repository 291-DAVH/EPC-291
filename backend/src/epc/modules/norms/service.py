"""Review of the norm data by a norm reviewer: every point (a rule, a calculation table or constant, a design criterion) can be corrected and approved.

A point is *pending* until someone approves it; approving stores who, when, a note and the fingerprint of the approved value. Editing a point returns it to pending
(unless saved with approval); if the value changes by any other means after approval (for example a git merge) the point shows as *stale* and needs a new approval.
The reviewer corrects values, never the structure of the data: tables keep their shape, rules keep their fields.
"""
import copy
import datetime as dt
import hashlib
import json
import re
from typing import Dict, List, Optional, Tuple

from epc.core.errors import Conflict, Invalid, NotFound
from epc.modules.identity import public as identity
from epc.modules.norms import repository

RULE_TYPES = ("obligatorio", "recomendado", "prohibido")
SOURCE_KEYS = ("norma", "edicion", "clausula", "pagina_impresa")
TABLE_SECTIONS = {"cap": ("tablas_capacidad", "Tablas de capacidad de corriente"), "fac": ("factores_correccion", "Factores de corrección"), "const": ("constantes", "Constantes")}
EDITABLE = {"rule": ["tema", "regla", "tipo", "parametros", "aplica_a", "fuente"], "criterion": ["label", "unit", "default", "options", "min", "max"], "table": ["value"]}


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _who() -> str:
    u = identity.current_user()
    return u.get("name") or u.get("email") or "-"


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ---------------------------------------------------------------- points of each kind
def _rule_points() -> Dict[str, List[dict]]:
    """unit id -> points; a unit is one standard and edition."""
    units: Dict[str, List[dict]] = {}
    for f in repository.rule_files():
        for r in repository.read(f).get("reglas", []):
            src = r.get("fuente", {})
            uid = "rule:" + slug(f"{src.get('norma', '?')} {src.get('edicion', '')}")
            units.setdefault(uid, []).append({"unit": uid, "kind": "rule", "key": r["id"], "title": r.get("tema", r["id"]), "group": r.get("grupo", ""),
                                              "ref": f"{src.get('clausula', '')} · p. {src.get('pagina_impresa', '')}".strip(" ·"), "value": r,
                                              "unit_name": f"{src.get('norma', '?')} ({src.get('edicion', '')})"})
    return units


def _table_points() -> List[dict]:
    data = repository.read(repository.paths()["tables"])
    out = []
    for short, (section, label) in TABLE_SECTIONS.items():
        for tid, v in data.get(section, {}).items():
            title = v.get("titulo", tid) if isinstance(v, dict) else tid
            out.append({"unit": "table:aea-calculo", "kind": "table", "key": f"{short}:{tid}", "title": f"{tid} · {title}" if title != tid else tid, "group": label,
                        "ref": f"PDF p. {v['pagina_pdf']}" if isinstance(v, dict) and v.get("pagina_pdf") else "", "value": v})
    return out


def _criterion_points() -> List[dict]:
    cat = repository.read(repository.paths()["criteria"])
    return [{"unit": "criterion:ar-electrical", "kind": "criterion", "key": c["id"], "title": c["label"].get("es", c["id"]), "group": c["group"].get("es", ""),
             "ref": c.get("unit", ""), "value": c} for c in cat["criteria"]]


def _all_units() -> Dict[str, dict]:
    units: Dict[str, dict] = {}
    for uid, pts in sorted(_rule_points().items()):
        units[uid] = {"id": uid, "kind": "rule", "name": pts[0]["unit_name"], "points": pts}
    units["table:aea-calculo"] = {"id": "table:aea-calculo", "kind": "table", "name": "Tablas y constantes de cálculo (AEA 90364-7-771, 2006)", "points": _table_points()}
    units["criterion:ar-electrical"] = {"id": "criterion:ar-electrical", "kind": "criterion", "name": "Criterios de diseño · valores base (AR, eléctrica)", "points": _criterion_points()}
    return units


def _unit(unit_id: str) -> dict:
    u = _all_units().get(unit_id)
    if not u:
        raise NotFound("norm not found")
    return u


def _point(unit_id: str, key: str) -> dict:
    p = next((p for p in _unit(unit_id)["points"] if p["key"] == key), None)
    if not p:
        raise NotFound("point not found")
    return p


# ---------------------------------------------------------------- status
def _pid(unit: str, key: str) -> str:
    return f"{unit}|{key}"


def _status(rec: Optional[dict], value) -> str:
    if not rec:
        return "pending"
    if rec["status"] == "approved" and rec.get("sha") != sha(value):
        return "stale"
    return rec["status"]


def units() -> List[dict]:
    rev = repository.review()
    out = []
    for u in _all_units().values():
        c = {"total": len(u["points"]), "approved": 0, "rejected": 0, "pending": 0, "stale": 0}
        for p in u["points"]:
            c[_status(rev.get(_pid(p["unit"], p["key"])), p["value"])] += 1
        out.append({"id": u["id"], "kind": u["kind"], "name": u["name"], "counts": c})
    return out


def points(unit_id: str, status: Optional[str] = None, q: Optional[str] = None) -> dict:
    u = _unit(unit_id)
    rev = repository.review()
    rows = []
    for p in u["points"]:
        rec = rev.get(_pid(p["unit"], p["key"]))
        st = _status(rec, p["value"])
        if status and st != status:
            continue
        if q and q.lower() not in " ".join([p["key"], p["title"], p["group"], p["ref"]]).lower():
            continue
        rows.append({"key": p["key"], "title": p["title"], "group": p["group"], "ref": p["ref"], "status": st, "by": (rec or {}).get("by"), "at": (rec or {}).get("at")})
    rows.sort(key=lambda r: (r["group"], r["key"]))
    return {"unit": {"id": u["id"], "kind": u["kind"], "name": u["name"]}, "total": len(rows), "items": rows}


def point(unit_id: str, key: str) -> dict:
    p = _point(unit_id, key)
    rec = repository.review().get(_pid(unit_id, key))
    return {"unit": unit_id, "kind": p["kind"], "key": key, "title": p["title"], "group": p["group"], "ref": p["ref"], "value": p["value"],
            "editable": EDITABLE[p["kind"]], "status": _status(rec, p["value"]), "review": rec, "history": repository.log_read(_pid(unit_id, key), 50)}


# ---------------------------------------------------------------- validation of an edit
def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _same_shape(old, new, path: str = "") -> Optional[str]:
    """The reviewer corrects values; keys, list lengths and the kind of each value stay as they are."""
    if isinstance(old, dict):
        if not isinstance(new, dict) or set(old) != set(new):
            return f"{path or 'value'}: the keys cannot change"
        for k in old:
            e = _same_shape(old[k], new[k], f"{path}/{k}" if path else k)
            if e:
                return e
    elif isinstance(old, list):
        if not isinstance(new, list) or len(old) != len(new):
            return f"{path}: the number of elements cannot change"
        for i, (a, b) in enumerate(zip(old, new)):
            e = _same_shape(a, b, f"{path}[{i}]")
            if e:
                return e
    elif _is_num(old):
        if not _is_num(new):
            return f"{path}: must be a number"
    elif old is None:
        pass
    elif type(old) is not type(new):
        return f"{path}: must keep its type"
    return None


def _edit_rule(old: dict, patch: dict) -> dict:
    new, errors = copy.deepcopy(old), {}
    for k, v in patch.items():
        if k in ("tema", "regla"):
            if not isinstance(v, str) or not v.strip() or len(v) > (200 if k == "tema" else 1000):
                errors[k] = "text, up to " + ("200" if k == "tema" else "1000") + " characters"
            else:
                new[k] = v.strip()
        elif k == "tipo":
            if v not in RULE_TYPES:
                errors[k] = "one of " + ", ".join(RULE_TYPES)
            else:
                new[k] = v
        elif k == "parametros":
            if not isinstance(v, dict):
                errors[k] = "an object"
            else:
                new[k] = v
        elif k == "aplica_a":
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                errors[k] = "a list of text"
            else:
                new[k] = v
        elif k == "fuente":
            if not isinstance(v, dict) or set(v) - set(SOURCE_KEYS):
                errors[k] = "only " + ", ".join(SOURCE_KEYS)
            else:
                new["fuente"] = {**old.get("fuente", {}), **v}
        else:
            errors[k] = "not editable"
    if errors:
        raise Invalid(errors)
    return new


def _edit_criterion(old: dict, patch: dict) -> dict:
    new, errors = copy.deepcopy(old), {}
    for k, v in patch.items():
        if k == "label":
            if not isinstance(v, dict) or set(v) != {"es", "en"} or not all(isinstance(x, str) and x.strip() for x in v.values()):
                errors[k] = "es and en texts"
            else:
                new[k] = v
        elif k == "unit":
            if not isinstance(v, str):
                errors[k] = "text"
            else:
                new[k] = v
        elif k in ("min", "max"):
            if old.get("type") != "number" or not _is_num(v):
                errors[k] = "a number (number criteria only)"
            else:
                new[k] = v
        elif k == "options":
            if old.get("type") != "choice" or not isinstance(v, list) or not v or len(set(map(str, v))) != len(v):
                errors[k] = "a non-empty list without repeated values (choice criteria only)"
            else:
                new[k] = v
        elif k == "default":
            new[k] = v
        else:
            errors[k] = "not editable"
    if not errors:
        if new["type"] == "choice" and new["default"] not in new["options"]:
            errors["default"] = "must be one of the options"
        if new["type"] == "number":
            if not _is_num(new["default"]) or not (new["min"] <= new["default"] <= new["max"]):
                errors["default"] = f"a number between {new['min']} and {new['max']}"
    if errors:
        raise Invalid(errors)
    return new


def _diff(old, new, path: str = "") -> List[list]:
    out: List[list] = []
    if isinstance(old, dict) and isinstance(new, dict):
        for k in sorted(set(old) | set(new)):
            out += _diff(old.get(k), new.get(k), f"{path}/{k}" if path else str(k))
    elif isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        for i, (a, b) in enumerate(zip(old, new)):
            out += _diff(a, b, f"{path}[{i}]")
    elif old != new:
        out.append([path, old, new])
    return out[:200]


# ---------------------------------------------------------------- writing
def _store(p: dict, new_value) -> None:
    """Write the corrected value into its data file."""
    try:
        if p["kind"] == "rule":
            for f in repository.rule_files():
                data = repository.read(f)
                for i, r in enumerate(data.get("reglas", [])):
                    if r["id"] == p["key"]:
                        data["reglas"][i] = new_value
                        repository.write_like(f, data)
                        return
        elif p["kind"] == "table":
            short, tid = p["key"].split(":", 1)
            f = repository.paths()["tables"]
            data = repository.read(f)
            data[TABLE_SECTIONS[short][0]][tid] = new_value
            repository.write_like(f, data)
        else:
            cat = repository.read(repository.paths()["criteria"])
            for i, c in enumerate(cat["criteria"]):
                if c["id"] == p["key"]:
                    cat["criteria"][i] = new_value
            repository.write_criteria(cat)
    except OSError:
        raise Conflict({"filesystem": "this installation is read-only: review the norms in the development copy of the repository"})
    repository.clear_engine_cache()


def _sync_criteria_validated() -> None:
    """The catalog says it is validated only when every criterion is approved."""
    cat = repository.read(repository.paths()["criteria"])
    rev = repository.review()
    ok = all(_status(rev.get(_pid("criterion:ar-electrical", c["id"])), c) == "approved" for c in cat["criteria"])
    if cat.get("validated") != ok:
        cat["validated"] = ok
        try:
            repository.write_criteria(cat)
        except OSError:
            raise Conflict({"filesystem": "this installation is read-only: review the norms in the development copy of the repository"})


def _record(p: dict, status: str, note: str, value, action: str, extra: Optional[dict] = None) -> dict:
    now, who = _now(), _who()
    rev = repository.review()
    rec = {"status": status, "by": who, "at": now, "note": note, "sha": sha(value)}
    rev[_pid(p["unit"], p["key"])] = rec
    repository.save_review(rev)
    repository.log_append({"at": now, "by": who, "point": _pid(p["unit"], p["key"]), "action": action, "note": note, **(extra or {})})
    if p["kind"] == "criterion":
        _sync_criteria_validated()
    return rec


def edit(unit_id: str, key: str, patch: dict, note: str = "", approve: bool = False) -> dict:
    p = _point(unit_id, key)
    old = p["value"]
    if p["kind"] == "table":
        if set(patch) != {"value"}:
            raise Invalid({"value": "send the corrected table as {\"value\": ...}"})
        err = _same_shape(old, patch["value"])
        if err:
            raise Invalid({"value": err})
        new = patch["value"]
    elif p["kind"] == "rule":
        new = _edit_rule(old, patch)
    else:
        new = _edit_criterion(old, patch)
    changes = _diff(old, new)
    if not changes and not approve:
        raise Invalid({"value": "nothing changed"})
    if changes:
        _store(p, new)
        p = {**p, "value": new}
    action = "edited_approved" if approve else "edited"
    _record(p, "approved" if approve else "pending", note, new, action, {"changes": changes})
    return point(unit_id, key)


def approve(unit_id: str, key: str, note: str = "") -> dict:
    p = _point(unit_id, key)
    _record(p, "approved", note, p["value"], "approved")
    return point(unit_id, key)


def reject(unit_id: str, key: str, note: str) -> dict:
    if not (note or "").strip():
        raise Invalid({"note": "say what is wrong"})
    p = _point(unit_id, key)
    _record(p, "rejected", note.strip(), p["value"], "rejected")
    return point(unit_id, key)


def log(limit: int = 100) -> List[dict]:
    return repository.log_read(None, min(limit, 500))
