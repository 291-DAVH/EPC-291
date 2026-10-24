"""Files of the reporting step: the methodology's report catalog, the PM² registers kept as Markdown tables, generated reports and their log."""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

MGMT = Path("workspace") / "05-management"
ID_FORMS = {
    "rfc": re.compile(r"^rfc-?\d+$", re.I), "risk": re.compile(r"^(RIE|RIS)-?\d+$", re.I),
    "issue": re.compile(r"^(BLQ|PND|INF|PA|INC)-?\d+$", re.I), "stakeholder": re.compile(r"^STK-?\d+$", re.I),
}


def catalog(methodology: str) -> Optional[dict]:
    return read_json(settings.methodologies_dir / methodology / "reports.json", None)


def mgmt(d: Path) -> Path:
    return d / MGMT


# ---- registers (Markdown tables written by the management workflow)
def _cells(line: str) -> List[str]:
    return [c.strip().strip("`*").strip() for c in line.strip().strip("|").split("|")]


def _tables(text: str):
    lines = text.splitlines()
    i = 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            header = [h.lower() for h in _cells(lines[i])]
            rows = []
            i += 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_cells(lines[i]))
                i += 1
            yield header, rows
        else:
            i += 1


def read_register(d: Path, filename: str, form: str) -> List[Dict[str, str]]:
    """Rows of the tables of `filename` whose first cell is an id of the given form (rfc, risk, issue, stakeholder). Illustrative `EJ-` rows are skipped."""
    f = mgmt(d) / filename
    if not f.exists():
        return []
    rx = ID_FORMS[form]
    out = []
    for header, rows in _tables(f.read_text(encoding="utf-8-sig")):
        for r in rows:
            if r and rx.match(r[0]):
                out.append({"id": r[0].upper() if form != "rfc" else r[0].lower(), **{h: (r[i] if i < len(r) else "") for i, h in enumerate(header) if i > 0}})
    return out


# ---- generated reports
def generated(d: Path) -> List[dict]:
    return read_json(mgmt(d) / "reports" / "generated.json", []) or []


def save_generated(d: Path, items: List[dict]) -> None:
    write_json(mgmt(d) / "reports" / "generated.json", items)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def render_pdf(doc: dict, dst: Path) -> None:
    """PDF through the engine exporter."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "report.json"
        src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        res = subprocess.run([sys.executable, "-m", "epc_drawing.export.report_pdf", str(src), str(dst)], capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        raise RuntimeError(f"could not render the report: {(res.stderr or res.stdout).strip()[-300:]}")
