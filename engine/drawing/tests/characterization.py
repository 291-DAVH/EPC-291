"""Characterization of the drawings: the single-line and multi-line diagrams, their tables, calculation files and memo, produced end to end by `board_design.design`
for boards that exercise every protection chain. What is pinned is the content of every file once what changes on every run (dates, GUIDs, the tool's time stamp,
line endings) is normalized away: a hash of the normalized text (of its lines as a set, for DXF) plus a structural summary that says where a difference is.

Golden file: golden/drawings.json (what the code produced when the refactoring started). `python engine/drawing/tests/characterization.py --write` recreates it.
PDFs are not compared byte by byte (fonts and the plotting library vary between machines): only that they exist and how many pages they have.
"""
import collections
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parents[1]
sys.path[:0] = [str(ENGINE / a / "src") for a in ("drawing", "sld", "mld", "symbols", "titleblock", "calc")]

from epc_drawing import board_design as B   # noqa: E402

GOLDEN = HERE / "golden" / "drawings.json"
TB = {"company": "ACME SA", "company_cuit": "30-1-1", "client": "CLIENTE SA", "client_cuit": "30-2-2", "drawn_by": "D. Proyecta", "checked_by": "V. Verifica", "approved_by": "A. Valida",
      "description": "Planta de prueba", "location": "Mendoza", "scale": "1:50", "revision": "A", "status": "Emitido"}


def board(name, icc=25):
    return {"name": name, "voltage_v": 380, "system": "TN-S", "icc_ka": icc, "fp_default": 0.85, "frequency_hz": 50, "project": "PRJ-1", "feeder_length_m": 20}


def circuit(tag, description, load=None, unit="kW", parent="", topology="single", phase="3F", length=20, kind="auto", **extra):
    return {"tag": tag, "description": description, "load": load, "unit": unit, "destination": "", "parent_tag": parent, "topology": topology, "phase": phase, "length_m": length,
            "fp": None, "efficiency": None, "kind": kind, "notes": "", "cable_type": "tetra_sep", **extra}


SMALL = {"board": board("TGBT-01"), "titleblock": TB, "circuits": [
    circuit("C-01", "ALIMENTADOR", 100, "A", length=60, kind="mccb"), circuit("M-01", "BOMBA", 15, topology="dol_ol", length=80),
    circuit("G-01", "RCCB", None, "A", kind="rccb", length=0), circuit("G-01-A", "Tomas", 2.2, parent="G-01", phase="1F", length=15, kind="mcb")]}

TOPOLOGIES = ("dol", "dol_ol", "star_delta", "softstarter", "vfd", "dol_rcd")
BIG = {"board": board("TGBT-02", icc=36), "titleblock": TB, "circuits": (
    [circuit(f"M-{i + 1:02d}", f"MOTOR {i + 1}", 7.5 + 3 * i, topology=t, length=30 + 10 * i) for i, t in enumerate(TOPOLOGIES)]
    + [circuit("A-01", "ALIMENTADOR TS", 160, "A", length=50, kind="mccb"), circuit("A-02", "ALIMENTADOR MOTORIZADO", 250, "A", length=40, kind="mccb_motorized"),
       circuit("R-01", "RCBO OFICINA", 3, phase="1F", length=25, kind="rcbo"), circuit("L-01", "ILUMINACION NAVE", 4.2, phase="1F", length=70, kind="mcb"),
       circuit("U-01", "UPS SERVIDORES", 20, "kVA", length=12, notes="UPS"), circuit("G-02", "RCCB GRUPO", None, "A", kind="rccb", length=0)]
    + [circuit(f"G-02-{c}", f"Tomas {c}", 1.5 + i * 0.4, parent="G-02", phase="1F", length=15 + 3 * i, kind="mcb") for i, c in enumerate("ABCD")]
    + [circuit(f"X-{i:02d}", f"CARGA VARIA {i}", 1 + i, length=10 + 2 * i) for i in range(1, 9)])}

CASES = {"small_sld_mld": (SMALL, None, 18, ("sld", "mld")), "big_paginated_sld_mld": (BIG, None, 6, ("sld", "mld")), "big_tight_criteria_sld": (BIG, {"vd_sectional_pct": 1, "vd_motors_pct": 3}, 8, ("sld",))}

JULIAN = re.compile(r"^\d{7}\.\d+$")
GUID = re.compile(r"^\{[0-9A-Fa-f-]{36}\}$")
TODAY = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")        # the title block prints the day the drawing was made
STAMP = re.compile(r"@ \d{4}-\d{2}-\d{2}T[\d:.]+\+\d\d:\d\d")
SVG_HASH = re.compile(r'"svg_sha256": "[0-9a-f]{64}"')   # the index of the delivery package holds the hash of each raw SVG, which carries the day it was made; the SVGs are pinned on their own


def normalize(name, raw):
    text = TODAY.sub("DD/MM/YYYY", raw.decode("utf-8", errors="replace").replace("\r\n", "\n"))
    if name.endswith("_entregable.json"):
        text = SVG_HASH.sub('"svg_sha256": "HASH"', text)
    if name.endswith(".dxf"):
        text = "\n".join("JULIAN" if JULIAN.match(ln) else "{GUID}" if GUID.match(ln) else STAMP.sub("@ STAMP", ln) for ln in text.split("\n"))
    return text


def summary(name, raw):
    if name.endswith(".pdf"):
        return {"pdf_pages": len(re.findall(rb"/Type\s*/Page\b", raw)), "starts_with_pdf": raw.startswith(b"%PDF")}
    text = normalize(name, raw)
    out = {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "lines": text.count("\n")}
    if name.endswith(".svg"):
        out["elements"] = dict(sorted(collections.Counter(re.findall(r"<([a-zA-Z]+)[ >/]", text)).items()))
    elif name.endswith(".dxf"):
        lines = text.split("\n")
        out["sha256"] = hashlib.sha256(("\n").join(sorted(lines)).encode("utf-8")).hexdigest()           # the order of two table objects changes between runs: the set of lines is what is pinned
        out["entities"] = dict(sorted(collections.Counter(lines[i + 1].strip() for i in range(0, len(lines) - 1, 2) if lines[i].strip() == "0").items()))
    return out


def run(name):
    data, criteria, maxl, diagrams = CASES[name]
    work = Path(tempfile.mkdtemp(prefix="drawchar_"))
    try:
        result = B.design(json.loads(json.dumps(data)), work, "T1", criteria, None, maxl, diagrams)
        files = {p.name: summary(p.name, p.read_bytes()) for p in sorted((work / "out").iterdir()) if p.is_file()}
        return {"ok": result["ok"], "circuits": result["circuits"], "non_compliant": result["non_compliant"], "files": files}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None) -> int:
    results = {name: run(name) for name in CASES}
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(results, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("golden written:", {k: len(v["files"]) for k, v in results.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
