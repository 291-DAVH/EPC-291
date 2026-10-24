"""Content of the PM² reports D11 to D15 (management-templates.md), built from the project's data.

A report is a *document model*: {"title", "subtitle", "summary", "blocks": [...]} with blocks kv / h / p / bullets / table. The Markdown file and the PDF are two renderings of it.
Nothing is invented: a figure the platform does not hold (for example hours actually worked) is shown as "n/d" with a note, and an empty register says so.
"""
import datetime as dt
import re
from typing import Dict, List, Optional, Tuple

T: Dict[str, Dict[str, str]] = {
    "es": {
        "project": "Proyecto", "code": "Código", "phase": "Fase actual", "period": "Período reportado", "number": "N° Informe", "by": "Elaborado por", "date": "Fecha",
        "general": "Estado general", "dimension": "Dimensión", "state": "Estado", "trend": "Tendencia", "comment": "Comentario breve",
        "scope": "Alcance", "schedule": "Cronograma", "quality": "Calidad", "risks": "Riesgos", "changes": "Cambios", "overall": "Estado general del proyecto",
        "exec": "Resumen ejecutivo", "kpis": "Indicadores de desempeño", "indicator": "Indicador", "planned": "Planificado", "real": "Real", "variation": "Variación",
        "kpi.progress": "Avance físico global (%)", "kpi.milestones": "Hitos completados / total",
        "done": "Actividades realizadas", "next": "Actividades planificadas para el próximo período", "none_done": "Sin actividades registradas en el período.", "none_next": "Sin actividades planificadas.",
        "milestones": "Hitos", "milestone": "Hito", "baseline": "Fecha línea base", "forecast": "Fecha real / proyectada",
        "ms.done": "Completado", "ms.ontime": "En plazo", "ms.late": "Con retraso",
        "active_changes": "Cambios activos (del registro de cambios)", "active_risks": "Riesgos activos relevantes", "issues": "Problemas / Incidencias",
        "decisions": "Decisiones requeridas", "topic": "Tema", "decider": "Decisor", "deadline": "Fecha límite", "client": "Cliente",
        "description": "Descripción", "level": "Nivel", "action": "Acción en curso", "impact": "Impacto", "owner": "Responsable", "status": "Estado",
        "empty.changes": "Sin solicitudes de cambio registradas.", "empty.risks": "Sin riesgos registrados.", "empty.issues": "Sin incidencias registradas.",
        "empty.decisions": "Sin decisiones pendientes.", "empty.ms": "Sin hitos definidos.",
        "stakeholders": "Interesados clave", "name": "Nombre", "role": "Rol", "org": "Organización", "involvement": "Nivel de involucramiento", "empty.stk": "Sin interesados registrados (pestaña Registros).",
        "ms_deliv": "Hitos y entregables", "deliverable": "Entregable", "revision": "Revisión", "due": "Vencimiento",
        "work_packages": "Plan de trabajo por paquete", "package": "Paquete de trabajo", "progress": "Avance (%)", "remarks": "Observaciones", "empty.wbs": "Sin EDT definida.",
        "scope_changes": "Cambios de alcance", "approved_acc": "Cambios aprobados acumulados", "main_risks": "Riesgos principales y acciones", "main_issues": "Problemas principales y acciones",
        "other_actions": "Otras acciones en curso / planificadas", "achievements": "Logros del período", "empty.ach": "Sin logros registrados en el período.",
        "appendix": "Apéndice: documentos relacionados", "document": "Documento", "location": "Ubicación",
        "risk.summary": "Resumen del registro de riesgos", "category": "Categoría", "high": "Alto (crítico)", "medium": "Medio", "low": "Bajo", "total_active": "Total activos", "total": "Total",
        "risk.high": "Riesgos activos de nivel alto", "risk.medium": "Riesgos de nivel medio activos", "risk.new": "Riesgos nuevos en el período", "risk.closed": "Riesgos cerrados en el período",
        "prob": "Prob.", "strategy": "Estrategia", "reason": "Motivo de cierre", "closed_on": "Fecha cierre", "risk.evolution": "Evolución del perfil de riesgo",
        "prev_period": "Período anterior", "curr_period": "Período actual", "high_risks": "Riesgos altos", "risk.conclusions": "Conclusiones y acciones recomendadas",
        "risk.src": "Fuente: registro de riesgos del proyecto (pestaña Registros).", "general_cat": "General",
        "effort.by_disc": "Esfuerzo por disciplina", "discipline": "Disciplina / rol", "hh_base": "HH línea base", "hh_earned": "HH ganadas (según avance)", "hh_left": "HH remanentes",
        "pct": "% avance", "effort.by_pkg": "Esfuerzo por paquete de trabajo", "effort.remaining": "Proyección de esfuerzo remanente", "hh_total": "HH total proyectadas",
        "effort.notes": "Observaciones y alertas", "effort.nohours": "Las horas realmente trabajadas todavía no se registran en la plataforma: no se calcula la desviación contra horas reales; las horas ganadas se obtienen del avance de cada paquete.",
        "effort.nobase": "Sin horas estimadas: carga las estimaciones en el backlog del proyecto.", "effort.noassoc": "Sin disciplina", "effort.nocost": "Los valores corresponden al plan aprobado. No se incluyen tarifas ni costos.",
        "chg.summary": "Resumen del período", "chg.status": "Estado rfc", "chg.period": "Cantidad en período", "chg.acc": "Acumulado total",
        "chg.approved": "Cambios aprobados", "chg.rejected": "Cambios rechazados o diferidos", "chg.eval": "Cambios en proceso de evaluación", "chg.conclusions": "Conclusiones",
        "chg.src": "Fuente: registro de cambios del proyecto (pestaña Registros).", "title_col": "Título", "opened": "Fecha apertura", "decision": "Decisión", "justification": "Justificación",
        "st.open": "Abiertos", "st.evaluated": "Evaluados", "st.approved": "Aprobados", "st.rejected": "Rechazados", "st.deferred": "Diferidos", "st.implemented": "Implementados", "st.closed": "Cerrados",
        "page": "Página {n} de {total}", "footer": "{name} {tr} · {project}", "nd": "n/d", "trend_note": "La tendencia compara con el informe anterior del mismo tipo.",
        "sum.text": "El proyecto se encuentra en la fase «{phase}» con un avance físico de {real} % (planificado: {plan}) y estado general {color}. Se completaron {hd} de {ht} hitos. Entregables vencidos: {od}; datos de entrada en análisis: {oi}; preguntas abiertas en requisitos: {oq}; cambios abiertos: {rfc}; riesgos de nivel alto: {rh}.",
        "c.VERDE": "VERDE", "c.AMARILLO": "AMARILLO", "c.ROJO": "ROJO",
        "cm.scope": "Preguntas abiertas en requisitos: {q}; cambios abiertos: {r}.", "cm.schedule": "Entregables vencidos: {od}; actividades atrasadas: {la}.",
        "cm.quality": "Sin registros de no conformidades.", "cm.risks": "Riesgos altos: {h}; medios: {m}.", "cm.changes": "Cambios abiertos: {r}.",
        "q.pending": "Pregunta abierta de requisito", "answered": "Respuesta registrada en {rid} por {who}", "delivered": "Entregable emitido", "ms_reached": "Hito alcanzado",
        "next.activity": "Actividad del cronograma", "next.deliv": "Entregable a emitir",
    },
    "en": {
        "project": "Project", "code": "Code", "phase": "Current phase", "period": "Reporting period", "number": "Report No.", "by": "Prepared by", "date": "Date",
        "general": "Overall status", "dimension": "Dimension", "state": "Status", "trend": "Trend", "comment": "Brief comment",
        "scope": "Scope", "schedule": "Schedule", "quality": "Quality", "risks": "Risks", "changes": "Changes", "overall": "Overall project status",
        "exec": "Executive summary", "kpis": "Performance indicators", "indicator": "Indicator", "planned": "Planned", "real": "Actual", "variation": "Variance",
        "kpi.progress": "Overall physical progress (%)", "kpi.milestones": "Milestones completed / total",
        "done": "Activities carried out", "next": "Activities planned for the next period", "none_done": "No activities recorded in the period.", "none_next": "No activities planned.",
        "milestones": "Milestones", "milestone": "Milestone", "baseline": "Baseline date", "forecast": "Actual / forecast date",
        "ms.done": "Completed", "ms.ontime": "On time", "ms.late": "Delayed",
        "active_changes": "Active changes (from the change log)", "active_risks": "Relevant active risks", "issues": "Issues",
        "decisions": "Decisions required", "topic": "Topic", "decider": "Decision maker", "deadline": "Deadline", "client": "Client",
        "description": "Description", "level": "Level", "action": "Action in progress", "impact": "Impact", "owner": "Owner", "status": "Status",
        "empty.changes": "No change requests recorded.", "empty.risks": "No risks recorded.", "empty.issues": "No issues recorded.",
        "empty.decisions": "No pending decisions.", "empty.ms": "No milestones defined.",
        "stakeholders": "Key stakeholders", "name": "Name", "role": "Role", "org": "Organization", "involvement": "Level of involvement", "empty.stk": "No stakeholders recorded (Registers tab).",
        "ms_deliv": "Milestones and deliverables", "deliverable": "Deliverable", "revision": "Revision", "due": "Due",
        "work_packages": "Work plan by package", "package": "Work package", "progress": "Progress (%)", "remarks": "Remarks", "empty.wbs": "No WBS defined.",
        "scope_changes": "Scope changes", "approved_acc": "Accumulated approved changes", "main_risks": "Main risks and actions", "main_issues": "Main issues and actions",
        "other_actions": "Other actions in progress / planned", "achievements": "Achievements of the period", "empty.ach": "No achievements recorded in the period.",
        "appendix": "Appendix: related documents", "document": "Document", "location": "Location",
        "risk.summary": "Risk register summary", "category": "Category", "high": "High (critical)", "medium": "Medium", "low": "Low", "total_active": "Total active", "total": "Total",
        "risk.high": "Active high-level risks", "risk.medium": "Active medium-level risks", "risk.new": "New risks in the period", "risk.closed": "Risks closed in the period",
        "prob": "Prob.", "strategy": "Strategy", "reason": "Closing reason", "closed_on": "Closing date", "risk.evolution": "Risk profile evolution",
        "prev_period": "Previous period", "curr_period": "Current period", "high_risks": "High risks", "risk.conclusions": "Conclusions and recommended actions",
        "risk.src": "Source: the project's risk register (Registers tab).", "general_cat": "General",
        "effort.by_disc": "Effort by discipline", "discipline": "Discipline / role", "hh_base": "Baseline hours", "hh_earned": "Earned hours (by progress)", "hh_left": "Remaining hours",
        "pct": "% progress", "effort.by_pkg": "Effort by work package", "effort.remaining": "Remaining effort forecast", "hh_total": "Total projected hours",
        "effort.notes": "Remarks and alerts", "effort.nohours": "Hours actually worked are not recorded in the platform yet: no variance against actual hours is computed; earned hours come from the progress of each package.",
        "effort.nobase": "No estimated hours: enter the estimates in the project backlog.", "effort.noassoc": "No discipline", "effort.nocost": "Values correspond to the approved plan. No rates or costs are included.",
        "chg.summary": "Summary of the period", "chg.status": "RFC status", "chg.period": "Count in period", "chg.acc": "Accumulated total",
        "chg.approved": "Approved changes", "chg.rejected": "Rejected or deferred changes", "chg.eval": "Changes under evaluation", "chg.conclusions": "Conclusions",
        "chg.src": "Source: the project's change register (Registers tab).", "title_col": "Title", "opened": "Opening date", "decision": "Decision", "justification": "Justification",
        "st.open": "Open", "st.evaluated": "Evaluated", "st.approved": "Approved", "st.rejected": "Rejected", "st.deferred": "Deferred", "st.implemented": "Implemented", "st.closed": "Closed",
        "page": "Page {n} of {total}", "footer": "{name} {tr} · {project}", "nd": "n/a", "trend_note": "The trend compares with the previous report of the same type.",
        "sum.text": "The project is in the \"{phase}\" phase with a physical progress of {real} % (planned: {plan}) and an overall status of {color}. {hd} of {ht} milestones are complete. Overdue deliverables: {od}; input items under analysis: {oi}; open questions on requirements: {oq}; open changes: {rfc}; high-level risks: {rh}.",
        "c.VERDE": "GREEN", "c.AMARILLO": "AMBER", "c.ROJO": "RED",
        "cm.scope": "Open questions on requirements: {q}; open changes: {r}.", "cm.schedule": "Overdue deliverables: {od}; late activities: {la}.",
        "cm.quality": "No non-conformities recorded.", "cm.risks": "High risks: {h}; medium: {m}.", "cm.changes": "Open changes: {r}.",
        "q.pending": "Open requirement question", "answered": "Answer recorded on {rid} by {who}", "delivered": "Deliverable issued", "ms_reached": "Milestone reached",
        "next.activity": "Schedule activity", "next.deliv": "Deliverable to issue",
    },
}
PHASES = {"es": {"IC": "Ingeniería conceptual", "IB": "Ingeniería básica", "ID": "Ingeniería de detalle", "IE": "Ingeniería de ejecución", "ASB": "As-built"},
          "en": {"IC": "Conceptual engineering", "IB": "Basic engineering", "ID": "Detail engineering", "IE": "Execution engineering", "ASB": "As-built"}}
COLORS = ["VERDE", "AMARILLO", "ROJO"]
ARROW = {-1: "↑", 0: "→", 1: "↓"}               # a lower rank is better: the arrow shows the direction of the status


def d(s) -> Optional[dt.date]:
    if isinstance(s, dt.date):
        return s
    s = (s or "").strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s[:10], f).date()
        except ValueError:
            continue
    return None


def lvl(r: dict) -> str:
    """high | medium | low: derived by the registers module from probability x impact."""
    return r.get("level_name") or "medium"


def is_closed(c: dict, kind: str, r: dict) -> bool:
    return r.get("status") in c["closed"][kind]


def in_period(c: dict, s) -> bool:
    x = d(s)
    return bool(x and c["period_start"] <= x <= c["period_end"])


def fmt_date(x) -> str:
    x = d(x)
    return x.strftime("%d/%m/%Y") if x else ""


# ---------------------------------------------------------------- assessment shared by D11 and D12
def assess(c: dict) -> dict:
    st, sched, deliv, reqs = c["status"], c["schedule"], c["deliverables"], c["requirements"]
    rfc_open = [r for r in c["rfc"] if r.get("status") in ("open", "evaluated")]
    risks = [r for r in c["risks"] if not is_closed(c, "risk", r)]
    high = [r for r in risks if lvl(r) == "high"]
    med = [r for r in risks if lvl(r) == "medium"]
    open_q = sum(len(r.get("open_questions", [])) for r in reqs)
    overdue = sum(1 for x in deliv if x.get("overdue"))
    late = sched["counts"]["late"] if sched.get("activities") else 0
    health = {"on_track": 0, "at_risk": 1, "delayed": 2}.get(st.get("health", "on_track"), 0)
    ranks = {"scope": 1 if (open_q or rfc_open) else 0, "schedule": max(health, 1 if (overdue or late) else 0),
             "quality": 0, "risks": 2 if high else 1 if med else 0, "changes": 1 if rfc_open else 0}
    real = c["wbs"]["progress"] if c["wbs"]["counts"]["nodes"] else float(st.get("progress_pct", 0) or 0)
    start, due = d(st.get("start")), d(st.get("due"))
    plan = None
    if start and due and due > start:
        plan = round(max(0.0, min(1.0, (c["period_end"] - start).days / (due - start).days)) * 100, 1)
    ms = st.get("milestones", [])
    return {"ranks": ranks, "overall": max(ranks.values()), "rfc_open": rfc_open, "risks_active": risks, "high": high, "med": med, "open_q": open_q,
            "overdue": overdue, "late": late, "real": round(real, 1), "plan": plan, "ms": ms, "ms_done": sum(1 for m in ms if m.get("done")),
            "ms_planned": sum(1 for m in ms if d(m.get("date")) and d(m.get("date")) <= c["period_end"])}


def summary_text(c: dict, a: dict, t: dict) -> str:
    phase = c["status"].get("phase") or c["meta"].get("phase") or ""
    return t["sum.text"].format(phase=PHASES[c["lang"]].get(phase, phase) or "-", real=f"{a['real']:g}", plan=f"{a['plan']:g} %" if a["plan"] is not None else t["nd"],
                                color=t["c." + COLORS[a["overall"]]], hd=a["ms_done"], ht=len(a["ms"]), od=a["overdue"], oi=c["inputs"]["open"], oq=a["open_q"],
                                rfc=len(a["rfc_open"]), rh=len(a["high"]))


def header_kv(c: dict, t: dict, with_phase: bool = True) -> dict:
    p = c["meta"]
    rows = [[t["project"], c["project_name"]], [t["code"], p.get("project_code", "")]]
    if with_phase:
        phase = c["status"].get("phase") or p.get("phase") or ""
        rows.append([t["phase"], PHASES[c["lang"]].get(phase, phase) or "-"])
    rows += [[t["period"], f"{fmt_date(c['period_start'])} – {fmt_date(c['period_end'])}"], [t["number"], f"{c['nn']:02d}"], [t["by"], c["prepared_by"]], [t["date"], fmt_date(c["today"])]]
    return {"type": "kv", "rows": rows}


def table(cols, rows, empty):
    return {"type": "table", "columns": cols, "rows": rows, "empty": empty}


def milestone_rows(c: dict, a: dict, t: dict) -> List[List[str]]:
    rows = []
    for m in a["ms"]:
        due = d(m.get("date"))
        state = t["ms.done"] if m.get("done") else (t["ms.late"] if due and due < c["today"] else t["ms.ontime"])
        rows.append([m.get("name", ""), fmt_date(m.get("date")), fmt_date(m.get("date")), state])
    return rows


def change_rows(c: dict, a: dict) -> List[List[str]]:
    return [[r["id"], r["title"], c["label"]("change", "status", r["status"])] for r in a["rfc_open"]]


def risk_rows(c: dict, risks: List[dict]) -> List[List[str]]:
    return [[r["id"], r["title"], f"{r.get('level', '')} · {T[c['lang']][lvl(r)]}", r.get("response") or c["label"]("risk", "strategy", r.get("strategy"))]
            for r in risks]


def issue_rows(c: dict) -> List[List[str]]:
    t = T[c["lang"]]
    return [[f"{r['id']} {r['title']}", r.get("impact", ""), f"{c['label']('issue', 'status', r['status'])} · {fmt_date(r.get('due'))}", r.get("owner", "")]
            for r in c["issues"] if not is_closed(c, "issue", r)]


def decision_rows(c: dict, t: dict) -> List[List[str]]:
    rows = []
    for r in c["requirements"]:
        for q in r.get("open_questions", []):
            rows.append([f"{r['id']}: {q}", t["client"], "-"])
    return rows


# ---------------------------------------------------------------- D11 status report
def status_report(c: dict, prev: Optional[dict]) -> dict:
    t = T[c["lang"]]
    a = assess(c)
    cm = {"scope": t["cm.scope"].format(q=a["open_q"], r=len(a["rfc_open"])), "schedule": t["cm.schedule"].format(od=a["overdue"], la=a["late"]),
          "quality": t["cm.quality"], "risks": t["cm.risks"].format(h=len(a["high"]), m=len(a["med"])), "changes": t["cm.changes"].format(r=len(a["rfc_open"]))}
    dims = []
    for k in ("scope", "schedule", "quality", "risks", "changes"):
        pr = (prev or {}).get("ranks", {}).get(k)
        arrow = ARROW[(a["ranks"][k] > pr) - (a["ranks"][k] < pr)] if pr is not None else "→"
        dims.append([t[k], t["c." + COLORS[a["ranks"][k]]], arrow, cm[k]])
    done, nxt = period_activities(c, t)
    blocks = [header_kv(c, t),
              {"type": "h", "text": t["general"]}, table([[t["dimension"], 0.18], [t["state"], 0.16], [t["trend"], 0.12], [t["comment"], 0.54]], dims, ""),
              {"type": "p", "text": f"{t['overall']}: {t['c.' + COLORS[a['overall']]]}"}, {"type": "p", "text": t["trend_note"]},
              {"type": "h", "text": t["exec"]}, {"type": "p", "text": summary_text(c, a, t)},
              {"type": "h", "text": t["kpis"]},
              table([[t["indicator"], 0.46], [t["planned"], 0.18], [t["real"], 0.18], [t["variation"], 0.18]],
                    [[t["kpi.progress"], f"{a['plan']:g}" if a["plan"] is not None else t["nd"], f"{a['real']:g}", f"{a['real'] - a['plan']:+.1f}" if a["plan"] is not None else t["nd"]],
                     [t["kpi.milestones"], f"{a['ms_planned']} / {len(a['ms'])}", f"{a['ms_done']} / {len(a['ms'])}", f"{a['ms_done'] - a['ms_planned']:+d}"]], ""),
              {"type": "h", "text": t["done"]}, {"type": "bullets", "items": done or [t["none_done"]]},
              {"type": "h", "text": t["next"]}, {"type": "bullets", "items": nxt or [t["none_next"]]},
              {"type": "h", "text": t["milestones"]},
              table([[t["milestone"], 0.3], [t["baseline"], 0.2], [t["forecast"], 0.3], [t["state"], 0.2]], milestone_rows(c, a, t), t["empty.ms"]),
              {"type": "h", "text": t["active_changes"]}, table([["rfc", 0.2], [t["description"], 0.55], [t["state"], 0.25]], change_rows(c, a), t["empty.changes"]),
              {"type": "h", "text": t["active_risks"]},
              table([["RIE", 0.15], [t["description"], 0.45], [t["level"], 0.15], [t["action"], 0.25]], risk_rows(c, a["high"] + a["med"]), t["empty.risks"]),
              {"type": "h", "text": t["issues"]},
              table([[t["description"], 0.4], [t["impact"], 0.2], [t["action"], 0.2], [t["owner"], 0.2]], issue_rows(c), t["empty.issues"]),
              {"type": "h", "text": t["decisions"]},
              table([[t["topic"], 0.6], [t["decider"], 0.2], [t["deadline"], 0.2]], decision_rows(c, t), t["empty.decisions"])]
    return {"title": "INFORME DE ESTADO" if c["lang"] == "es" else "STATUS REPORT", "summary": summary_text(c, a, t), "blocks": blocks,
            "snapshot": {"ranks": a["ranks"], "risks_high": len(a["high"])}}


def period_activities(c: dict, t: dict) -> Tuple[List[str], List[str]]:
    ps, pe = c["period_start"], c["period_end"]
    done: List[str] = []
    for x in c["deliverables"]:
        if x.get("status") == "delivered" and d(x.get("delivered_on")) and ps <= d(x.get("delivered_on")) <= pe:
            done.append(f"{t['delivered']}: {x.get('code', '')} – {x.get('name', '')}")
    for m in c["status"].get("milestones", []):
        if m.get("done") and d(m.get("date")) and ps <= d(m["date"]) <= pe:
            done.append(f"{t['ms_reached']}: {m['name']}")
    for r in c["requirements"]:
        for a in r.get("answered_questions", []):
            when = d(a.get("at"))
            if when and ps <= when <= pe:
                done.append(f"{t['answered'].format(rid=r['id'], who=a.get('by', '-'))}: {a['question']}")
    span = max((pe - ps).days, 7)
    ns, ne = pe + dt.timedelta(days=1), pe + dt.timedelta(days=span)
    nxt: List[str] = []
    for a in c["schedule"].get("activities", []):
        s, e = d(a.get("start")), d(a.get("end"))
        if s and e and a.get("progress", 0) < 100 and s <= ne and e >= ns:
            nxt.append(f"{t['next.activity']}: {a['name']} ({fmt_date(a['start'])} – {fmt_date(a['end'])})")
    for x in c["deliverables"]:
        if x.get("status") != "delivered" and d(x.get("due")) and ns <= d(x["due"]) <= ne:
            nxt.append(f"{t['next.deliv']}: {x.get('code', '')} – {x.get('name', '')} ({fmt_date(x['due'])})")
    return done, nxt


# ---------------------------------------------------------------- D12 progress report
def progress_report(c: dict, prev: Optional[dict]) -> dict:
    t = T[c["lang"]]
    a = assess(c)
    done, _ = period_activities(c, t)
    stk = [[r["id"], r["name"], r.get("role", ""), r.get("organization", ""), c["label"]("stakeholder", "attitude", r.get("attitude"))] for r in c["stakeholders"]]
    wp = [[f"{n['id']} {n['name']}", n.get("owner", "") or "-", f"{n['progress']:g}", t["ms.done"] if n["status"] == "done" else t["ms.ontime"] if n["status"] == "in_progress" else "-",
           n.get("discipline", "")] for n in c["wbs"]["nodes"] if n["level"] <= 2]
    dl = [[f"{x.get('code', '')} {x.get('name', '')}".strip(), x.get("revision", ""), fmt_date(x.get("due")), t["ms.done"] if x.get("status") == "delivered" else (t["ms.late"] if x.get("overdue") else x.get("status", ""))]
          for x in c["deliverables"]]
    other = [[b["title"], b.get("owner", "") or "-", b["status"], "-"] for b in c["backlog"]["items"] if b["status"] != "done"][:15]
    appendix = [[x, "—", "workspace/05-management/registers/"] for x in ("change.json", "risk.json", "issue.json", "decision.json")]
    blocks = [header_kv(c, t, with_phase=False),
              {"type": "h", "text": f"1. {t['exec']}"}, {"type": "p", "text": f"{t['overall']}: {t['c.' + COLORS[a['overall']]]}. {summary_text(c, a, t)}"},
              {"type": "h", "text": f"2. {t['stakeholders']}"},
              table([["ID", 0.12], [t["name"], 0.28], [t["role"], 0.2], [t["org"], 0.2], [t["involvement"], 0.2]], stk, t["empty.stk"]),
              {"type": "h", "text": f"3. {t['ms_deliv']}"},
              table([[t["milestone"], 0.3], [t["baseline"], 0.2], [t["forecast"], 0.3], [t["state"], 0.2]], milestone_rows(c, a, t), t["empty.ms"]),
              table([[t["deliverable"], 0.46], [t["revision"], 0.14], [t["due"], 0.18], [t["state"], 0.22]], dl, ""),
              {"type": "h", "text": f"4. {t['work_packages']}"},
              table([[t["package"], 0.38], [t["owner"], 0.16], [t["progress"], 0.14], [t["state"], 0.14], [t["remarks"], 0.18]], wp, t["empty.wbs"]),
              {"type": "h", "text": f"5. {t['scope_changes']}"}, table([["rfc", 0.2], [t["description"], 0.55], [t["state"], 0.25]], change_rows(c, a), t["empty.changes"]),
              {"type": "p", "text": f"{t['approved_acc']}: {sum(1 for r in c['rfc'] if r.get('status') in ('approved', 'implemented'))}"},
              {"type": "h", "text": f"6. {t['main_risks']}"},
              table([["RIE", 0.12], [t["description"], 0.4], [t["level"], 0.12], [t["action"], 0.2], [t["owner"], 0.16]],
                    [[r["id"], r["title"], str(r.get("level", "")), r.get("response") or c["label"]("risk", "strategy", r.get("strategy")), r.get("owner", "")]
                     for r in a["high"] + a["med"]], t["empty.risks"]),
              {"type": "h", "text": f"7. {t['main_issues']}"},
              table([[t["description"], 0.4], [t["impact"], 0.2], [t["action"], 0.2], [t["owner"], 0.2]], issue_rows(c), t["empty.issues"]),
              {"type": "h", "text": f"8. {t['other_actions']}"},
              table([[t["description"], 0.5], [t["owner"], 0.2], [t["state"], 0.15], [t["deadline"], 0.15]], other, t["none_next"]),
              {"type": "h", "text": f"9. {t['achievements']}"}, {"type": "bullets", "items": done or [t["empty.ach"]]},
              {"type": "h", "text": t["appendix"]}, table([[t["document"], 0.5], [t["revision"], 0.15], [t["location"], 0.35]], appendix, "")]
    return {"title": "INFORME DE AVANCE" if c["lang"] == "es" else "PROGRESS REPORT", "summary": summary_text(c, a, t), "blocks": blocks,
            "snapshot": {"ranks": a["ranks"], "risks_high": len(a["high"])}}


# ---------------------------------------------------------------- D13 risk report
def risk_report(c: dict, prev: Optional[dict]) -> dict:
    t = T[c["lang"]]
    a = assess(c)
    lab = c["label"]
    cats: Dict[str, Dict[str, int]] = {}
    for r in a["risks_active"]:
        cat = lab("risk", "category", r.get("category")) or t["general_cat"]
        cats.setdefault(cat, {"high": 0, "medium": 0, "low": 0})[lvl(r)] += 1
    cat_rows = [[k, str(v["high"]), str(v["medium"]), str(v["low"]), str(sum(v.values()))] for k, v in sorted(cats.items())]
    if cat_rows:
        tot = [sum(int(r[i]) for r in cat_rows) for i in range(1, 5)]
        cat_rows.append([t["total"]] + [str(x) for x in tot])

    def line(r, full=True):
        base = [r["id"], r["title"], str(r.get("probability") or ""), str(r.get("impact") or "")]
        if full:
            return base + [str(r.get("level", "")), lab("risk", "strategy", r.get("strategy")), r.get("owner", ""), lab("risk", "status", r["status"])]
        return base + [lab("risk", "strategy", r.get("strategy")), r.get("owner", "")]

    new = [r for r in c["risks"] if in_period(c, r.get("opened"))]
    closed = [r for r in c["risks"] if is_closed(c, "risk", r) and in_period(c, r.get("closed_on"))]
    pr_high = (prev or {}).get("risks_high")
    arrow = ARROW[(len(a["high"]) > pr_high) - (len(a["high"]) < pr_high)] if pr_high is not None else "→"
    concl = [t["cm.risks"].format(h=len(a["high"]), m=len(a["med"]))] if a["risks_active"] else [t["empty.risks"]]
    blocks = [header_kv(c, t, with_phase=False),
              {"type": "h", "text": t["risk.summary"]},
              table([[t["category"], 0.36], [t["high"], 0.16], [t["medium"], 0.16], [t["low"], 0.16], [t["total_active"], 0.16]], cat_rows, t["empty.risks"]),
              {"type": "h", "text": t["risk.high"]},
              table([["RIE", 0.09], [t["description"], 0.27], [t["prob"], 0.08], [t["impact"], 0.1], [t["level"], 0.09], [t["strategy"], 0.13], [t["owner"], 0.12], [t["state"], 0.12]],
                    [line(r) for r in a["high"]], t["empty.risks"]),
              {"type": "h", "text": t["risk.medium"]},
              table([["RIE", 0.1], [t["description"], 0.36], [t["prob"], 0.09], [t["impact"], 0.1], [t["strategy"], 0.17], [t["owner"], 0.18]], [line(r, False) for r in a["med"]], t["empty.risks"]),
              {"type": "h", "text": t["risk.new"]},
              table([["RIE", 0.1], [t["description"], 0.36], [t["prob"], 0.09], [t["impact"], 0.1], [t["strategy"], 0.17], [t["owner"], 0.18]], [line(r, False) for r in new], t["empty.risks"]),
              {"type": "h", "text": t["risk.closed"]},
              table([["RIE", 0.12], [t["description"], 0.4], [t["reason"], 0.28], [t["closed_on"], 0.2]],
                    [[r["id"], r["title"], f"{lab('risk', 'status', r['status'])}{(' – ' + r['closing_reason']) if r.get('closing_reason') else ''}", fmt_date(r.get("closed_on"))] for r in closed],
                    t["empty.risks"]),
              {"type": "h", "text": t["risk.evolution"]},
              table([[t["prev_period"], 0.35], [t["curr_period"], 0.35], [t["trend"], 0.3]],
                    [[f"{t['high_risks']}: {pr_high if pr_high is not None else t['nd']}", f"{t['high_risks']}: {len(a['high'])}", arrow]], ""),
              {"type": "h", "text": t["risk.conclusions"]}, {"type": "bullets", "items": concl}, {"type": "p", "text": t["risk.src"]}]
    return {"title": "INFORME DE RIESGOS" if c["lang"] == "es" else "RISK REPORT", "summary": concl[0], "blocks": blocks,
            "snapshot": {"ranks": a["ranks"], "risks_high": len(a["high"])}}


# ---------------------------------------------------------------- D14 effort report
def effort_report(c: dict, prev: Optional[dict]) -> dict:
    t = T[c["lang"]]
    a = assess(c)
    nodes = {n["id"]: n for n in c["wbs"]["nodes"]}
    by_disc: Dict[str, List[float]] = {}
    by_pkg: Dict[str, List[float]] = {}
    for b in c["backlog"]["items"]:
        est = float(b.get("estimate_h") or 0)
        node = nodes.get(b.get("wbs_id", ""))
        prog = node["progress"] if node else (100.0 if b["status"] == "done" else 0.0)
        disc = (node or {}).get("discipline") or t["effort.noassoc"]
        for table_, key in ((by_disc, disc), (by_pkg, f"{b['wbs_id']} {node['name']}" if node else t["effort.noassoc"])):
            row = table_.setdefault(key, [0.0, 0.0])
            row[0] += est
            row[1] += est * prog / 100
    base = sum(v[0] for v in by_disc.values())
    earned = sum(v[1] for v in by_disc.values())

    def fmt(x):
        return f"{x:.1f}".rstrip("0").rstrip(".") if x else "0"

    def rows(tab):
        out = [[k, fmt(v[0]), fmt(v[1]), fmt(v[0] - v[1]), f"{(v[1] / v[0] * 100 if v[0] else 0):.0f} %"] for k, v in sorted(tab.items())]
        if out:
            out.append([t["total"], fmt(base), fmt(earned), fmt(base - earned), f"{(earned / base * 100 if base else 0):.0f} %"])
        return out

    cols = [[t["discipline"], 0.32], [t["hh_base"], 0.17], [t["hh_earned"], 0.19], [t["hh_left"], 0.17], [t["pct"], 0.15]]
    notes = [t["effort.nohours"], t["effort.nocost"]] + ([] if base else [t["effort.nobase"]])
    blocks = [header_kv(c, t, with_phase=False),
              {"type": "h", "text": t["effort.by_disc"]}, table(cols, rows(by_disc), t["effort.nobase"]),
              {"type": "h", "text": t["effort.by_pkg"]}, table([[t["package"], 0.32]] + cols[1:], rows(by_pkg), t["effort.nobase"]),
              {"type": "h", "text": t["effort.remaining"]},
              table([[t["discipline"], 0.34], [t["hh_earned"], 0.22], [t["hh_left"], 0.22], [t["hh_total"], 0.22]],
                    [[k, fmt(v[1]), fmt(v[0] - v[1]), fmt(v[0])] for k, v in sorted(by_disc.items())], t["effort.nobase"]),
              {"type": "h", "text": t["effort.notes"]}, {"type": "bullets", "items": notes}]
    summ = f"{t['hh_base']}: {fmt(base)} · {t['hh_earned']}: {fmt(earned)} · {t['hh_left']}: {fmt(base - earned)}"
    return {"title": "INFORME DE ESFUERZO" if c["lang"] == "es" else "EFFORT REPORT", "summary": summ, "blocks": blocks,
            "snapshot": {"ranks": a["ranks"], "risks_high": len(a["high"])}}


# ---------------------------------------------------------------- D15 change report
def change_report(c: dict, prev: Optional[dict]) -> dict:
    t = T[c["lang"]]
    a = assess(c)
    lab = c["label"]
    acc: Dict[str, int] = {}
    per: Dict[str, int] = {}
    for r in c["rfc"]:
        k = r["status"]
        acc[k] = acc.get(k, 0) + 1
        when = r.get("opened") if k in ("open", "evaluated") else (r.get("decided_on") or r.get("opened"))
        if in_period(c, when):
            per[k] = per.get(k, 0) + 1
    order = ["open", "evaluated", "approved", "rejected", "deferred", "implemented", "closed"]
    sums = [[t["st." + k], str(per.get(k, 0)), str(acc.get(k, 0))] for k in order]
    sums.append([t["total"], str(sum(per.values())), str(len(c["rfc"]))])

    def sel(*keys):
        return [r for r in c["rfc"] if r["status"] in keys]

    concl = [f"{len(c['rfc'])} rfc / {len(sel('approved', 'implemented'))} {t['st.approved'].lower()}"] if c["rfc"] else [t["empty.changes"]]
    blocks = [header_kv(c, t, with_phase=False),
              {"type": "h", "text": t["chg.summary"]}, table([[t["chg.status"], 0.5], [t["chg.period"], 0.25], [t["chg.acc"], 0.25]], sums, ""),
              {"type": "h", "text": t["chg.approved"]},
              table([["rfc", 0.12], [t["title_col"], 0.38], [t["category"], 0.16], ["DEC", 0.12], [t["owner"], 0.22]],
                    [[r["id"], r["title"], lab("change", "category", r.get("category")), r.get("decision_ref", ""), r.get("owner", "")] for r in sel("approved", "implemented")], t["empty.changes"]),
              {"type": "h", "text": t["chg.rejected"]},
              table([["rfc", 0.12], [t["title_col"], 0.36], [t["decision"], 0.16], ["DEC", 0.12], [t["justification"], 0.24]],
                    [[r["id"], r["title"], lab("change", "status", r["status"]), r.get("decision_ref", ""), r.get("justification", "")] for r in sel("rejected", "deferred")], t["empty.changes"]),
              {"type": "h", "text": t["chg.eval"]},
              table([["rfc", 0.12], [t["title_col"], 0.46], [t["opened"], 0.2], [t["owner"], 0.22]],
                    [[r["id"], r["title"], fmt_date(r.get("opened")), r.get("owner", "")] for r in sel("open", "evaluated")], t["empty.changes"]),
              {"type": "h", "text": t["chg.conclusions"]}, {"type": "bullets", "items": concl}, {"type": "p", "text": t["chg.src"]}]
    return {"title": "INFORME DE CAMBIOS" if c["lang"] == "es" else "CHANGE REPORT", "summary": concl[0], "blocks": blocks,
            "snapshot": {"ranks": a["ranks"], "risks_high": len(a["high"])}}


BUILDERS = {"status": status_report, "progress": progress_report, "risks": risk_report, "effort": effort_report, "changes": change_report}


# ---------------------------------------------------------------- renderings
def to_markdown(doc: dict) -> str:
    out = [f"# {doc['title']} — {doc['subtitle']}", ""]
    for b in doc["blocks"]:
        k = b["type"]
        if k == "kv":
            out += [f"**{label}:** {value}  " for label, value in b["rows"]] + [""]
        elif k == "h":
            out += [f"### {b['text']}", ""]
        elif k == "p":
            out += [b["text"], ""]
        elif k == "bullets":
            out += [f"- {i}" for i in b["items"]] + [""]
        elif k == "table":
            if not b["rows"]:
                out += [f"_{b['empty']}_" if b.get("empty") else "", ""]
                continue
            esc = lambda x: str(x).replace("|", "\\|").replace("\n", " ")
            out += ["| " + " | ".join(esc(c[0]) for c in b["columns"]) + " |", "|" + "|".join("---" for _ in b["columns"]) + "|"]
            out += ["| " + " | ".join(esc(x) for x in r) + " |" for r in b["rows"]] + [""]
    return "\n".join(out).rstrip("\n") + "\n"
