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
    return out


# ---------------------------------------------------------------- project verifier
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


def all_results():
    r = {"ccpm": ccpm_cases(), "specification": spec_cases(), "project": project_cases(), "canvas": canvas_cases()}
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
