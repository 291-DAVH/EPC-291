"""Characterization of the board memo and summary (epc_aea90364.board_memo): data, Markdown and the document structure for boards that exercise every branch.

Golden file: golden/memo.json (what the code produced when the refactoring started). `python engine/aea90364/tests/characterization_memo.py --write` recreates it.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))

from epc_aea90364 import aea_pipeline as P   # noqa: E402
from epc_aea90364 import board_memo as BM    # noqa: E402

GOLDEN = HERE / "golden" / "memo.json"
FORM_TO_ROW = {"tag": "TAG", "description": "DESCRIPCION", "load": "CARGA", "unit": "UNIDAD_CARGA", "parent_tag": "PARENT_TAG", "topology": "TOPOLOGY", "phase": "FASE",
               "length_m": "LONGITUD_m", "fp": "FP", "efficiency": "RENDIMIENTO", "kind": "KIND", "notes": "NOTAS", "cable_type": "CABLE_TIPO", "route": "RUTA"}


def c(tag, description, load=None, unit="kW", parent="", topology="single", phase="3F", length=20, kind="auto", fp=None, **extra):
    return {"tag": tag, "description": description, "load": load, "unit": unit, "parent_tag": parent, "topology": topology, "phase": phase, "length_m": length, "kind": kind,
            "fp": fp, "efficiency": None, "notes": "", "cable_type": "tetra_sep", **extra}


def board(name, system="TN-S", icc=25.0, voltage=380.0, feeder=20.0):
    return {"name": name, "voltage_v": voltage, "system": system, "icc_ka": icc, "fp_default": 0.85, "frequency_hz": 50.0, "project": "PRJ-1", "feeder_length_m": feeder}


CASES = {
    "groups_tns": {"board": board("TGBT-01"), "criteria": None, "validated": True, "upstream": None, "circuits": [
        c("C-01", "ALIMENTADOR TS-1", 63, "A", length=30, kind="mccb"), c("M-01", "EXTRACTOR", 7.5, topology="dol", length=25, fp=0.85),
        c("G-01", "RCCB TOMAS", None, "A", kind="rccb"), c("G-01-A", "Tomas 1", 2.2, parent="G-01", phase="1F", length=15, kind="mcb"),
        c("G-01-B", "Tomas 2", 1.8, parent="G-01", phase="1F", length=22, kind="mcb"), c("L-01", "ILUMINACION", 1.5, phase="1F", length=35, kind="mcb")]},
    "it_system_unvalidated": {"board": board("TS-IT", system="IT", icc=10.0), "criteria": {"insulation": "XLPE", "rcd_sensitivity_ma": 300}, "validated": False, "upstream": None, "circuits": [
        c("C-VFD", "VENTILADOR VFD", 15, "HP", topology="vfd", length=40), c("C-RCD", "BOMBA CON DIFERENCIAL", 5.5, topology="dol_rcd", length=30)]},
    "with_upstream": {"board": board("TS-2", icc=15.0, feeder=45.0), "criteria": None, "validated": True,
                      "upstream": {"board": "TGBT-01", "tag": "C-01", "length_m": 60.0, "In": 160, "S": 70, "dU": 0.8, "disp": "MCCB (160 A)", "curva": "MCCB",
                                   "ruta": [{"n": 1, "kind": "tray_perforated", "label": "Bandeja", "length_m": 40.0, "metodo": "E", "circuits": 1, "t_amb": 40.0, "t_suelo": 25.0, "rho_kmw": 1.0,
                                             "depth_m": None, "iz_a": 215.0, "f_temp": 1.0, "f_agrup": 1.0, "f_suelo": 1.0, "limitante": True}, {"n": 2, "kind": "buried_duct", "label": "", "length_m": 20.0,
                                             "metodo": "D1", "circuits": 1, "t_amb": 40.0, "t_suelo": 25.0, "rho_kmw": 1.0, "depth_m": 0.7, "iz_a": 230.0, "f_temp": 1.0, "f_agrup": 1.0, "f_suelo": 1.0, "limitante": False}],
                                   "ruta_limitante": 1},
                      "circuits": [c("S-01", "ALIMENTADOR TABLERO", 100, "A", length=20, kind="mccb"), c("S-02", "MOTOR", 22, topology="star_delta", length=50),
                                   c("S-03", "TOMAS", 3, phase="1F", length=30, kind="mcb")]},
    "route_and_failures": {"board": board("TS-3", icc=36.0), "criteria": {"vd_sectional_pct": 1}, "validated": True, "upstream": None, "circuits": [
        c("F-01", "ALIMENTADOR LARGO", 250, "A", length=999, kind="mccb", route=[{"kind": "tray_perforated", "length_m": 20}, {"kind": "buried_direct", "length_m": 60, "soil_c": 30, "rho_kmw": 2.5},
                                                                                 {"kind": "road_crossing", "length_m": 8, "depth_m": 1.0, "circuits": 3}, {"kind": "tray_perforated", "length_m": 30}]),
        c("F-02", "TOMAS SIN DIFERENCIAL", 2.2, phase="1F", length=40, kind="mcb")]},
}


def run(name):
    spec = CASES[name]
    circuits = spec["circuits"]
    rows = [{FORM_TO_ROW[k]: v for k, v in c_.items() if k in FORM_TO_ROW and v not in (None, "")} for c_ in circuits]
    for row, c_ in zip(rows, circuits):
        if c_.get("route"):
            row["LONGITUD_m"] = round(sum(s["length_m"] for s in c_["route"]), 3)
    b = spec["board"]
    tablero = {"TENSION_V": b["voltage_v"], "ICC_KA": b["icc_ka"], "FP_DEFAULT": b["fp_default"]}
    detail = {}
    data, warnings = P.calculate(tablero, rows, criterios=spec["criteria"], detalle=detail)
    limits, _, material, insulation, sens = P.resolver_criterios(spec["criteria"])
    memo = BM.build(b, circuits, data, detail, {"seccional": limits["seccional"], "terminal": limits["iluminacion"], "motor": limits["motor"]},
                    {"material": material, "aislacion": insulation}, sens, upstream=spec["upstream"], validated=spec["validated"])
    return json.loads(json.dumps({"memo": memo, "mc_md": BM.memoria_md(memo), "sp_md": BM.sintesis_md(memo), "mc_doc": BM.memoria_doc(memo), "sp_doc": BM.sintesis_doc(memo)}, ensure_ascii=False))


def main(argv=None) -> int:
    results = {name: run(name) for name in CASES}
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(results, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(f"golden written: {len(results)} boards")
    return 0


if __name__ == "__main__":
    sys.exit(main())
