"""The engineering folder of a project: diagrams and documents, how each is shown to the person, and the calculation as a table."""

from pathlib import Path
from typing import Dict, Optional

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


CALC_SUFFIX = "_dimensionado"
DOC_KINDS = {".csv": "list", ".xlsx": "list", repository.PDF_EXT: "pdf"}           # how a document is shown by its extension; the rest is read as text


def _doc(item: dict) -> Optional[dict]:
    """How a workspace document is shown to the person. Internal formats (JSON data of the software) are not shown: the calculation is, as a table."""
    stem, ext = item["name"], item["ext"]
    if ext == ".json":
        if stem.endswith(CALC_SUFFIX):
            return {**item, "kind": "calculation", "name": stem[: -len(CALC_SUFFIX)]}
        return None
    return {**item, "kind": DOC_KINDS.get(ext, "text")}


def overview(d: Path, technical: bool = False) -> dict:
    items = repository.scan(d)
    diagrams = [{**i, "kind": _kind(i["name"])} for i in items if i["what"] == "diagram"]
    documents = []
    for i in items:
        if i["what"] != "document":
            continue
        doc = _doc(i)
        if doc:
            documents.append(doc)
        elif technical:
            documents.append({**i, "kind": "technical"})
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


def pdf_file(d: Path, rel: str) -> Path:
    return _file(d, rel, (repository.PDF_EXT,))


def svg_file(d: Path, rel: str) -> Path:
    path = _file(d, rel, (".svg",))
    if path.stat().st_size > 5_000_000:
        raise Invalid({"path": "file too large to preview"})
    return path


def text_view(d: Path, rel: str, technical: bool = False) -> Dict:
    path = _file(d, rel, tuple(repository.TEXT_EXT))
    if path.suffix.lower() == ".json" and not technical:
        raise NotFound("file not found")                       # the data files of the software are not a view for the person
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


def calculation_view(d: Path, rel: str) -> Dict:
    """A calculation result as a table: one row per circuit and the criteria that governed it (from the calculation files the generator published)."""
    from epc.core.fsutil import read_json
    path = _file(d, rel, (".json",))
    if not path.stem.endswith(CALC_SUFFIX):
        raise NotFound("file not found")
    stem = path.stem[: -len(CALC_SUFFIX)]
    calc = read_json(path, {}) or {}
    detail = read_json(path.with_name(stem + "_dimensionado_detalle.json"), {}) or {}
    crit = read_json(path.with_name(stem + "_criterios.json"), {}) or {}
    rows = []
    for tag, v in calc.items():
        x = detail.get(tag, {})
        rows.append({"tag": tag, "description": x.get("descripcion", ""), **v, "tipo": x.get("tipo"), "limite_pct": x.get("limite_pct"),
                     "du_propia_pct": x.get("du_propia_pct"), "iz_a": x.get("iz_a"), "cumple": x.get("cumple")})
    judged = [r for r in rows if r["cumple"] is not None]
    return {"name": stem, "rows": rows, "summary": {"circuits": len(rows), "compliant": sum(1 for r in judged if r["cumple"]), "non_compliant": sum(1 for r in judged if not r["cumple"])},
            "criteria": {"limits_pct": crit.get("limites_pct"), "conductor": crit.get("conductor"), "rcd_ma": crit.get("rcd_ma")} if crit else None}
