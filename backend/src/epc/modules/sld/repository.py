"""Files of the SLD feature inside workspace/02-engineering/electrical/<package>/ (src = input, build = scratch, drawings/calc = outputs)."""
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

# Excel column <-> form field names, used to turn the plugin's example workbook into form data
BOARD_ROWS = [("NOMBRE", "name"), ("TENSION_V", "voltage_v"), ("SISTEMA", "system"), ("ICC_KA", "icc_ka"), ("FP_DEFAULT", "fp_default"),
              ("FRECUENCIA_HZ", "frequency_hz"), ("PROYECTO", "project"), ("LONG_ACOMETIDA_m", "feeder_length_m")]
CIRCUIT_COLS = [("TAG", "tag"), ("DESCRIPCION", "description"), ("CARGA", "load"), ("UNIDAD_CARGA", "unit"), ("DESTINO", "destination"), ("PARENT_TAG", "parent_tag"),
                ("TOPOLOGY", "topology"), ("FASE", "phase"), ("LONGITUD_m", "length_m"), ("FP", "fp"), ("RENDIMIENTO", "efficiency"), ("KIND", "kind"),
                ("NOTAS", "notes"), ("CABLE_TIPO", "cable_type")]
PACKAGE = "PQ-01"
DISCIPLINE = "electrical"


def pkg(d: Path) -> Path:
    return d / "workspace" / "02-engineering" / DISCIPLINE / PACKAGE


def input_file(d: Path) -> Path:
    return pkg(d) / "src" / "sld-input.json"


def work_dir(d: Path) -> Path:
    return pkg(d) / "build" / "sld"


def load_input(d: Path):
    return read_json(input_file(d), None)


def save_input(d: Path, data: dict) -> None:
    write_json(input_file(d), {"schema_version": "1.0", **data})


def load_status(d: Path) -> dict:
    return read_json(work_dir(d) / "status.json", {"state": "idle", "outputs": [], "log": []})


def save_status(d: Path, status: dict) -> None:
    write_json(work_dir(d) / "status.json", status)


def run_design(work: Path, name: str, data: dict, criteria: dict, logos: Dict[str, Path], diagrams: str = "sld"):
    """Criteria-driven calculation + SLD through the engine's `epc_drawing.board_design` (the plugin pipeline, as it runs inside Claude)."""
    work.mkdir(parents=True, exist_ok=True)
    write_json(work / "input.json", data)
    write_json(work / "criteria.json", criteria)
    cmd = [sys.executable, "-m", "epc_drawing.board_design", "--input", str(work / "input.json"), "--criteria", str(work / "criteria.json"),
           "--out", str(work), "--name", name, "--diagrams", diagrams]
    for k, p in logos.items():
        cmd += ["--logo", f"{k}={p}"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=900)


def read_summary(work: Path) -> dict:
    return read_json(work / "out" / "summary.json", {}) or {}


def render_pdfs(out: Path, name: str) -> List[str]:
    """PDF of every DXF produced (the deliverable rendering of the drawing), through the engine's exporter. Returns warnings, never raises."""
    warnings: List[str] = []
    for dxf in sorted(out.glob(f"{name}*.dxf")):
        res = subprocess.run([sys.executable, "-m", "epc_drawing.export.pdf", str(dxf), str(dxf.with_suffix(".pdf"))], capture_output=True, text=True, timeout=300)
        if res.returncode != 0:
            warnings.append(f"AVISO no se pudo generar el PDF de {dxf.name}: {(res.stderr or res.stdout).strip()[-200:]}")
    return warnings


def publish(d: Path, out: Path, name: str, previous: List[str], previous_name: Optional[str] = None) -> List[str]:
    """Copy outputs into the engineering folders (SVG -> drawings/svg, DXF -> drawings/dxf, PDF -> drawings/pdf, calculation JSON -> calc).
    The files of the previous run that this run replaces are removed (an MLD run keeps the SLD files of an earlier run, and vice versa)."""
    base = pkg(d)
    prefixes = ("SLD_" + name, "MLD_" + name, name + "_")
    mine = [f for f in sorted(out.iterdir()) if f.name.startswith(prefixes) and f.suffix.lower() in (".svg", ".dxf", ".pdf", ".json")]
    now_kinds = {p for f in mine for p in prefixes if f.name.startswith(p)}
    kept: List[str] = []
    for rel in previous:
        fname = Path(rel).name
        replaced = (previous_name != name) or (fname.startswith(name + "_") and "calc/" in rel) or any(fname.startswith(p) for p in now_kinds)
        if replaced:
            (base / rel).unlink(missing_ok=True)
        else:
            kept.append(rel)
    placed: List[str] = []
    for f in mine:
        sub = {".svg": "drawings/svg", ".dxf": "drawings/dxf", ".pdf": "drawings/pdf", ".json": "calc"}[f.suffix.lower()]
        dest = base / sub / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)
        placed.append(f"{sub}/{f.name}")
    return kept + placed


def example_data() -> Dict:
    """The plugin's example workbook as input data (a starting point for the form)."""
    import openpyxl
    wb = openpyxl.load_workbook(settings.engine / "drawing" / "examples" / "sld" / "input_for_sld_V1.xlsx", data_only=True)
    board = {}
    for row in wb["TABLERO"].iter_rows(values_only=True):
        for col, key in BOARD_ROWS:
            if row and row[0] == col and row[1] is not None:
                board[key] = row[1]
    rows = list(wb["CIRCUITOS"].iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "TAG")
    hdr = [str(h).strip() if h else "" for h in rows[hi]]
    circuits = []
    for r in rows[hi + 1:]:
        if not r or r[0] is None or str(r[0]).lower().startswith(("campo", "fila")):
            continue
        dct = dict(zip(hdr, r))
        circuits.append({key: dct[col] for col, key in CIRCUIT_COLS if dct.get(col) is not None})
    return {"board": board, "circuits": circuits}
