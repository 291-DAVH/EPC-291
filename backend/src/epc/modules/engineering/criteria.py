"""Design criteria of a project: the catalog, the value in force, changes with their source and the report of the criteria."""

import re
from pathlib import Path
from typing import Dict

from epc.core import clock
from epc.core.config import settings
from epc.core.errors import Invalid, NotFound, first_or_404
from epc.modules.engineering import repository
from epc.modules.projects import public as projects


SOURCES = ("client", "standard", "project")


SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]{0,40}$")


def _catalog(d: Path, discipline: str) -> Dict:
    if not SLUG_RE.match(discipline):
        raise Invalid({"discipline": "invalid"})
    jur = projects.read_meta(d).get("jurisdiction", "AR")
    cat = repository.load_catalog(settings.engine / "jurisdictions" / jur / discipline / "design-criteria.json") if re.match(r"^[A-Z]{2}$", jur) else {}
    if not cat:
        raise NotFound(f"no design criteria catalog for {jur}/{discipline}")
    return {**cat, "jurisdiction": jur}


def _clean(spec: dict, value):
    t = spec["type"]
    if t == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            try:
                value = float(str(value).replace(",", "."))
            except ValueError:
                raise Invalid({"value": "must be a number"})
        if value < spec.get("min", float("-inf")) or value > spec.get("max", float("inf")):
            raise Invalid({"value": f"must be between {spec.get('min')} and {spec.get('max')}"})
        return round(float(value), 3)
    if t == "choice":
        for opt in spec["options"]:
            if str(opt) == str(value):
                return opt
        raise Invalid({"value": "one of " + ", ".join(str(o) for o in spec["options"])})
    text = str(value).strip()
    if not text or len(text) > 200:
        raise Invalid({"value": "required, up to 200 characters"})
    return text


def criteria_view(d: Path, discipline: str) -> dict:
    cat = _catalog(d, discipline)
    data = repository.load_criteria(d)
    ov = data["overrides"].get(discipline, {})
    items = []
    for spec in cat["criteria"]:
        o = ov.get(spec["id"])
        items.append({**spec, "value": o["value"] if o else spec["default"], "overridden": bool(o),
                      "source": o["source"] if o else "default", "note": o.get("note", "") if o else "", "updated": o.get("updated") if o else None})
    return {"discipline": discipline, "jurisdiction": cat["jurisdiction"], "validated": cat.get("validated", False), "notice": cat.get("note", ""),
            "items": items, "changed": sum(1 for i in items if i["overridden"]),
            "history": [h for h in data["history"] if h["discipline"] == discipline][-20:][::-1]}


def _spec(cat: dict, key: str) -> dict:
    spec = first_or_404((s for s in cat["criteria"] if s["id"] == key), "unknown criterion")
    return spec


def _now() -> str:
    return clock.now_local()


def set_criterion(d: Path, discipline: str, key: str, body) -> dict:
    cat = _catalog(d, discipline)
    spec = _spec(cat, key)
    if body.source not in SOURCES:
        raise Invalid({"source": "one of " + ", ".join(SOURCES)})
    if len(body.note) > 300:
        raise Invalid({"note": "up to 300 characters"})
    value = _clean(spec, body.value)
    data = repository.load_criteria(d)
    ov = data["overrides"].setdefault(discipline, {})
    before = ov[key]["value"] if key in ov else spec["default"]
    now = _now()
    if value == spec["default"] and not body.note.strip():
        ov.pop(key, None)                                       # back to the default: nothing to keep as an override
    else:
        ov[key] = {"value": value, "source": body.source, "note": body.note.strip(), "updated": now}
    if value != before:
        data["history"].append({"discipline": discipline, "key": key, "from": before, "to": value, "source": body.source, "note": body.note.strip(), "at": now})
    repository.save_criteria(d, data)
    return criteria_view(d, discipline)


def reset_criterion(d: Path, discipline: str, key: str) -> dict:
    cat = _catalog(d, discipline)
    spec = _spec(cat, key)
    data = repository.load_criteria(d)
    ov = data["overrides"].get(discipline, {})
    if key in ov:
        before = ov.pop(key)["value"]
        data["history"].append({"discipline": discipline, "key": key, "from": before, "to": spec["default"], "source": "default", "note": "", "at": _now()})
        repository.save_criteria(d, data)
    return criteria_view(d, discipline)


_T = {"es": {"title": "Criterios de diseño", "ref": "Proyecto", "agreed": "Criterios modificados respecto de los valores base", "none": "Ningún criterio modificado: se usan los valores base.",
             "all": "Todos los criterios", "src": {"client": "pedido del cliente", "standard": "norma", "project": "decisión de proyecto", "default": "valor base"},
             "warn": "Valores base propuestos por la plataforma, sin validar contra las normas: confirmar antes de emitir.", "gen": "Generado automáticamente a partir de los criterios del proyecto."},
      "en": {"title": "Design criteria", "ref": "Project", "agreed": "Criteria changed from the base values", "none": "No criterion changed: base values are used.",
             "all": "All criteria", "src": {"client": "client requirement", "standard": "standard", "project": "project decision", "default": "base value"},
             "warn": "Base values proposed by the platform, not validated against the standards: confirm before issuing.", "gen": "Generated automatically from the project criteria."}}


def report(d: Path, discipline: str, lang: str) -> dict:
    lang = lang if lang in _T else "es"
    t = _T[lang]
    v = criteria_view(d, discipline)
    meta = projects.read_meta(d)

    def fmt(i):
        return f"{i['value']} {i['unit']}".strip()

    out = [f"# {t['title']} - {discipline}", "", f"{t['ref']}: {meta.get('project_name') or meta.get('project_code', '')} ({meta.get('client', '')})", ""]
    if not v["validated"]:
        out += [f"> {t['warn']}", ""]
    out += [f"## {t['agreed']}", ""]
    changed = [i for i in v["items"] if i["overridden"]]
    out += [f"- **{i['label'][lang]}**: {fmt(i)} ({t['src'][i['source']]})" + (f" - {i['note']}" if i["note"] else "") for i in changed] or [t["none"]]
    out += ["", f"## {t['all']}"]
    group = None
    for i in v["items"]:
        if i["group"][lang] != group:
            group = i["group"][lang]
            out += ["", f"### {group}", ""]
        out.append(f"- {i['label'][lang]}: {fmt(i)}")
    out += ["", f"_{t['gen']}_", ""]
    return {"markdown": "\n".join(out), "lang": lang}
