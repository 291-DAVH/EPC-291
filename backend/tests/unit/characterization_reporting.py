"""Characterization of the PM² report builders (D11 to D15): a rich project context, built by hand, goes through the five builders in both languages and through
`to_markdown`; what is pinned is the document model and the Markdown each one gives. The previous-report snapshot is exercised with and without a value.

Golden file: golden/reporting.json. `python tests/unit/characterization_reporting.py --write` recreates it (only when a change of behaviour is decided on purpose).
"""
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1] / "src")]

from epc.modules.reporting import builders as B   # noqa: E402

GOLDEN = HERE / "golden" / "reporting.json"

OPTIONS = {
    ("risk", "category"): {"tech": "Técnica", "legal": "Legal"}, ("risk", "strategy"): {"mitigate": "Mitigar", "accept": "Aceptar"},
    ("risk", "status"): {"open": "Abierto", "closed": "Cerrado", "materialized": "Materializado"},
    ("change", "status"): {"open": "Abierto", "evaluated": "Evaluado", "approved": "Aprobado", "rejected": "Rechazado", "deferred": "Diferido", "implemented": "Implementado"},
    ("change", "category"): {"scope": "Alcance", "cost": "Costo"}, ("issue", "status"): {"open": "Abierta", "closed": "Cerrada"},
    ("stakeholder", "attitude"): {"supportive": "Favorable", "neutral": "Neutral"},
}


def label(kind, field, value):
    opts = OPTIONS.get((kind, field))
    if opts is not None:
        return opts.get(value, str(value or ""))
    return "" if value is None else str(value)


def context(lang="es", with_data=True):
    d = dt.date
    if not with_data:
        return {"meta": {"project_code": "P-1"}, "lang": lang, "status": {}, "project_name": "Proyecto vacío", "wbs": {"progress": 0.0, "counts": {"nodes": 0, "leaves": 0, "done": 0}, "nodes": []},
                "schedule": {"activities": [], "counts": {"activities": 0, "late": 0, "conflicts": 0}}, "backlog": {"items": []}, "deliverables": [], "requirements": [],
                "inputs": {"open": 0}, "rfc": [], "risks": [], "issues": [], "stakeholders": [], "closed": {"change": ["closed"], "risk": ["closed"], "issue": ["closed"]},
                "label": label, "period_start": d(2026, 10, 1), "period_end": d(2026, 10, 31), "today": d(2026, 11, 2), "nn": 1, "prepared_by": "Ana"}
    return {
        "meta": {"project_code": "P-1", "phase": "ID"}, "lang": lang, "project_name": "Planta Acme",
        "status": {"phase": "IB", "health": "at_risk", "progress_pct": 40, "start": "2026-09-01", "due": "2026-12-31",
                   "milestones": [{"name": "Diseño aprobado", "date": "2026-10-15", "done": True}, {"name": "Entrega IFA", "date": "2026-10-28"}, {"name": "Cierre", "date": "2026-12-31"}]},
        "wbs": {"progress": 62.5, "counts": {"nodes": 4, "leaves": 3, "done": 1}, "nodes": [
            {"id": "1", "name": "Ingeniería", "level": 1, "progress": 75.0, "status": "in_progress", "owner": "Ana", "discipline": "Eléctrica"},
            {"id": "1.1", "name": "Cálculo", "level": 2, "progress": 100.0, "status": "done", "discipline": "Eléctrica"},
            {"id": "1.2", "name": "Planos", "level": 2, "progress": 50.0, "status": "in_progress", "discipline": "Dibujo"},
            {"id": "2", "name": "Gestión", "level": 1, "progress": 0.0, "status": "not_started"}]},
        "schedule": {"activities": [{"id": "A", "name": "Cálculo", "start": "2026-10-01", "end": "2026-10-20", "progress": 100}, {"id": "B", "name": "Planos", "start": "2026-11-01", "end": "2026-11-10", "progress": 0},
                                    {"id": "C", "name": "Revisión", "start": "2026-10-10", "end": "2026-10-25", "progress": 20}], "counts": {"activities": 3, "late": 1, "conflicts": 0}},
        "backlog": {"items": [{"title": "Memoria de cálculo", "estimate_h": 40, "wbs_id": "1.1", "status": "done", "owner": "Ana"}, {"title": "Unifilares", "estimate_h": 60, "wbs_id": "1.2", "status": "doing", "owner": "Luis"},
                              {"title": "Coordinación", "estimate_h": 10, "wbs_id": "", "status": "todo"}]},
        "deliverables": [{"code": "P1-E-MC-001", "name": "Memoria de cálculo", "status": "delivered", "delivered_on": "2026-10-12", "revision": "00.1", "due": "2026-10-10"},
                         {"code": "P1-E-PL-001", "name": "Unifilar", "status": "draft", "due": "2026-11-05", "revision": "00.0", "overdue": False},
                         {"code": "P1-E-PL-002", "name": "Multifilar", "status": "draft", "due": "2026-10-20", "revision": "00.0", "overdue": True}],
        "requirements": [{"id": "REQ-001", "open_questions": ["¿Tensión de servicio?", "¿Régimen de neutro?"], "answered_questions": [{"question": "¿Potencia?", "at": "2026-10-14", "by": "Cliente"}]},
                         {"id": "REQ-002", "open_questions": [], "answered_questions": []}],
        "inputs": {"open": 2},
        "rfc": [{"id": "RFC-001", "title": "Agregar tablero", "status": "open", "opened": "2026-10-05", "owner": "Ana", "category": "scope"},
                {"id": "RFC-002", "title": "Cambio de cable", "status": "approved", "opened": "2026-09-20", "decided_on": "2026-10-10", "decision_ref": "DEC-001", "owner": "Luis", "category": "cost"},
                {"id": "RFC-003", "title": "Ampliar planta", "status": "rejected", "opened": "2026-09-25", "decided_on": "2026-10-12", "decision_ref": "DEC-002", "justification": "Fuera de alcance", "category": "scope"},
                {"id": "RFC-004", "title": "Sello", "status": "evaluated", "opened": "2026-10-20", "owner": "Ana"}],
        "risks": [{"id": "RIE-001", "title": "Retraso del cliente", "status": "open", "probability": 4, "impact": 5, "level": 20, "level_name": "high", "category": "tech", "strategy": "mitigate", "owner": "Ana",
                   "response": "Reunión semanal", "opened": "2026-10-02"},
                  {"id": "RIE-002", "title": "Cambio normativo", "status": "open", "probability": 2, "impact": 3, "level": 6, "level_name": "medium", "category": "legal", "strategy": "accept", "opened": "2026-09-01"},
                  {"id": "RIE-003", "title": "Proveedor", "status": "open", "probability": 1, "impact": 1, "level": 1, "level_name": "low"},
                  {"id": "RIE-004", "title": "Falla de licencia", "status": "closed", "probability": 3, "impact": 3, "level": 9, "level_name": "medium", "closed_on": "2026-10-22", "closing_reason": "Resuelto",
                   "opened": "2026-09-10"}],
        "issues": [{"id": "INC-001", "title": "Plano ilegible", "status": "open", "impact": "Medio", "due": "2026-11-03", "owner": "Luis"}, {"id": "INC-002", "title": "Cerrada", "status": "closed"}],
        "stakeholders": [{"id": "INT-001", "name": "Cliente SA", "role": "Dueño", "organization": "Cliente", "attitude": "supportive"}],
        "closed": {"change": ["closed", "implemented"], "risk": ["closed"], "issue": ["closed"]}, "label": label,
        "period_start": d(2026, 10, 1), "period_end": d(2026, 10, 31), "today": d(2026, 11, 2), "nn": 3, "prepared_by": "Ana",
    }


def cases():
    return {f"{lang}|{'full' if full else 'empty'}": context(lang, full) for lang in ("es", "en") for full in (True, False)}


def run():
    out = {}
    for key, ctx in cases().items():
        for name, build in B.BUILDERS.items():
            for prev_key, prev in (("no_prev", None), ("prev", {"ranks": {"scope": 0, "schedule": 2, "quality": 0, "risks": 1, "changes": 0}, "risks_high": 3})):
                doc = build(ctx, prev)
                out[f"{key}|{name}|{prev_key}"] = {"doc": doc, "markdown": B.to_markdown({**doc, "subtitle": "INF-001"})}
    out["helpers"] = {"d": [str(B.d(x)) for x in ("2026-10-23", "23/10/2026", "23-10-2026", "", None, "x", "2026-10-23T10:00")],
                      "fmt_date": [B.fmt_date(x) for x in ("2026-10-23", "", None, "bad")],
                      "assess_full": {k: v for k, v in B.assess(context("es", True)).items() if k not in ("rfc_open", "risks_active", "high", "med", "ms")},
                      "assess_empty": {k: v for k, v in B.assess(context("en", False)).items() if k not in ("rfc_open", "risks_active", "high", "med", "ms")}}
    return json.loads(json.dumps(out, ensure_ascii=False, default=str))


def main(argv=None) -> int:
    r = run()
    if "--write" in (argv or sys.argv[1:]):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(r, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        print("golden written:", len(r), "entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
