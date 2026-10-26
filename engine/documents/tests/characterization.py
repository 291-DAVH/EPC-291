"""Characterization of the documents package: the CCPM schedule (calculation, tracking and Markdown), the specification and project verifiers, and the canvas parser
and HTML. The inputs are the package's own examples and the sample projects that the verifier tests build; the outputs are pinned in golden/documents.json.
`python engine/documents/tests/characterization.py --write` recreates the golden file (only when the baseline is taken or a change of behaviour is decided on purpose).
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "src")]

from epc_documents import canvas_exporter as CE   # noqa: E402
from epc_documents import ccpm   # noqa: E402
from epc_documents import document_verifier as DV   # noqa: E402
from epc_documents import specification_verifier as SV   # noqa: E402
import test_document_verifier as TD   # noqa: E402
import test_specification_verifier as TS   # noqa: E402

GOLDEN = HERE / "golden" / "documents.json"
PKG = Path(ccpm.__file__).resolve().parent


def digest(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(text.replace("\r\n", "\n").encode("utf-8")).hexdigest()


def clean(obj, root):
    """The temporary folder of a run is replaced by <ROOT> so that the result does not depend on where it ran."""
    return json.loads(json.dumps(obj, ensure_ascii=False, default=str).replace(root, "<ROOT>").replace(root.replace("\\", "\\\\"), "<ROOT>"))


# ---------------------------------------------------------------- CCPM
def ccpm_cases():
    out = {}
    for name in ("example_ccpm.json", "example_ccpm_packages.json"):
        data = json.loads((PKG / name).read_text(encoding="utf-8"))
        for tag, kwargs in (("default", {}), ("from_date", {"desde": "2026-11-02"})):
            key = f"{name}:{tag}"
            try:
                res = ccpm.calcular_ccpm(json.loads(json.dumps(data)), **kwargs)
            except (ValueError, KeyError) as e:
                out[key] = {"error": str(e)}
                continue
            out[key] = {"result_sha": digest(res), "keys": sorted(res), "markdown_sha": digest(ccpm.generar_markdown(res)), "sections_sha": digest(ccpm.generar_md_secciones(res)),
                        "markdown_lines": ccpm.generar_markdown(res).count("\n"), "summary": {k: res[k] for k in sorted(res) if isinstance(res[k], (str, int, float, bool)) or res[k] is None}}
    base = json.loads((PKG / "example_ccpm.json").read_text(encoding="utf-8"))
    bad = {
        "no_tasks": {**base, "tareas": []}, "not_a_dict": [], "no_start": {k: v for k, v in base.items() if k not in ("inicio",)},
        "cycle": _with_cycle(base), "negative_duration": _with_task_change(base, "dur_segura", -3), "text_duration": _with_task_change(base, "dur_segura", "x"),
        "unknown_predecessor": _with_task_change(base, "predecesores", ["ZZZ"]),
    }
    out["invalid"] = {}
    for k, v in bad.items():
        try:
            ccpm.calcular_ccpm(json.loads(json.dumps(v)))
            out["invalid"][k] = "accepted"
        except Exception as e:                         # noqa: BLE001 - the type and the message are the behaviour
            out["invalid"][k] = f"{type(e).__name__}: {e}"
    out["tracking"] = {
        "avance_entregable": [attempt(ccpm.avance_entregable, h) for h in ([], ["generado"], ["generado", "revisado"], ["generado", "revisado", "auditado", "emitido"], ["zzz"])],
        "avance_global": [attempt(ccpm.avance_global, e) for e in (
            [], [{"id": "E1", "hitos": ["generado"], "aplica": True, "peso": 1}],
            [{"id": "E1", "hitos": ["generado", "revisado", "auditado", "emitido"], "aplica": True, "peso": 2}, {"id": "E2", "hitos": [], "aplica": True, "peso": 1},
             {"id": "E3", "hitos": [], "aplica": False, "peso": 5}])],
        "consumo_buffer": [attempt(ccpm.consumo_buffer, r, b) for r, b in ((0, 10), (3, 10), (10, 10), (15, 10), (-2, 10), (4, 0))],
        "estado_buffer": [attempt(ccpm.estado_buffer, a, c) for a, c in ((0, 0), (0.3, 0.1), (0.3, 0.4), (0.6, 0.5), (0.9, 0.95), (0.1, 0.8), (1, 1), (0.5, 1.2), (30, 10))],
    }
    return out


def attempt(fn, *args):
    """The value of a call, or the type and message of the error it raises: both are behaviour."""
    try:
        return fn(*args)
    except Exception as e:                                 # noqa: BLE001
        return f"{type(e).__name__}: {e}"


def _with_task_change(base, field, value):
    d = json.loads(json.dumps(base))
    tasks = d.get("tareas") or d.get("tasks") or []
    if tasks:
        tasks[0][field] = value
    return d


def _with_cycle(base):
    d = json.loads(json.dumps(base))
    tasks = d.get("tareas") or d.get("tasks") or []
    if len(tasks) >= 2:
        tasks[0]["predecesores"] = [tasks[1]["id"]]
        tasks[1]["predecesores"] = [tasks[0]["id"]]
    return d


# ---------------------------------------------------------------- specification verifier
def spec_cases():
    variants = {
        "clean": {}, "missing_05": {5: None}, "missing_last_three": {8: None, 9: None, 10: None},
        "no_question": {3: TS.capitulo(3, pregunta=False)}, "no_pending": {4: TS.capitulo(4, pendientes=False)}, "wrong_code": {2: TS.capitulo(2, codigo="ZZ99-G-PG-009")},
        "wrong_revision": {6: TS.capitulo(6, rev="00.9")}, "duplicated_text": {7: TS.capitulo(7, cuerpo=TS.CUERPOS[1])},
        "extra_chapter": {11: TS.capitulo(11)},
        "chapter_not_pg": {2: TS.capitulo(2, codigo="AB01-G-MD-001")}, "no_chapter_code": {2: TS.capitulo(2, codigo=""), 3: TS.capitulo(3, rev="")},
        "everything_wrong": {1: TS.capitulo(1, pregunta=False, pendientes=False, cuerpo="Costo total USD 5.000 y el Contratista deberá ver el capítulo 09."),
                             4: TS.capitulo(4, cuerpo="La norma IEC 60364 y la IRAM 2178 se reescriben aquí. El Contratista deberá cumplirlas."),
                             5: TS.capitulo(5, cuerpo="El Contratista deberá instalar y el instalador realizará el montaje. [DEFINIR] [VERIFICAR]"),
                             8: TS.capitulo(8, cuerpo="No aplica a este proyecto"), 9: TS.capitulo(9, cuerpo="x"), 6: TS.capitulo(6, extra="\ttabulado\n* viñeta\n# otro h1")},
    }
    out = {}
    for name, changes in variants.items():
        d = tempfile.mkdtemp(prefix="specchar_")
        try:
            TS.pliego(d, {k: v for k, v in changes.items() if k <= 10})
            if 11 in changes:
                TS.escribir(d, "11_Data_Sheet.md", changes[11])
            res = SV.verificar_pliego(d)
            out[name] = {"result": clean(res, d), "markdown": clean(SV.generar_markdown(res), d)}
        finally:
            shutil.rmtree(d, ignore_errors=True)
    for name, text in (("index_without_code", "# Índice y control\n\ntexto\n"), ("index_not_pg", TS.indice(codigo="AB01-G-MD-001")),
                       ("index_without_revision", "---\ncode: \"AB01-G-PG-001\"\n---\n\n# Índice y control\n"), ("index_table_form", TS.indice(yaml=False))):
        d = tempfile.mkdtemp(prefix="specchar_")
        try:
            TS.pliego(d)
            TS.escribir(d, SV.INDICE, text)
            res = SV.verificar_pliego(d)
            out[name] = {"result": clean(res, d), "markdown": clean(SV.generar_markdown(res), d)}
        finally:
            shutil.rmtree(d, ignore_errors=True)
    d = tempfile.mkdtemp(prefix="specchar_")
    try:
        TS.pliego(d)
        os.remove(os.path.join(d, SV.INDICE))
        TS.escribir(d, "notes.md", "# Notas\n")
        TS.escribir(d, "03_Normativa_Aplicable.md", TS.capitulo(3))
        res = SV.verificar_pliego(d)
        out["no_index_and_stray_files"] = {"result": clean(res, d), "markdown": clean(SV.generar_markdown(res), d)}
    finally:
        shutil.rmtree(d, ignore_errors=True)
    out["missing_folder"] = attempt(SV.verificar_pliego, os.path.join(tempfile.gettempdir(), "no_such_spec_folder_xyz"))
    return out


# ---------------------------------------------------------------- project verifier
CONTROL_ROWS = """# AB01-E-MC-001_Rev00.2.3 — Balance

| Campo | Valor |
|---|---|
| Código | AB01-E-MC-001 |
| Revisión | 00.2.3 |

## Control de revisiones

| Rev. | Fecha | Descripción |
|---|---|---|
| 00.0 | 2026-10-08 | Inicial |
| 00.1 | 2026-10-09 | Cambio sin cita |
| 00.2 | 2026-10-10 | Cambio rfc-002 |
| 00.2.1 | 2026-10-11 | Comentario sin identificador |
| 00.2.2.IB | 2026-10-12 | Avance de fase |
| 00.2.3 | 2026-10-13 | REV-003 |
"""

CHARTER_TECH = """| Campo | Valor |
|---|---|
| Proyecto | Planta Acme |
| Código de proyecto | AB01 |
| Versión de la línea base | 1.2 (borrador) |
| Fecha | 2026-10-20 |
| Estado | DRAFT |

# REGISTRO DEL PROYECTO

### 3.8 Riesgos

| ID | Descripción | Prob. | Impacto | Nivel |
|---|---|---|---|---|
| RIE-001 | Retraso | 4 | 5 | 20 |
| RIE-002 | Cambio | 2 | 3 | 7 |

## 4.1 Costo

Costo estimado a definir: [DEFINIR]

### 4.2 Hitos

| Hito | Fecha |
|---|---|
| Inicio | 2026-10-05 |
| Entrega | 2026-12-18 |

## 7. Paquetes

| N | Paquete | Depende de |
|---|---|---|
| 1 | PQ-1 Cálculo | — |
| 2 | PQ-2 Planos | PQ-1 |

Supuestos SUP-001 y ALD-001.
"""

CHARTER_EXEC = """# LIENZO EJECUTIVO

| Proyecto | Versión | Fecha | Estado |
|---|---|---|---|
| Planta Acme | 1.3 | 2026-10-21 | DRAFT |

### Riesgos

| ID | Prob. | Impacto | Nivel |
|---|---|---|---|
| RIE-001 | 4 | 5 | 20 |
| RIE-002 | 3 | 3 | 8 |
| RIE-003 | 1 | 1 | 2 |

### Desglose del trabajo

| N | Paquete | Depende de |
|---|---|---|
| 1 | PQ-2 Planos | PQ-1 |
| 2 | PQ-1 Cálculo | — |

### Hitos

Inicio 2026-10-05, entrega 2026-12-30.

### Presupuesto

Costo: 100 USD
"""


def _project(*files):
    """A project builder: the base project plus the given (path, text) files."""
    def build(d):
        TD.proyecto_base(d)
        for path, text in files:
            TD.escribir(d, path, text)
    return build


def _project_variants():
    doc = TD.doc
    lme_plus = TD.LME.format(rev1="00.2", rev2="00.2") + ("| ENT-004 | AB01-G-PG-001 | Pliego | Documentación | ID | PG | SÍ | ENGINEERING | 00.3 | — |\n"
                                                           "| ENT-005 | AB01-G-PG-002 | Otro pliego | Documentación | ID | PG | SÍ | ENGINEERING | 00.1 | — |\n"
                                                           "| ENT-006 | AB01-G-PG-003 | Tercer pliego | Documentación | ID | PG | NO | — | 00.1 | — |\n")
    return {
        "draft_file": _project(("02/AB01-E-MC-001_Rev00.1_draft-1.md", doc("AB01-E-MC-001", "00.1", "Balance"))),
        "rev_00_and_annexes": _project(("02/AB01-E-PL-001_Rev00.md", doc("AB01-E-PL-001", "00", "Plano")), ("02/AB01-E-MC-001_Rev00.2_annex_B.py", "print(1)\n"),
                                       ("02/AB01-E-MC-001_Rev00.1_annex_A.py", "print(1)\n")),
        "control_rows": _project(("02/AB01-E-MC-001_Rev00.2.3.md", CONTROL_ROWS)),
        "no_revision_row": _project(("02/AB01-E-PL-002_Rev00.1.md", "# Plano sin cabecera\n\ntexto\n")),
        "lme_with_specifications": _project(("90-management/deliverables.md", lme_plus), ("Technical_Specs/00_Index_and_Control.md", "---\ncode: \"AB01-G-PG-001\"\nrevision: \"00.2\"\n---\n# Índice\n")),
        "citations": _project(("02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", "Ver MD-001 Rev 00.1, AB01-E-MC-001 Rev 00, AB01-E-MC-001 Rev 01, ZZ-999 Rev 00.1, AB01-E-MC-001 Rev vigente.")),
                              ("02/AB02-E-MD-001_Rev00.1.md", doc("AB02-E-MD-001", "00.1", "Otra memoria", "Ver MD-001 Rev 00.1.")),
                              ("02/AB01-E-MC-001_Rev00.2.md", doc("AB01-E-MC-001", "00.2", "Balance", "Ver MD-007 Rev 00.1 y AB01-E-MD-001 Rev 00.3."))),
        "marks_and_ranges": _project(("02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", "[DEFINIR] [VERIFICAR] [PENDIENTE INF-001] [SUPUESTO S1] DEC-001 a DEC-004, RIE-001 – RIE-003, PAR-007."))),
        "pandoc_problems": _project(("02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", "## 1. Capítulo\n\n* viñeta\n- lista\ntexto\n- otra\n\nver el capítulo 3\n\n#### salto\n\n\ttab")),
                                    ("Technical_Specs/x.md", "# a\n\n* b\n"), ("CLAUDE.md", "# a\n\n* b\n")),
        "money": _project(("02/AB01-E-MD-001_Rev00.2.md", doc("AB01-E-MD-001", "00.2", "Memoria", "Costo total USD 1.000.\npresupuesto de 50.000 pesos aprox\n[ECON-AUTORIZADO DEC-001] USD 5\n[ECON-AUTORIZADO DEC-099] USD 7\n```\nUSD 9\n```")),
                          ("01-input/_INPUT_REGISTER.md", "# Registro\n\nPrecio $ 12.500 por unidad.\n"), ("01-input/minutes/MINUTES-1.md", "# Acta\n\nHonorarios 250.000 acordados.\n"),
                          ("01-input/other.md", "# Otro\n\nUSD 4\n")),
        "charter_pair": _project(("02_PROJECT/project-charter.md", CHARTER_TECH), ("02_PROJECT/project-charter-executive.md", CHARTER_EXEC)),
        "charter_pair_pdf_without_seal": _project(("02_PROJECT/project-charter.md", CHARTER_TECH), ("02_PROJECT/project-charter-executive.md", CHARTER_EXEC),
                                                  ("02_PROJECT/project-charter-executive.pdf", "%PDF-1.4 sin sello")),
        "charter_pair_pdf_other_seal": _project(("02_PROJECT/project-charter.md", CHARTER_TECH), ("02_PROJECT/project-charter-executive.md", CHARTER_EXEC.replace("DRAFT", "APROBADO", 1)),
                                                ("02_PROJECT/project-charter-executive.pdf", "%PDF-1.4 sha256:0123456789abcdef")),
        "charter_pair_pdf_matching_seal": lambda d: _charter_with_matching_pdf(d),
        "charter_guide_only": _project(("02_PROJECT/project-charter.md", CHARTER_TECH), ("02_PROJECT/project-charter-executive.md", "# GUÍA DEL ARCHIVO\n")),
    }


def _charter_with_matching_pdf(d):
    TD.proyecto_base(d)
    TD.escribir(d, "02_PROJECT/project-charter.md", CHARTER_TECH)
    path = TD.escribir(d, "02_PROJECT/project-charter-executive.md", CHARTER_EXEC)
    with open(path, encoding="utf-8") as f:
        seal = DV.sello_charter_md(f.read())
    TD.escribir(d, "02_PROJECT/project-charter-executive.pdf", f"%PDF-1.4 sha256:{seal}")


def project_cases():
    cases = {
        "clean": {"cuerpo1": "Ver `AB01-E-MD-001` Rev 00.2 y DEC-001, SUP-001, INF-001, rfc-001.", "cuerpo2": "Según AB01-E-MC-001 vigente. Ver DEC-001 a DEC-002."},
        "old_lme_revision": {"rev1": "00.1"}, "title_revision_differs": {"rev_titulo": "00.1"}, "table_revision_differs": {"rev_tabla": "00.3"},
        "stale_citation": {"cuerpo1": "Ver AB01-E-MD-001 Rev 00.1 para el detalle."}, "unknown_ids": {"cuerpo1": "Según DEC-099 y RIE-050 y rfc-077."},
    }
    out = {}
    for name, kw in cases.items():
        d = tempfile.mkdtemp(prefix="projchar_")
        try:
            TD.proyecto_base(d, **kw)
            res = DV.verificar_proyecto(d)
            out[name] = {"result": clean(res, d), "markdown": clean(DV.generar_markdown(res), d)}
        finally:
            shutil.rmtree(d, ignore_errors=True)
    for name, build in _project_variants().items():
        d = tempfile.mkdtemp(prefix="projchar_")
        try:
            build(d)
            res = DV.verificar_proyecto(d)
            out[name] = {"result": clean(res, d), "markdown": clean(DV.generar_markdown(res), d)}
        finally:
            shutil.rmtree(d, ignore_errors=True)
    out["missing_folder"] = attempt(DV.verificar_proyecto, os.path.join(tempfile.gettempdir(), "no_such_project_folder_xyz"))
    out["format_checks"] = {
        "pandoc": DV.comprobar_formato_pandoc("# Titulo\n\nTexto con `codigo` y **negrita**.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"),
        "pandoc_bad": DV.comprobar_formato_pandoc("Titulo\n=====\n\n* item\n\n| A | B |\n| 1 | 2 |\n"),
        "confidential": DV.comprobar_confidencialidad("Contrato n.º 123, cliente SECRETO SA, precio USD 10.000."),
    }
    return out


# ---------------------------------------------------------------- canvas
CANVAS = """# LIENZO DE PLANIFICACIÓN

| Proyecto | Versión | Fecha | Estado | Fase |
|---|---|---|---|---|
| Planta Acme | 1.2 | 2026-10-20 | DRAFT | Planificación |

### Objetivo de la fase
Definir el plan de trabajo.

### Entregables de la fase
- Memoria de cálculo
- Planos unifilares

### Hitos de planificación
| Hito | Fecha |
|---|---|
| Kick-off | 2026-10-05 |
| Entrega IFA | 2026-11-20 |

### Caja que no existe
texto
"""


def canvas_cases():
    parsed = CE.parsear(CANVAS, CE.CAJAS_planning)
    return {"parsed": parsed, "html_planning_sha": digest(CE.generar_html_planning(parsed, "sello", "planning_CANVAS.md")),
            "boxes": {"planning": list(CE.CAJAS_planning), "phase": list(CE.CAJAS_PHASE), "closure": list(CE.CAJAS_CLOSURE)}}


# ---------------------------------------------------------------- CCPM input matrix
TOP_VALUES = [None, "", "x", -1, 0, 1, 25, 1.5, True, [], {}, "2026-13-45", "2026-10-05", ["2026-10-06"], ["x"], "esfuerzo", "rss", "otro", 40, "mon", [0, 1, 2], [9]]
TOP_FIELDS = ["inicio", "feriados", "dias_laborables", "fecha_limite_contractual", "metodo_buffer", "hitos", "tareas", "horas_por_dia", "tipo_plazo", "plazo_horas",
              "factor_buffer", "base", "desconocida"]
TASK_VALUES = [None, "", "x", -1, 0, 2, 100, 1.5, True, [], ["T1"], ["ZZZ"], "2026-10-05", "2026-09-01", "hecha", "excluida", "bloqueada", "pendiente", "Hecha", "elaborar", "revisar", "L1", "PQ"]
TASK_FIELDS = ["id", "nombre", "recurso", "tipo_recurso", "dur_segura", "dur_segura_h", "dur_agresiva", "dur_agresiva_h", "predecesores", "fecha_no_antes_de", "inicio_real",
               "fin_real", "estado", "lote", "paquete", "fase_paquete", "entregable"]
HITO_VALUES = [None, "x", {"nombre": "H"}, {"nombre": "H", "fecha": "2026-10-20"}, {"fecha": "2026-10-20", "tarea": "ZZZ"}, {"fecha": "bad"}, {"fecha": "2026-10-20", "tarea": "T1"}]


def _set(i, **fields):
    def change(d):
        d["tareas"][i].update(fields)
    return change


def _drop(i, key):
    def change(d):
        d["tareas"][i].pop(key, None)
    return change


def _top(**fields):
    def change(d):
        d.update(fields)
    return change


def _isolated(d):
    for t in d["tareas"]:
        t["predecesores"] = []


def _with_date(d):
    import datetime
    return {"desde": datetime.date(2026, 10, 12)}


def _lots(d):
    for k, t in enumerate(d["tareas"]):
        t["lote"] = "L1" if k % 2 == 0 else "L2"
    return {"lote": "L1"}


def _milestone_on_done(d):
    d["tareas"][0]["estado"] = "hecha"
    d["tareas"][0]["fin_real"] = "2026-10-02"
    d["hitos"] = [{"nombre": "H", "fecha": "2026-10-20", "tarea": d["tareas"][0]["id"]}]


COMBOS = [
    _with_date, _lots, _isolated, _milestone_on_done,
    _top(plazo_horas=80), _top(plazo_horas=80, fecha_limite_contractual="2026-12-01"), _top(plazo_horas=80, fecha_limite_contractual=None),
    _top(plazo_horas=10, tipo_plazo="esfuerzo"), _top(plazo_horas=100000, tipo_plazo="esfuerzo"), _top(plazo_horas=200, tipo_plazo="esfuerzo", horas_por_dia=6),
    _top(horas_por_dia=6, plazo_horas=40), _top(metodo_buffer="rss"), _top(factor_buffer=0.3), _top(base={"fin_cadena": "2026-12-01"}), _top(base=[]),
    _drop(0, "dur_segura"), _set(0, dur_segura=None, dur_segura_h=16), _set(0, dur_segura_h=16, dur_agresiva_h=8), _set(0, dur_segura_h=16, dur_agresiva_h=40),
    _set(0, dur_agresiva=2, dur_agresiva_h=8), _set(0, dur_segura=None, dur_segura_h=0), _set(1, dur_agresiva=1), _set(1, dur_agresiva=900),
    _set(0, inicio_real="2026-10-10", fin_real="2026-10-01"), _set(0, inicio_real="2026-10-01", fin_real="2026-10-03"), _set(0, fin_real="2026-10-03", estado="pendiente"),
    _set(0, estado="hecha", fin_real="2026-10-03"), _set(0, estado="excluida"), _set(0, estado="bloqueada"), _set(0, estado=" Hechá "),
    _set(0, paquete="PQ-1", fase_paquete="elaborar"), _set(0, fase_paquete="elaborar"), _set(0, paquete="PQ-1", fase_paquete="x"),
    _set(0, tipo_recurso="externo", recurso=""), _set(0, recurso=""), _set(1, predecesores=["T1", "T1", " T1 "]), _set(0, predecesores="T2"),
]


def _outcome(data, **kw):
    try:
        res = ccpm.calcular_ccpm(json.loads(json.dumps(data)), **kw)
    except Exception as e:                                 # noqa: BLE001 - the type and the message are the behaviour
        return f"{type(e).__name__}: {e}"
    return {"sha": digest(res), "warnings": len(res.get("advertencias", []))}


def ccpm_matrix():
    """Every field of the input and of three tasks of each example set to a series of odd values: what the validation answers to each is pinned (message or result digest)."""
    out = {}
    for name, task_ids in (("example_ccpm.json", (0, 1, 3)), ("example_ccpm_packages.json", (0, 2))):
        base = json.loads((PKG / name).read_text(encoding="utf-8"))
        for f in TOP_FIELDS:
            for k, v in enumerate(TOP_VALUES):
                data = json.loads(json.dumps(base))
                data[f] = v
                out[f"{name}|top|{f}|{k}"] = _outcome(data)
        for ti in task_ids:
            for f in TASK_FIELDS:
                for k, v in enumerate(TASK_VALUES):
                    data = json.loads(json.dumps(base))
                    data["tareas"][ti][f] = v
                    out[f"{name}|task{ti}|{f}|{k}"] = _outcome(data)
        for k, v in enumerate(HITO_VALUES):
            data = json.loads(json.dumps(base))
            data["hitos"] = [v] if "hitos" in data else [v]
            out[f"{name}|hito|{k}"] = _outcome(data)
        for k, desde in enumerate([None, "2026-10-12", "2026-10-10", "bad", 5]):
            for j, lote in enumerate([None, "L1", "zz", ""]):
                out[f"{name}|params|{k}|{j}"] = _outcome(base, desde=desde, lote=lote)
        for k, change in enumerate(COMBOS):
            data = json.loads(json.dumps(base))
            kw = change(data) or {}
            out[f"{name}|combo|{k}"] = _outcome(data, **kw)
        data = json.loads(json.dumps(base))
        for t in data["tareas"]:
            t["estado"] = "hecha"
        out[f"{name}|all_done"] = _outcome(data)
        data = json.loads(json.dumps(base))
        data["tareas"][1]["predecesores"] = [data["tareas"][1]["id"]]
        out[f"{name}|self_predecessor"] = _outcome(data)
        data = json.loads(json.dumps(base))
        data["tareas"].append(json.loads(json.dumps(data["tareas"][0])))
        out[f"{name}|duplicated_id"] = _outcome(data)
    return out


def all_results():
    r = {"ccpm": ccpm_cases(), "ccpm_matrix": ccpm_matrix(), "specification": spec_cases(), "project": project_cases(), "canvas": canvas_cases()}
    return json.loads(json.dumps(r, ensure_ascii=False, default=str))      # what a JSON file gives back: tuples are lists


def main(argv=None) -> int:
    r = all_results()
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(r, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("golden written:", {k: len(v) for k, v in r.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
