"""The lighting calculation report of a sheet: what was asked, what each room got and what was estimated with how much confidence, as the structure the engine's PDF exporter draws."""
from typing import Dict, List

SURE = 0.6                                         # under this confidence an estimate is listed as something to confirm

TEXT: Dict[str, Dict[str, str]] = {
    "en": {"title": "Lighting calculation report", "project": "Project", "sheet": "Sheet", "calculated": "Calculated on", "by": "Calculated by", "engine": "Engine", "summary": "Summary",
           "totals": "{rooms} room(s), {luminaires} luminaire(s), {power} W installed.", "rooms": "Rooms", "room": "Room", "activity": "Activity", "luminaire": "Luminaire", "count": "Qty",
           "average": "Avg (lx)", "target": "Target (lx)", "verdict": "Result", "density": "W/m²", "areas": "Exterior areas", "floodlights": "Floodlights", "power": "Power (W)", "meets": "meets", "fails": "does not meet", "none": "No room was calculated",
           "assumptions": "Assumptions and estimates", "est_target": "target", "est_beam": "beam utilisation", "est_cu": "utilisation factor", "est_maintenance": "maintenance factor", "confirm": "confirm",
           "left_out": "Rooms left out", "warnings": "Warnings", "illustrative": "The luminaires of this study are typical values, not a maker's: replace them with the ones of the project before issuing.",
           "footer": "Lighting calculation", "page": "Page {n} of {total}"},
    "es": {"title": "Memoria de cálculo de iluminación", "project": "Proyecto", "sheet": "Hoja", "calculated": "Calculado el", "by": "Calculado por", "engine": "Motor", "summary": "Resumen",
           "totals": "{rooms} ambiente(s), {luminaires} luminaria(s), {power} W instalados.", "rooms": "Ambientes", "room": "Ambiente", "activity": "Actividad", "luminaire": "Luminaria", "count": "Cant.",
           "average": "Prom. (lx)", "target": "Meta (lx)", "verdict": "Resultado", "density": "W/m²", "areas": "Áreas exteriores", "floodlights": "Proyectores", "power": "Potencia (W)", "meets": "cumple", "fails": "no cumple", "none": "No se calculó ningún ambiente",
           "assumptions": "Supuestos y estimaciones", "est_target": "la meta", "est_beam": "el aprovechamiento del haz", "est_cu": "el factor de utilización", "est_maintenance": "el factor de mantenimiento", "confirm": "confirmar",
           "left_out": "Ambientes omitidos", "warnings": "Avisos", "illustrative": "Las luminarias de este estudio son valores típicos, no de un fabricante: reemplázalas por las del proyecto antes de emitir.",
           "footer": "Cálculo de iluminación", "page": "Página {n} de {total}"},
}


def _number(value, digits: int = 0) -> str:
    return "–" if value is None else f"{value:.{digits}f}"


def _row(r: dict, rooms: Dict[str, dict], t: Dict[str, str], luminaire_names: Dict[str, str]) -> List[str]:
    asked = rooms.get(r["id"], {})
    v, layout = r["verification"], r["layout"]
    return [r["name"], asked.get("activity") or "–", luminaire_names.get(asked.get("luminaire", ""), asked.get("luminaire") or "–"), f"{layout['installed']} / {layout['required']}",
            _number(v["average_lux"]), _number(v["target_lux"]), t["meets"] if v["complies"] else t["fails"], _number(r["energy"].get("power_density_w_m2"), 1)]


def _assumptions(result_rooms: List[dict], t: Dict[str, str]) -> List[str]:
    """The target of each room with where it comes from, and the factors that were estimated with little confidence."""
    lines = []
    for r in result_rooms:
        for key, est in (("est_target", r["target"]), ("est_cu", r["factors"]["cu"]), ("est_maintenance", r["factors"]["maintenance"])):
            if key == "est_target" or est["confidence"] < SURE:
                flag = f" [{t['confirm']}]" if est["confidence"] < SURE else ""
                lines.append(f"{r['name']}: {t[key]} = {est['value']:g} ({est['reason']}){flag}")
    return lines


def _area_row(a: dict, areas: Dict[str, dict], t: Dict[str, str], luminaire_names: Dict[str, str]) -> List[str]:
    v = a["verification"]
    return [a["name"], luminaire_names.get(areas.get(a["id"], {}).get("luminaire", ""), "–"), _number(a["area_m2"]), str(a["flux"]["luminaires_required"]), _number(v["average_lux"]), _number(v["target_lux"]),
            t["meets"] if v["complies"] else t["fails"], _number(a["energy"].get("installed_power_w"))]


def _area_assumptions(result_areas: List[dict], t: Dict[str, str]) -> List[str]:
    lines = []
    for a in result_areas:
        for key, est in (("est_target", a["target"]), ("est_beam", a["factors"]["beam_utilisation"])):
            if key == "est_target" or est["confidence"] < SURE:
                flag = f" [{t['confirm']}]" if est["confidence"] < SURE else ""
                lines.append(f"{a['name']}: {t[key]} = {est['value']:g} ({est['reason']}){flag}")
    return lines


def _head(stored: dict, project: dict, t: Dict[str, str], engine_version: str) -> List[dict]:
    result = stored["result"]
    rooms, areas = result["rooms"], result.get("areas", [])
    power = sum(x["energy"].get("installed_power_w") or 0 for x in rooms + areas)
    luminaires = sum(r["layout"]["installed"] for r in rooms) + sum(a["flux"]["luminaires_required"] for a in areas)
    return [{"type": "kv", "rows": [[t["project"], f"{project.get('code', '')} {project.get('name', '')}".strip()], [t["sheet"], stored["sheet"]], [t["calculated"], stored["saved_at"]],
                                    [t["by"], stored.get("saved_by") or "–"], [t["engine"], f"epc_lighting {engine_version}"]]},
            {"type": "h", "text": t["summary"]},
            {"type": "p", "text": t["totals"].format(rooms=len(rooms) + len(areas), luminaires=luminaires, power=_number(power))}]


def _tables(stored: dict, t: Dict[str, str], luminaire_names: Dict[str, str]) -> List[dict]:
    asked = stored["input"]["rooms"]
    rooms, areas = stored["result"]["rooms"], stored["result"].get("areas", [])
    blocks = [{"type": "h", "text": t["rooms"]},
              {"type": "table", "columns": [[t["room"], 0.15], [t["activity"], 0.19], [t["luminaire"], 0.2], [t["count"], 0.1], [t["average"], 0.11], [t["target"], 0.09], [t["verdict"], 0.1], [t["density"], 0.06]],
               "rows": [_row(r, asked, t, luminaire_names) for r in rooms], "empty": t["none"]}]
    if areas:
        blocks += [{"type": "h", "text": t["areas"]},
                   {"type": "table", "columns": [[t["room"], 0.2], [t["luminaire"], 0.24], ["m²", 0.1], [t["floodlights"], 0.12], [t["average"], 0.1], [t["target"], 0.08], [t["verdict"], 0.1], [t["power"], 0.06]],
                    "rows": [_area_row(a, asked, t, luminaire_names) for a in areas], "empty": t["none"]}]
    return blocks


def _notes(stored: dict, t: Dict[str, str], illustrative: bool) -> List[dict]:
    rooms, areas = stored["result"]["rooms"], stored["result"].get("areas", [])
    blocks: List[dict] = [{"type": "h", "text": t["assumptions"]}, {"type": "bullets", "items": _assumptions(rooms, t) + _area_assumptions(areas, t)}]
    if illustrative:
        blocks.append({"type": "p", "text": t["illustrative"]})
    if stored["skipped"]:
        blocks += [{"type": "h", "text": t["left_out"]}, {"type": "bullets", "items": [f"{s['name'] or s['id']}: {s['reason']}" for s in stored["skipped"]]}]
    if stored["warnings"]:
        blocks += [{"type": "h", "text": t["warnings"]}, {"type": "bullets", "items": list(stored["warnings"])}]
    return blocks


def document(stored: dict, project: dict, lang: str, luminaire_names: Dict[str, str], illustrative: bool, engine_version: str) -> dict:
    """The report of a stored study: `stored` is what `study.save` keeps; `project` has `name` and `code`; `luminaire_names` and `illustrative` come from the catalogue in force."""
    t = TEXT["es" if lang == "es" else "en"]
    blocks = _head(stored, project, t, engine_version) + _tables(stored, t, luminaire_names) + _notes(stored, t, illustrative)
    return {"title": t["title"], "subtitle": stored["sheet"], "footer": f"{t['footer']} · {project.get('code', '')}", "page_label": t["page"], "blocks": blocks}
