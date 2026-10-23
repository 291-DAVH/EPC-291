"""Files of the SLD feature inside workspace/02-engineering/electrical/<package>/ (src = input, build = scratch, drawings/calc = outputs)."""
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from epc.core.config import settings
from epc.core.fsutil import read_json, write_json

PACKAGE = "PQ-01"
DISCIPLINE = "electrical"

BOARD_ROWS = [("NOMBRE", "name"), ("TENSION_V", "voltage_v"), ("SISTEMA", "system"), ("ICC_KA", "icc_ka"), ("FP_DEFAULT", "fp_default"),
              ("FRECUENCIA_HZ", "frequency_hz"), ("PROYECTO", "project"), ("LONG_ACOMETIDA_m", "feeder_length_m")]
CIRCUIT_COLS = [("TAG", "tag"), ("DESCRIPCION", "description"), ("CARGA", "load"), ("UNIDAD_CARGA", "unit"), ("DESTINO", "destination"), ("PARENT_TAG", "parent_tag"),
                ("TOPOLOGY", "topology"), ("FASE", "phase"), ("LONGITUD_m", "length_m"), ("FP", "fp"), ("RENDIMIENTO", "efficiency"), ("KIND", "kind"),
                ("NOTAS", "notes"), ("CABLE_TIPO", "cable_type")]
TITLEBLOCK_COLS = {"company": "Empresa: razón social", "company_cuit": "Empresa: CUIT", "client": "Cliente: razón social", "client_cuit": "Cliente: CUIT",
                   "drawn_by": "Proyectado por", "checked_by": "Verificado por", "approved_by": "Validado por", "description": "Descripción",
                   "location": "Ubicación", "scale": "Escala", "revision": "Revisión", "status": "Estado"}


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


def write_excel(path: Path, data: dict) -> None:
    """The workbook the plugin reads: sheets TABLERO (CAMPO/VALOR) and CIRCUITOS (one row per circuit)."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "TABLERO"
    ws.append(["DATOS DEL TABLERO"])
    ws.append(["CAMPO", "VALOR"])
    for col, key in BOARD_ROWS:
        ws.append([col, data["board"].get(key)])
    cs = wb.create_sheet("CIRCUITOS")
    cs.append(["CIRCUITOS"])
    cs.append([c for c, _ in CIRCUIT_COLS])
    for row in data["circuits"]:
        cs.append([None if row.get(k) in (None, "") else row.get(k) for _, k in CIRCUIT_COLS])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def write_titleblock(folder: Path, tb: dict) -> None:
    """Copy the plugin's titleblock workbook and fill the common data of its first row (company, client, people...). No logos are copied."""
    import openpyxl
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "input-titleblocks.xlsx"
    shutil.copy(settings.engine / "drawing" / "examples" / "sld" / "titleblock" / "input-titleblocks.xlsx", target)
    wb = openpyxl.load_workbook(target)
    ws = wb["Láminas"]
    hdr = {c.value: c.column for c in ws[1]}
    today = dt.date.today()
    for key, col in TITLEBLOCK_COLS.items():
        ws.cell(2, hdr[col]).value = tb.get(key) or None
    for col in ("Proyectado: fecha", "Verificado: fecha", "Validado: fecha"):
        ws.cell(2, hdr[col]).value = dt.datetime(today.year, today.month, today.day)
    wb.save(target)


def run_generator(xlsx: Path, out: Path, name: str, rotulo_dir: Path):
    out.mkdir(parents=True, exist_ok=True)
    import os
    env = dict(os.environ, SLD_ROTULO_DIR=str(rotulo_dir))
    return subprocess.run([sys.executable, "-m", "epc_drawing.sld.sld_paginate", "default", str(xlsx), str(out), name, "default", "default"],
                          env=env, capture_output=True, text=True, timeout=600)


def render_pdfs(out: Path, name: str) -> List[str]:
    """PDF of every DXF produced (the deliverable rendering of the drawing), through the engine's exporter. Returns warnings, never raises."""
    warnings: List[str] = []
    for dxf in sorted(out.glob(f"{name}*.dxf")):
        res = subprocess.run([sys.executable, "-m", "epc_drawing.export.pdf", str(dxf), str(dxf.with_suffix(".pdf"))], capture_output=True, text=True, timeout=300)
        if res.returncode != 0:
            warnings.append(f"AVISO no se pudo generar el PDF de {dxf.name}: {(res.stderr or res.stdout).strip()[-200:]}")
    return warnings


def publish(d: Path, out: Path, name: str, previous: List[str]) -> List[str]:
    """Copy outputs into the engineering folders (SVG -> drawings/svg, DXF -> drawings/dxf, calculation JSON -> calc) and drop the previous run's files."""
    base = pkg(d)
    for rel in previous:
        (base / rel).unlink(missing_ok=True)
    placed: List[str] = []
    for f in sorted(out.glob(f"{name}*")):
        sub = {".svg": "drawings/svg", ".dxf": "drawings/dxf", ".pdf": "drawings/pdf", ".json": "calc"}.get(f.suffix.lower())
        if not sub:
            continue
        dest = base / sub / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(f, dest)
        placed.append(f"{sub}/{f.name}")
    return placed


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
