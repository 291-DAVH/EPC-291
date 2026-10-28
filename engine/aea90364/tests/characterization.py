"""Characterization of the design calculation: a fixed grid of circuits, norm criteria and installation methods whose results are pinned in golden/pipeline.json.

The golden file is what the code produced when the refactoring started. Tests compare against it; they never rewrite it. If the code changes a result the test
fails and the difference has to be understood (a behaviour change is not a refactoring). `python engine/aea90364/tests/characterization.py --write` recreates the
golden file, and is only for the moment the baseline is taken or when a change of behaviour is decided on purpose.
"""
import itertools
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))

from epc_aea90364 import aea_pipeline as P  # noqa: E402

GOLDEN = HERE / "golden" / "pipeline.json"
BOARD = {"TENSION_V": 380, "ICC_KA": 25, "FP_DEFAULT": 0.85}

CRITERIA = {
    "default": None,
    "tight": {"vd_sectional_pct": 1, "vd_lighting_sockets_pct": 1.5, "vd_motors_pct": 2.5, "min_section_lighting_mm2": 2.5, "min_section_sockets_mm2": 4},
    "loose": {"vd_sectional_pct": 3, "vd_lighting_sockets_pct": 5, "vd_motors_pct": 5, "conductor_material": "aluminio", "insulation": "XLPE"},
    "pvc_cu": {"conductor_material": "cobre", "insulation": "PVC", "rcd_sensitivity_ma": 300},
    "hot": {"insulation": "XLPE", "ambient_temp_c": 50, "soil_temp_c": 30, "soil_resistivity_kmw": 2.0},
}

KINDS = {                      # name -> circuit row (a load of each kind the pipeline tells apart)
    "feeder_A": {"DESCRIPCION": "ALIMENTADOR TS", "CARGA": 120, "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 60, "KIND": "mccb"},
    "feeder_kw": {"DESCRIPCION": "ALIMENTADOR", "CARGA": 90, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 120, "FP": 0.9, "KIND": "auto"},
    "motor_dol": {"DESCRIPCION": "BOMBA", "CARGA": 7.5, "UNIDAD_CARGA": "kW", "TOPOLOGY": "dol", "FASE": "3F", "LONGITUD_m": 45, "FP": 0.85, "RENDIMIENTO": 0.9, "KIND": "auto"},
    "motor_sd": {"DESCRIPCION": "COMPRESOR", "CARGA": 30, "UNIDAD_CARGA": "kW", "TOPOLOGY": "star_delta", "FASE": "3F", "LONGITUD_m": 80, "KIND": "auto"},
    "motor_vfd": {"DESCRIPCION": "VENTILADOR", "CARGA": 15, "UNIDAD_CARGA": "HP", "TOPOLOGY": "vfd", "FASE": "3F", "LONGITUD_m": 25, "KIND": "auto"},
    "lighting": {"DESCRIPCION": "ILUMINACION NAVE", "CARGA": 4.2, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 70, "FP": 0.9, "KIND": "mcb"},
    "sockets": {"DESCRIPCION": "TOMAS OFICINA", "CARGA": 2.2, "UNIDAD_CARGA": "kW", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 35, "FP": 0.9, "KIND": "mcb"},
    "ups": {"DESCRIPCION": "UPS", "CARGA": 20, "UNIDAD_CARGA": "kVA", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 12, "FP": 0.9, "KIND": "auto", "NOTAS": "UPS"},
}
METHODS = ("B1", "B2", "C", "E", "F", "G", "D1", "D2")
ROUTES = {
    "tray_buried_tray": [{"kind": "tray_perforated", "length_m": 20}, {"kind": "buried_direct", "length_m": 40, "soil_c": 30, "rho_kmw": 2.0}, {"kind": "tray_perforated", "length_m": 30}],
    "duct_crossing": [{"kind": "buried_duct", "length_m": 60, "circuits": 3}, {"kind": "road_crossing", "length_m": 8, "depth_m": 1.0}, {"kind": "conduit_air", "length_m": 10}],
}


def circuit(tag, base, **extra):
    return {"TAG": tag, **base, **extra}


def cases():
    """Every case is {"id", "criteria", "circuits"}: the grid of kinds x criteria, the methods, the routes and a board with groups."""
    out = []
    for (cname, crit), (kname, base) in itertools.product(CRITERIA.items(), KINDS.items()):
        out.append({"id": f"kind:{kname}:{cname}", "criteria": crit, "circuits": [circuit("C-01", base)]})
    for m, ais, mat in itertools.product(METHODS, ("pvc", "xlpe"), ("cu", "al")):
        out.append({"id": f"method:{m}:{ais}:{mat}", "criteria": None, "circuits": [circuit("C-01", KINDS["feeder_A"], METODO=m, AISLACION=ais, MATERIAL=mat, AGRUP_CIRCUITOS=2)]})
    for rname, route in ROUTES.items():
        for crit in ("default", "hot"):
            out.append({"id": f"route:{rname}:{crit}", "criteria": CRITERIA[crit], "circuits": [circuit("C-01", KINDS["feeder_A"], RUTA=route, CARGA=250)]})
    out.append({"id": "board:groups", "criteria": None, "circuits": [
        circuit("TG", KINDS["feeder_A"]), circuit("G-02", {"DESCRIPCION": "RCCB GRUPO TOMAS", "UNIDAD_CARGA": "A", "TOPOLOGY": "single", "FASE": "3F", "KIND": "rccb"}),
        circuit("G-02-A", KINDS["sockets"], PARENT_TAG="G-02"), circuit("G-02-B", {**KINDS["sockets"], "CARGA": 1.8, "LONGITUD_m": 20}, PARENT_TAG="G-02"),
        circuit("M-01", KINDS["motor_dol"]), circuit("L-01", KINDS["lighting"]), circuit("C-02", KINDS["ups"])]})
    out.append({"id": "board:sub", "criteria": None, "circuits": [
        circuit("SUB", {**KINDS["feeder_A"], "CARGA": None, "UNIDAD_CARGA": "A", "LONGITUD_m": 30}),
        circuit("SUB-A", KINDS["motor_vfd"], PARENT_TAG="SUB"), circuit("SUB-B", KINDS["motor_sd"], PARENT_TAG="SUB")]})
    return out


def _round(v):
    if isinstance(v, float):
        return round(v, 6)
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_round(x) for x in v]
    return v


def run(case):
    detail = {}
    try:
        data, warnings = P.calculate(BOARD, [dict(c) for c in case["circuits"]], criterios=case["criteria"], detalle=detail)
    except ValueError as e:                                       # a combination with no table is part of the behaviour
        return {"error": str(e)}
    return _round({"datos": data, "detalle": detail, "avisos": warnings})


def main(argv=None) -> int:
    results = {c["id"]: run(c) for c in cases()}
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(results, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(f"golden written: {len(results)} cases, {sum(1 for r in results.values() if 'error' in r)} with an error as result")
    else:
        print(f"{len(results)} cases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
