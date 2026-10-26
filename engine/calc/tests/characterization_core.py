"""Characterization of the calculation primitives: ampacity over installation methods, the feeder report (MC and SP) and the protection checks.

Golden file: golden/core.json (what the code produced when the refactoring started). `python engine/calc/tests/characterization_core.py --write` recreates it.
"""
import itertools
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src"))

from epc_calc import aea_ampacity as AMP   # noqa: E402
from epc_calc import aea_feeder_report as AFR   # noqa: E402
from epc_calc import aea_pipeline as P   # noqa: E402
from epc_calc import aea_protection as PR   # noqa: E402

GOLDEN = HERE / "golden" / "core.json"
SECTIONS = (1.5, 2.5, 6, 16, 35, 70, 120, 240, 300)


def ampacity():
    out = {}
    for method, ins, mat, phases, agrup, t_amb in itertools.product(AMP.METODOS, AMP.AISLACIONES, AMP.MATERIALES, (1, 3), (1, 2, 3, 4, 8), (40.0, 55.0)):
        row = {"AISLACION": ins, "MATERIAL": mat, "METODO": method, "AGRUP_CIRCUITOS": agrup, "TEMP_AMBIENTE_C": t_amb, "TEMP_SUELO_C": 30.0, "RESIST_TERMICA_KMW": 1.5}
        p = AMP.parametros(row)
        cell = {}
        for s in SECTIONS:
            key = f"{s:g}"
            if not AMP.seccion_valida(p, s):
                cell[key] = "invalid"
                continue
            try:
                cell[key] = round(AMP.iz(p, s, phases), 4)
            except ValueError as e:
                cell[key] = f"error: {e}"
        out[f"{method}|{ins}|{mat}|{phases}f|g{agrup}|{t_amb:g}C"] = {"factors": {k: round(v, 6) for k, v in AMP.factores(p, phases == 3).items()}, "iz": cell,
                                                                       "r90": round(AMP.resistencia_ohm_km(70, mat, AMP.temp_conductor(p)), 6) if mat == "cu" or 70 in AMP.R20_AL_OHM_KM else None}
    return out


BOARD = {"TENSION_V": 380, "ICC_KA": 36, "FP_DEFAULT": 0.85, "SISTEMA": "TN-S"}
FEEDERS = {
    "amps_3f": {"TAG": "C-01", "DESCRIPCION": "ALIMENTADOR TD-PB", "CARGA": 250, "UNIDAD_CARGA": "A", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 40, "CABLE_TIPO": "tetra_sep"},
    "kw_3f": {"TAG": "C-02", "DESCRIPCION": "ALIMENTADOR PLANTA", "CARGA": 80, "UNIDAD_CARGA": "kW", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 90, "FP": 0.9},
    "kva_1f": {"TAG": "C-03", "DESCRIPCION": "ALIMENTADOR 1F", "CARGA": 12, "UNIDAD_CARGA": "kVA", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "1F", "LONGITUD_m": 25},
    "hp_motor": {"TAG": "C-04", "DESCRIPCION": "ALIMENTADOR MOTOR", "CARGA": 50, "UNIDAD_CARGA": "HP", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 60, "RENDIMIENTO": 0.92},
    "al_xlpe": {"TAG": "C-05", "DESCRIPCION": "ALIMENTADOR AL", "CARGA": 400, "UNIDAD_CARGA": "A", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 150, "MATERIAL": "al", "AISLACION": "xlpe"},
    "long_fail": {"TAG": "C-06", "DESCRIPCION": "ALIMENTADOR LARGO", "CARGA": 300, "UNIDAD_CARGA": "A", "KIND": "mccb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 900},
}


def feeder_reports():
    out = {}
    for name, row in FEEDERS.items():
        tmp = Path(tempfile.mkdtemp())
        try:
            circuits = [dict(row), {"TAG": "X-99", "DESCRIPCION": "OTRO", "CARGA": 5, "UNIDAD_CARGA": "kW", "KIND": "mcb", "TOPOLOGY": "single", "FASE": "3F", "LONGITUD_m": 10}]
            data, warnings = P.calculate(BOARD, circuits)
            try:
                paths = AFR.generar_documentos(str(tmp / "PROJ"), BOARD, circuits, data)
            except ValueError as e:                         # the report does not apply the pipeline's XLPE -> B2 rule: a known divergence, pinned as it is
                out[name] = {"warnings": warnings, "error": str(e)}
                continue
            out[name] = {"warnings": warnings, "files": {Path(p).name: Path(p).read_text(encoding="utf-8") for p in paths}}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return out


def protection():
    out = {}
    for in_a, kind in itertools.product((6, 16, 32, 63, 100, 250, 630), ("mcb", "mccb", "fusible_gg")):
        out[f"i2|{kind}|{in_a}"] = [round(PR.i2_convencional(in_a, kind), 6), round(PR.in_max_por_iz(in_a * 1.2, kind), 6)]
    for zs, ia in itertools.product((0.2, 0.8, 2.5, 8.0), (30, 160, 500, 3000)):
        out[f"tn|{zs}|{ia}"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in PR.verifica_tn(zs, ia).items()}
    for ra, ia in itertools.product((5.0, 40.0, 200.0, 1500.0), (0.03, 0.3, 1.0)):
        out[f"tt|{ra}|{ia}"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in PR.verifica_tt(ra, ia).items()}
        out[f"tt-if|{ra}|{ia}"] = round(PR.corriente_falla_tt(230.0, ra, 2.0), 6)
    for zs, ia, neutral in itertools.product((0.3, 1.2), (160, 800), (False, True)):
        out[f"it|{zs}|{ia}|{neutral}"] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in PR.verifica_it_segunda_falla(zs, ia, neutro_distribuido=neutral).items()}
    return out


def all_results():
    return {"ampacity": ampacity(), "feeder_reports": feeder_reports(), "protection": protection()}


def main(argv=None) -> int:
    r = all_results()
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(r, indent=0, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print(f"golden written: {len(r['ampacity'])} ampacity rows, {len(r['feeder_reports'])} feeder reports, {len(r['protection'])} protection values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
