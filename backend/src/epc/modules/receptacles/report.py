"""The socket-outlet report of a sheet: what each room needs and has, the load and the circuits, the checks and what was estimated and how sure it is, as the structure the engine's PDF exporter draws."""
from typing import Dict, List

SURE = 0.6                                         # under this confidence an estimate is listed as something to confirm

TEXT: Dict[str, Dict[str, str]] = {
    "en": {"title": "Socket outlets report", "project": "Project", "sheet": "Sheet", "calculated": "Calculated on", "by": "Calculated by", "engine": "Engine", "summary": "Summary",
           "totals": "{rooms} room(s), {outlets} outlet(s) of {required} needed, {load} VA installed.", "rooms": "Rooms", "room": "Room", "use": "Use", "outlet": "Outlet", "count": "Qty", "load": "Load (VA)",
           "circuits": "Circuits", "family": "Family", "verdict": "Result", "meets": "complies", "fails": "does not comply", "checks": "Checks", "assumptions": "Assumptions and estimates",
           "confirm": "to confirm", "left_out": "Rooms left out", "warnings": "Warnings", "typical": "The outlets per use and the mounting heights are typical values until the norms review confirms them: confirm them before issuing.",
           "company": "Issuer", "client": "Client", "drawn_by": "Drawn by", "checked_by": "Checked by", "approved_by": "Approved by", "footer": "Socket outlets", "page": "Page {n} of {total}"},
    "es": {"title": "Memoria de tomacorrientes", "project": "Proyecto", "sheet": "Hoja", "calculated": "Calculado el", "by": "Calculado por", "engine": "Motor", "summary": "Resumen",
           "totals": "{rooms} ambiente(s), {outlets} tomacorriente(s) de {required} necesarios, {load} VA instalados.", "rooms": "Ambientes", "room": "Ambiente", "use": "Uso", "outlet": "Tomacorriente", "count": "Cant.",
           "load": "Carga (VA)", "circuits": "Circuitos", "family": "Familia", "verdict": "Resultado", "meets": "cumple", "fails": "no cumple", "checks": "Verificaciones", "assumptions": "Supuestos y estimaciones",
           "confirm": "a confirmar", "left_out": "Ambientes omitidos", "warnings": "Avisos", "typical": "La cantidad por uso y las alturas de montaje son valores típicos hasta que la revisión de normas los confirme: confírmalos antes de emitir.",
           "company": "Emisora", "client": "Cliente", "drawn_by": "Dibujó", "checked_by": "Revisó", "approved_by": "Aprobó", "footer": "Tomacorrientes", "page": "Página {n} de {total}"},
}
TITLEBLOCK = ("company", "client", "drawn_by", "checked_by", "approved_by")


def _row(r: dict, names: Dict[str, str], uses: Dict[str, str], t: Dict[str, str]) -> List[str]:
    ok = all(c["ok"] for c in r["checks"])
    return [r["name"], uses.get(r["use"], r["use"]), names.get(r["receptacle"], r["receptacle"] or "–"), f"{r['installed']} / {r['required']}", r["family"], f"{r['load_va']:g}", str(r["circuits_min"]), t["meets"] if ok else t["fails"]]


def _assumptions(rooms: List[dict], t: Dict[str, str]) -> List[str]:
    """How many outlets each room got and why, flagging what rests on a typical value."""
    return [f"{r['name']}: {r['estimate']['reason']} ({r['estimate']['source']})" + (f" [{t['confirm']}]" if r["estimate"]["confidence"] < SURE else "") for r in rooms]


def _head(stored: dict, project: dict, t: Dict[str, str], engine_version: str, titleblock: Dict[str, str]) -> List[dict]:
    rooms = stored["result"]["rooms"]
    counts = stored["result"]["counts"]
    people = [[t[k], titleblock[k]] for k in TITLEBLOCK if titleblock.get(k)]
    return [{"type": "kv", "rows": [[t["project"], f"{project.get('code', '')} {project.get('name', '')}".strip()], *people, [t["sheet"], stored["sheet"]], [t["calculated"], stored["saved_at"]],
                                    [t["by"], stored.get("saved_by") or "–"], [t["engine"], f"epc_receptacles {engine_version}"]]},
            {"type": "h", "text": t["summary"]},
            {"type": "p", "text": t["totals"].format(rooms=len(rooms), outlets=counts["outlets"], required=counts["required"], load=f"{sum(r['load_va'] for r in rooms):g}")}]


def document(stored: dict, project: dict, lang: str, names: Dict[str, str], uses: Dict[str, str], engine_version: str, titleblock: Dict[str, str]) -> dict:
    """The report of a stored study: `stored` is what `study.save` keeps; `names` are the outlets and `uses` the uses of the rooms in the language asked."""
    t = TEXT["es" if lang == "es" else "en"]
    rooms = stored["result"]["rooms"]
    blocks = _head(stored, project, t, engine_version, titleblock) + [
        {"type": "h", "text": t["rooms"]},
        {"type": "table", "columns": [[t["room"], 0.17], [t["use"], 0.15], [t["outlet"], 0.22], [t["count"], 0.08], [t["family"], 0.08], [t["load"], 0.1], [t["circuits"], 0.08], [t["verdict"], 0.12]],
         "rows": [_row(r, names, uses, t) for r in rooms]},
        {"type": "h", "text": t["assumptions"]}, {"type": "bullets", "items": _assumptions(rooms, t)}, {"type": "p", "text": t["typical"]}]
    problems = [f"{r['name']}: {c['message']}" for r in rooms for c in r["checks"] if not c["ok"]]
    if problems:
        blocks += [{"type": "h", "text": t["checks"]}, {"type": "bullets", "items": problems}]
    if stored.get("skipped"):
        blocks += [{"type": "h", "text": t["left_out"]}, {"type": "bullets", "items": [f"{s['name'] or s['id']}: {s['reason']}" for s in stored["skipped"]]}]
    if stored.get("warnings"):
        blocks += [{"type": "h", "text": t["warnings"]}, {"type": "bullets", "items": stored["warnings"]}]
    return {"title": t["title"], "subtitle": stored["sheet"], "footer": f"{t['footer']} · {project.get('code', '')}", "page_label": t["page"], "blocks": blocks}
