from pathlib import Path
from typing import Dict

from epc.core.errors import Invalid, NotFound
from epc.core.fsutil import is_inside
from epc.modules.engineering import repository


def _kind(name: str) -> str:
    n = name.lower()
    if "mld" in n or "multifilar" in n or "multi-line" in n:
        return "multi_line"
    if "sld" in n or "unifilar" in n or "single-line" in n:
        return "single_line"
    return "drawing"


def overview(d: Path) -> dict:
    items = repository.scan(d)
    diagrams = [{**i, "kind": _kind(i["name"])} for i in items if i["what"] == "diagram"]
    documents = [{**i, "kind": "list" if i["ext"] in (".csv", ".xlsx") else "text"} for i in items if i["what"] == "document"]
    return {"diagrams": diagrams, "documents": documents,
            "counts": {"diagrams": len(diagrams), "documents": len(documents),
                       "by_kind": {k: sum(1 for x in diagrams if x["kind"] == k) for k in ("single_line", "multi_line", "drawing")}}}


def _file(d: Path, rel: str, exts: tuple) -> Path:
    if not rel or ".." in Path(rel).parts or Path(rel).suffix.lower() not in exts:
        raise Invalid({"path": "unsupported path"})
    known = {i["path"] for i in repository.scan(d)}
    if rel not in known or not is_inside(repository.base(d), rel):
        raise NotFound("file not found")
    return (repository.base(d) / rel).resolve()


def svg_file(d: Path, rel: str) -> Path:
    path = _file(d, rel, (".svg",))
    if path.stat().st_size > 5_000_000:
        raise Invalid({"path": "file too large to preview"})
    return path


def text_view(d: Path, rel: str) -> Dict:
    path = _file(d, rel, tuple(repository.TEXT_EXT))
    ext = path.suffix.lower()
    if ext == ".xlsx":
        if path.stat().st_size > 5_000_000:
            raise Invalid({"path": "file too large to preview"})
        return {"name": path.name, "format": "sheets", "sheets": repository.xlsx_sheets(path)}
    text = repository.read_text(path)
    truncated = repository.too_big(path)
    if ext == ".csv":
        return {"name": path.name, "format": "table", "rows": repository.csv_rows(text), "truncated": truncated}
    return {"name": path.name, "format": "text", "text": text, "truncated": truncated}


# ---- design criteria ----
import datetime as dt
import re

from epc.core.config import settings
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
    spec = next((s for s in cat["criteria"] if s["id"] == key), None)
    if not spec:
        raise NotFound("unknown criterion")
    return spec


def _now() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


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
