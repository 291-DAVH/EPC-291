"""Files of the SLD feature inside workspace/02-engineering/electrical/<package>/ (src = input, build = scratch, drawings/calc = outputs)."""
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json
from epc.core.text import slugify

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


def route_kinds() -> List[str]:
    from epc_calc import aea_route                                     # the engine owns the kinds of installation (single source)
    return list(aea_route.KINDS)


def route_errors(route: List[dict]) -> Dict[str, str]:
    from epc_calc import aea_route
    return aea_route.validate(route)


def route_total(route: List[dict]) -> float:
    from epc_calc import aea_route
    return aea_route.total_length(route)


def boards_dir(d: Path) -> Path:
    return pkg(d) / "src" / "boards"


def slug(name: str) -> str:
    return slugify(name, 40)


def input_file(d: Path, bid: str) -> Path:
    return boards_dir(d) / bid / "sld-input.json"


def work_dir(d: Path, bid: str) -> Path:
    return pkg(d) / "build" / "sld" / bid


def migrate_legacy(d: Path) -> None:
    """A project from before several boards had one `src/sld-input.json` and one `build/sld`: it becomes the first board, nothing is lost."""
    legacy = pkg(d) / "src" / "sld-input.json"
    if not legacy.is_file():
        return
    data = read_json(legacy, {}) or {}
    bid = slug((data.get("board") or {}).get("name", "")) or "tablero-1"
    target = input_file(d, bid)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy), str(target))
    old, new = pkg(d) / "build" / "sld", work_dir(d, bid)
    new.mkdir(parents=True, exist_ok=True)
    for item in ("input.json", "criteria.json", "status.json", "out"):
        if (old / item).exists():
            shutil.move(str(old / item), str(new / item))


def board_ids(d: Path) -> List[str]:
    migrate_legacy(d)
    root = boards_dir(d)
    return sorted(p.parent.name for p in root.glob("*/sld-input.json")) if root.is_dir() else []


def new_id(d: Path, name: str) -> str:
    base, ids, n = slug(name) or "tablero", set(board_ids(d)), 1
    bid = base
    while bid in ids:
        n += 1
        bid = f"{base}-{n}"
    return bid


def load_input(d: Path, bid: str):
    return read_json(input_file(d, bid), None)


def save_input(d: Path, bid: str, data: dict) -> None:
    write_json(input_file(d, bid), {"schema_version": "1.0", **data})


def load_status(d: Path, bid: str) -> dict:
    return read_json(work_dir(d, bid) / "status.json", {"state": "idle", "outputs": [], "log": []})


def save_status(d: Path, bid: str, status: dict) -> None:
    write_json(work_dir(d, bid) / "status.json", status)


def delete_board(d: Path, bid: str) -> None:
    """Removes the board with the files it published (diagrams and calculation); the other boards are not touched."""
    for rel in load_status(d, bid).get("outputs", []):
        (pkg(d) / rel).unlink(missing_ok=True)
    shutil.rmtree(input_file(d, bid).parent, ignore_errors=True)
    shutil.rmtree(work_dir(d, bid), ignore_errors=True)


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
    mine = [f for f in sorted(out.iterdir()) if f.name.startswith(prefixes) and f.suffix.lower() in (".svg", ".dxf", ".pdf", ".json", ".md")]
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
        sub = {".svg": "drawings/svg", ".dxf": "drawings/dxf", ".pdf": "drawings/pdf", ".json": "calc", ".md": "docs"}[f.suffix.lower()]
        if f.suffix.lower() == ".pdf" and f.stem.endswith(("_MC", "_SP")):
            sub = "docs"                                                   # memo and summary: documents, not drawings
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
