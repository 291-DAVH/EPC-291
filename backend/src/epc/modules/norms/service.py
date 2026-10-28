"""Review of the norm data by a norm reviewer: every point (a rule, a calculation table or constant, a design criterion) can be corrected and approved.

A point is *pending* until someone approves it; approving stores who, when, a note and the fingerprint of the approved value. Editing a point returns it to pending
(unless saved with approval); if the value changes by any other means after approval (for example a git merge) the point shows as *stale* and needs a new approval.
The reviewer corrects values, never the structure of the data: tables keep their shape, rules keep their fields.
"""
import copy
from typing import Dict, List, Optional, Tuple

from epc.core import clock
from epc.core.errors import Conflict, Invalid, NotFound, first_or_404
from epc.core.text import slugify
from epc.core.hashing import sha256_json
from epc.modules.identity import public as identity
from epc.modules.norms import repository

RULE_TYPES = ("obligatorio", "recomendado", "prohibido")
SOURCE_KEYS = ("norma", "edicion", "clausula", "pagina_impresa")
TABLE_SECTIONS = {"cap": ("tablas_capacidad", "Tablas de capacidad de corriente"), "fac": ("factores_correccion", "Factores de corrección"), "const": ("constantes", "Constantes")}
EDITABLE = {"rule": ["tema", "regla", "tipo", "parametros", "aplica_a", "fuente"], "criterion": ["label", "unit", "default", "options", "min", "max"], "table": ["value"],
            "lighting_rule": ["summary", "value", "unit", "plane", "clause"]}
LIGHTING_UNITS = ("lx", "ratio")


def slug(s: str) -> str:
    return slugify(s)


def sha(value) -> str:
    return sha256_json(value)


def _who() -> str:
    u = identity.current_user()
    return u.get("name") or u.get("email") or "-"


def _now() -> str:
    return clock.now_aware()


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


def _lighting_points() -> Dict[str, dict]:
    """The rules of each norm of the lighting engine, as the reviewer sees them (without the `review` flag the engine reads: approving changes it, and the approved value must not)."""
    units: Dict[str, dict] = {}
    for f in repository.lighting_files():
        data = repository.read(f)
        uid = "lighting-rule:" + slug(data["norm"])
        pts = [{"unit": uid, "kind": "lighting_rule", "key": r["id"], "title": r["summary"], "group": r["clause"], "ref": r["clause"], "value": {k: v for k, v in r.items() if k != "review"}} for r in data["rules"]]
        units[uid] = {"id": uid, "kind": "lighting_rule", "name": f"{data['norm']} · iluminación (valores por revisar)", "points": pts}
    return units


def lighting_rule(rule_id: str) -> Optional[dict]:
    """A rule of the lighting norms with its review status: `{id, norm, clause, summary, value, unit, status}`, or None when there is none."""
    rev = repository.review()
    for u in _lighting_points().values():
        for p in u["points"]:
            if p["key"] == rule_id:
                v = p["value"]
                return {"id": rule_id, "norm": v.get("norm", ""), "clause": v.get("clause", ""), "summary": v.get("summary", ""), "value": v.get("value"), "unit": v.get("unit", ""),
                        "status": _status(rev.get(_pid(p["unit"], p["key"])), v)}
    return None


def lighting_rules() -> List[dict]:
    """Every rule of the lighting norms that gives a level in lux (one with no value loaded yet is not one), with its review status: the lighting panel offers the approved ones."""
    out = []
    for u in _lighting_points().values():
        out += [r for p in u["points"] if p["value"].get("unit") == "lx" and _is_num(p["value"].get("value")) and (r := lighting_rule(p["key"]))]
    return out


def _all_units() -> Dict[str, dict]:
    units: Dict[str, dict] = dict(_lighting_points())
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
    p = first_or_404((p for p in _unit(unit_id)["points"] if p["key"] == key), "point not found")
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


LIGHTING_TEXT = {"summary": 240, "clause": 200, "plane": 40}                    # the texts of a lighting rule and how long each may be


def _lighting_field(key: str, value) -> Tuple[bool, object]:
    """One corrected field of a lighting rule: (valid, the value to keep or what to correct)."""
    if key in LIGHTING_TEXT:
        ok = isinstance(value, str) and bool(value.strip()) and len(value) <= LIGHTING_TEXT[key]
        return ok, value.strip() if ok else f"text, up to {LIGHTING_TEXT[key]} characters"
    if key == "value":
        return (True, value) if _is_num(value) and value >= 0 else (False, "a number from 0 up")
    if key == "unit":
        return (True, value) if value in LIGHTING_UNITS else (False, "one of " + ", ".join(LIGHTING_UNITS))
    return False, "not editable"


def _edit_lighting_rule(old: dict, patch: dict) -> dict:
    new, errors = copy.deepcopy(old), {}
    for k, v in patch.items():
        ok, kept = _lighting_field(k, v)
        if ok:
            new[k] = kept
        else:
            errors[k] = kept
    if not errors and new.get("unit") == "lx" and new.get("value") is not None and not new["value"] > 0:
        errors["value"] = "a level in lux is above 0"
    if errors:
        raise Invalid(errors)
    return new


def _edit_table(old, patch: dict):
    if set(patch) != {"value"}:
        raise Invalid({"value": "send the corrected table as {\"value\": ...}"})
    err = _same_shape(old, patch["value"])
    if err:
        raise Invalid({"value": err})
    return patch["value"]


_EDITORS = {"rule": _edit_rule, "table": _edit_table, "criterion": _edit_criterion, "lighting_rule": _edit_lighting_rule}       # point kind -> how its patch is validated and applied


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
def _store_rule(p: dict, new_value) -> None:
    for f in repository.rule_files():
        data = repository.read(f)
        for i, r in enumerate(data.get("reglas", [])):
            if r["id"] == p["key"]:
                data["reglas"][i] = new_value
                repository.write_like(f, data)
                return


def _store_table(p: dict, new_value) -> None:
    short, tid = p["key"].split(":", 1)
    f = repository.paths()["tables"]
    data = repository.read(f)
    data[TABLE_SECTIONS[short][0]][tid] = new_value
    repository.write_like(f, data)


def _store_criterion(p: dict, new_value) -> None:
    cat = repository.read(repository.paths()["criteria"])
    for i, c in enumerate(cat["criteria"]):
        if c["id"] == p["key"]:
            cat["criteria"][i] = new_value
    repository.write_criteria(cat)


def _write_lighting_rule(p: dict, change) -> None:
    """Rewrite one rule of its norm's file: `change` gets the rule as the file has it and returns it as it must be."""
    for f in repository.lighting_files():
        data = repository.read(f)
        for i, r in enumerate(data["rules"]):
            if r["id"] == p["key"]:
                data["rules"][i] = change(r)
                repository.write_like(f, data)
                return


def _store_lighting_rule(p: dict, new_value) -> None:
    _write_lighting_rule(p, lambda old: {**new_value, "review": old.get("review", "pending")})


def _sync_lighting_review(p: dict, status: str) -> None:
    """The engine reads whether a rule is approved from the rule itself: it follows what the reviewer decided."""
    flag = "approved" if status == "approved" else "pending"
    try:
        _write_lighting_rule(p, lambda old: {**old, "review": flag})
    except OSError:
        raise Conflict({"filesystem": "this installation is read-only: review the norms in the development copy of the repository"})
    repository.clear_engine_cache()


_STORERS = {"rule": _store_rule, "table": _store_table, "criterion": _store_criterion, "lighting_rule": _store_lighting_rule}       # point kind -> where its corrected value is written


def _store(p: dict, new_value) -> None:
    """Write the corrected value into its data file."""
    try:
        _STORERS[p["kind"]](p, new_value)
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


_AFTER_RECORD = {"criterion": lambda p, status: _sync_criteria_validated(), "lighting_rule": _sync_lighting_review}       # what a kind of point keeps in step once its review changed


def _record(p: dict, status: str, note: str, value, action: str, extra: Optional[dict] = None) -> dict:
    now, who = _now(), _who()
    rev = repository.review()
    rec = {"status": status, "by": who, "at": now, "note": note, "sha": sha(value)}
    rev[_pid(p["unit"], p["key"])] = rec
    repository.save_review(rev)
    repository.log_append({"at": now, "by": who, "point": _pid(p["unit"], p["key"]), "action": action, "note": note, **(extra or {})})
    _AFTER_RECORD.get(p["kind"], lambda *_: None)(p, status)
    return rec


def edit(unit_id: str, key: str, patch: dict, note: str = "", approve: bool = False) -> dict:
    p = _point(unit_id, key)
    old = p["value"]
    new = _EDITORS[p["kind"]](old, patch)
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
