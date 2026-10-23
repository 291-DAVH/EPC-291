"""Reads the engineering workspace of a project: workspace/02-engineering/<discipline>/<package>/{drawings/svg,calc,docs}."""
import csv
import datetime as dt
from pathlib import Path
from typing import Dict, List

SVG_DIR = ("drawings", "svg")
TEXT_AREAS = ("calc", "docs")
TEXT_EXT = {".md", ".txt", ".csv", ".json", ".xlsx"}
MAX_TEXT_BYTES = 1_000_000
MAX_ROWS, MAX_COLS = 300, 30


def base(d: Path) -> Path:
    return d / "workspace" / "02-engineering"


def scan(d: Path) -> List[Dict]:
    root = base(d)
    out: List[Dict] = []
    if not root.is_dir():
        return out
    for f in sorted(root.rglob("*")):
        if not f.is_file() or f.name.startswith(".") or "_discipline" in f.parts:
            continue
        rel = f.relative_to(root)
        parts = rel.parts
        if len(parts) < 4:                                  # <discipline>/<package>/<area>/<file>
            continue
        area = "/".join(parts[2:-1])
        if f.suffix.lower() == ".svg" and tuple(parts[2:4]) == SVG_DIR:
            what = "diagram"
        elif parts[2] in TEXT_AREAS and f.suffix.lower() in TEXT_EXT:
            what = "document"
        else:
            continue
        st = f.stat()
        out.append({"path": rel.as_posix(), "discipline": parts[0], "package": parts[1], "area": area, "name": f.stem, "ext": f.suffix.lower(),
                    "what": what, "size": st.st_size, "modified": dt.datetime.fromtimestamp(st.st_mtime).date().isoformat()})
    return out


def read_text(path: Path) -> str:
    with open(path, "rb") as fh:
        raw = fh.read(MAX_TEXT_BYTES + 1)
    return raw[:MAX_TEXT_BYTES].decode("utf-8-sig", errors="replace")


def too_big(path: Path) -> bool:
    return path.stat().st_size > MAX_TEXT_BYTES


def csv_rows(text: str) -> List[List[str]]:
    rows = list(csv.reader(text.splitlines(), delimiter=";" if text.split("\n", 1)[0].count(";") > text.split("\n", 1)[0].count(",") else ","))
    return [r[:MAX_COLS] for r in rows[:MAX_ROWS]]


def xlsx_sheets(path: Path) -> Dict[str, List[List[str]]]:
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        return {ws.title: [["" if c is None else str(c) for c in row[:MAX_COLS]] for row in ws.iter_rows(max_row=MAX_ROWS, values_only=True)] for ws in wb.worksheets}
    finally:
        wb.close()


# ---- design criteria: catalog (per jurisdiction and discipline) and per-project overrides ----
def load_catalog(path: Path) -> Dict:
    from epc.core.fsutil import read_json
    return read_json(path, {}) or {}


def criteria_file(d: Path) -> Path:
    return d / "workspace" / "00-setup" / "design-criteria.json"


def load_criteria(d: Path) -> Dict:
    from epc.core.fsutil import read_json
    data = read_json(criteria_file(d), {}) or {}
    data.setdefault("schema_version", "1.0")
    data.setdefault("overrides", {})
    data.setdefault("history", [])
    return data


def save_criteria(d: Path, data: Dict) -> None:
    from epc.core.fsutil import write_json
    write_json(criteria_file(d), data)


# ---- sources that can be issued to the client ----
DELIVERABLE_DOC_EXT = (".xlsx", ".docx", ".pdf")


def issuable(d: Path) -> List[Dict]:
    """Drawings (DXF master + its PDF) and documents of the engineering workspace that may become deliverables."""
    root = base(d)
    out: List[Dict] = []
    if not root.is_dir():
        return out
    for pkg in sorted(root.glob("*/*")):
        if not pkg.is_dir() or "_discipline" in pkg.parts or pkg.name.startswith("_"):
            continue
        disc = pkg.parent.name
        for dxf in sorted((pkg / "drawings" / "dxf").glob("*.dxf")):
            files = {"dxf": dxf}
            pdf = pkg / "drawings" / "pdf" / (dxf.stem + ".pdf")
            if pdf.is_file():
                files["pdf"] = pdf
            out.append({"id": f"{disc}/{pkg.name}/drawing/{dxf.stem}", "name": dxf.stem, "discipline": disc, "package": pkg.name, "kind": "drawing", "files": files})
        for area in ("calc", "docs"):
            for f in sorted((pkg / area).glob("*")):
                if f.is_file() and f.suffix.lower() in DELIVERABLE_DOC_EXT:
                    out.append({"id": f"{disc}/{pkg.name}/{area}/{f.stem}{f.suffix.lower()}", "name": f.stem, "discipline": disc, "package": pkg.name,
                                "kind": "document", "files": {f.suffix.lstrip(".").lower(): f}})
    return out
