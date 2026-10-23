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
