"""Lighting: what the editor needs to put luminaires in the rooms of a sheet.

The calculation takes the rooms as the editor has them (in the request, as the design of runs and circuits does), asks `epc_lighting` in this process and answers with a proposal:
the engine's result and the position of every luminaire as a point of the view. Nothing is saved by calculating. The catalogue of luminaires has three levels: the factory's (in
the engine), the company's and the project's; each level stores only what it changes.
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from epc.core.errors import Invalid
from epc.modules.identity import public as identity
from epc.modules.lighting import geometry, repository
from epc.modules.lighting.models import CalcIn, PlanRoom, RoomParams
from epc.modules.projects import public as projects

PARENT = {"company": "factory", "project": "company"}
MAX_ROOM_M = 1000.0                                  # a room longer than this is a wrong scale or a stray point, not a room
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


def _engine():
    import epc_lighting
    from epc_lighting import catalogue
    return epc_lighting, catalogue


# ---------------------------------------------------------------- the catalogue of luminaires
def _org(level: str, project_dir: Optional[Path]) -> str:
    """The organization the company level belongs to: the project's, or the one the caller works in (a company-level request needs one)."""
    slug = projects.read_meta(project_dir).get("org", "") if project_dir is not None else identity.active_org_slug()
    if level == "company" and not slug:
        raise Invalid({"organization": "this level belongs to an organization: work inside one"})
    return slug


def _levels(project_dir: Optional[Path]) -> List[tuple]:
    """The levels that apply to a project, in order of authority, each with its file: (level, path)."""
    org = projects.read_meta(project_dir).get("org", "") if project_dir is not None else ""
    return ([("company", repository.company_file(org))] if org else []) + ([("project", repository.project_file(project_dir))] if project_dir is not None else [])


def _chain(level: str, project_dir: Optional[Path]) -> List[Path]:
    """The files that apply up to and including the level."""
    if level == "company":
        return [repository.company_file(_org(level, project_dir))]
    return [path for _, path in _levels(project_dir)]


def _layers(files: List[Path]) -> List[dict]:
    return [repository.read(f) for f in files]


def _resolve(project_dir: Optional[Path]) -> tuple:
    """The luminaires in force for a project and, for each, the level that last set it (one read of the files)."""
    _, catalogue = _engine()
    levels = _levels(project_dir)
    layers = [repository.read(path) for _, path in levels]
    origin = {lid: "factory" for lid in catalogue.defaults()}
    for (level, _), layer in zip(levels, layers):
        for lid, entry in layer.items():
            if entry.get("disabled"):
                origin.pop(lid, None)
            else:
                origin[lid] = level
    return catalogue.merge(layers), origin


def effective(project_dir: Optional[Path] = None) -> Dict[str, dict]:
    """The luminaires in force for a project: the factory's with the company's and the project's changes on top."""
    return _resolve(project_dir)[0]


def luminaires_view(level: str, project_dir: Optional[Path] = None) -> dict:
    """The catalogue as a level sees it, what it changed itself and the level it inherits from."""
    _, catalogue = _engine()
    files = _chain(level, project_dir)
    return {"luminaires": catalogue.merge(_layers(files)), "own": repository.read(files[-1]), "default": catalogue.merge(_layers(files[:-1])), "inherits": PARENT[level]}


def _differs(below: Dict[str, dict], own: Dict[str, dict]) -> Dict[str, dict]:
    """Only what a level changes with respect to the levels under it: an entry equal to the one below is not a change, nor is removing what is not there."""
    kept = {}
    for lid, entry in own.items():
        if entry.get("disabled"):
            if lid in below:
                kept[lid] = {"disabled": True}
        elif entry != below.get(lid):
            kept[lid] = entry
    return kept


def luminaires_save(level: str, changes: Dict[str, dict], project_dir: Optional[Path] = None) -> dict:
    """Store the changes this level sent (by id); the rest of what the level had stays. An entry that is not valid is refused with what to correct."""
    _, catalogue = _engine()
    problems = [f"{lid}: the id is letters, digits, '_', '-' or '.', up to 64 characters" for lid in changes if not ID.match(lid)]
    problems += [p for lid, entry in changes.items() if not entry.get("disabled") for p in catalogue.check(lid, entry)]
    if problems:
        raise Invalid({"luminaires": problems})
    files = _chain(level, project_dir)
    below = catalogue.merge(_layers(files[:-1]))
    own = _differs(below, {**repository.read(files[-1]), **changes})
    repository.write(files[-1], own) if own else repository.delete(files[-1])
    _audit("luminaires_changed", level, project_dir, {"changed": sorted(own)})
    return luminaires_view(level, project_dir)


def luminaires_reset(level: str, project_dir: Optional[Path] = None) -> dict:
    repository.delete(_chain(level, project_dir)[-1])
    _audit("luminaires_reset", level, project_dir)
    return luminaires_view(level, project_dir)


def _audit(action: str, level: str, project_dir: Optional[Path], detail: Optional[dict] = None) -> None:
    org = _org(level, project_dir) if level == "company" else (projects.read_meta(project_dir).get("org", "") if project_dir is not None else "")
    target = f"company:{org}" if level == "company" else projects.project_id(project_dir)
    identity.audit_event(action, target=target, org_slug=org, detail=detail)


# ---------------------------------------------------------------- what the screens offer
def _pick(label: Any, lang: str) -> str:
    """A label in the language asked (the other one when it is missing)."""
    return (label.get(lang) or label.get("en") or "") if isinstance(label, dict) else str(label or "")


def _luminaire_rows(project_dir: Path, lang: str) -> List[dict]:
    entries, origin = _resolve(project_dir)
    return [{"id": lid, "name": _pick(e.get("name"), lang) or lid, "kind": e.get("kind", "interior"), "lamps": e.get("lamps", 1), "lamp_flux_lm": e.get("lamp_flux_lm"), "power_w": e.get("power_w"),
             "illustrative": bool(e.get("illustrative")), "level": origin.get(lid, "factory")} for lid, e in entries.items()]


def options(project_dir: Path, lang: str = "en") -> dict:
    """The choices of the lighting panel: activities (with their typical target and where it comes from), materials, systems, methods and the luminaires in force."""
    from epc_lighting.config import data
    return {
        "activities": [{"id": a["id"], "label": _pick(a["label"], lang), "em_lux": a["em_lux"], "ugr_l": a.get("ugr_l"), "ra": a.get("ra"), "source": a.get("source", "")} for a in data("levels")["activities"]],
        "materials": [{"id": k, "label": _pick(v["label"], lang), "range": v["range"]} for k, v in data("reflectances")["materials"].items()],
        "systems": [{"id": k, "label": _pick(v["label"], lang)} for k, v in data("lighting_systems")["systems"].items()],
        "methods": ["lumen", "zonal"],
        "luminaires": _luminaire_rows(project_dir, lang),
    }


# ---------------------------------------------------------------- the calculation
def _skip(room: PlanRoom, reason: str) -> dict:
    return {"id": room.id, "name": room.name, "reason": reason}


def _calculable(room: PlanRoom, params: Optional[RoomParams], luminaires: Dict[str, dict]) -> Optional[str]:
    """Why a room is left out of the calculation, or None when it can be calculated."""
    if params is None or not params.luminaire:
        return "no luminaire chosen"
    if not (params.activity or params.target_lux):
        return "no activity or target illuminance"
    if params.luminaire not in luminaires:
        return f"luminaire '{params.luminaire}' is not in the catalogue"
    return None


def _engine_room(room: PlanRoom, params: RoomParams, rect: geometry.Rect, k: float, default_height: float) -> dict:
    length, width = geometry.to_engine(rect, k)
    body = {"id": room.id, "name": room.name or room.id, "width_m": width, "length_m": length, "height_m": params.height_m or default_height, "luminaire": params.luminaire, "method": params.method}
    for key in ("activity", "target_lux", "coefficient_of_utilisation", "work_plane_height_m", "operating_hours_per_year", "reflectances"):
        value = getattr(params, key)
        if value not in (None, ""):
            body[key] = value
    return body


def _document(body: CalcIn, rooms: List[dict], used: List[str], luminaires: Dict[str, dict]) -> dict:
    _, catalogue = _engine()
    return {"schema_version": "1.0", "luminaires": [catalogue.as_document(lid, luminaires[lid], body.lang) for lid in used], "rooms": rooms}


def _placements(result: dict, rects: Dict[str, geometry.Rect], k: float, outlines: Dict[str, list]) -> tuple:
    """The luminaires of each room as points of the view (the engine's tag is kept to follow them back), and a warning for each room whose outline is not its rectangle and left some of them outside."""
    out, warnings = {}, []
    for room in result["rooms"]:
        points = []
        for p in room["layout"]["positions"]:
            x, y = geometry.to_view(rects[room["id"]], k, p["x_m"], p["y_m"])
            points.append({"tag": p["tag"], "x": x, "y": y, "z_m": p["z_m"]})
        outline = outlines.get(room["id"])
        kept = [p for p in points if outline is None or geometry.contains(outline, p["x"], p["y"])]
        if len(kept) < len(points):
            warnings.append(f"room '{room['name']}': {len(points) - len(kept)} of {len(points)} luminaires fall outside its outline and are not placed; the illuminance shown counts all of them")
        out[room["id"]] = kept
    return out, warnings


def _fingerprint(body: CalcIn, luminaires: Dict[str, dict], used: List[str]) -> str:
    """What a calculation was made from: the rooms, their parameters, the options and the luminaires used. A later change of any of them makes the study stale."""
    seen = {"sheet": body.sheet.model_dump(), "rooms": {k: v.model_dump() for k, v in sorted(body.rooms.items())}, "options": body.options.model_dump(), "luminaires": {lid: luminaires[lid] for lid in used}}
    return hashlib.sha256(json.dumps(seen, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _prepare(body: CalcIn, k: float, luminaires: Dict[str, dict]) -> tuple:
    """The engine's rooms, the rectangle of each, the rooms left out and the warnings of the geometry."""
    rooms, rects, skipped, warnings = [], {}, [], []
    for room in body.sheet.rooms:
        params = body.rooms.get(room.id)
        why = _calculable(room, params, luminaires)
        if why:
            skipped.append(_skip(room, why))
            continue
        try:
            rect = geometry.rectangle(room.points)
        except geometry.GeometryError as exc:
            skipped.append(_skip(room, str(exc)))
            continue
        if max(geometry.to_engine(rect, k)) > MAX_ROOM_M:
            skipped.append(_skip(room, f"the room is longer than {MAX_ROOM_M:g} m: check the scale of the sheet and the outline"))
            continue
        if not rect.exact:
            warnings.append(f"room '{room.name or room.id}' is not a rectangle with its sides along the axes: its bounding box was used")
        rects[room.id] = rect
        rooms.append(_engine_room(room, params, rect, k, body.options.default_height_m))
    return rooms, rects, skipped, warnings


def calc(project_dir: Path, body: CalcIn) -> dict:
    """Luminaires for the rooms of a sheet. Answers `{result, placements, rooms, skipped, warnings, fingerprint}`; `result` is the engine's (None when no room could be calculated)."""
    try:
        k = geometry.metres_per_unit(body.sheet.scale)
    except geometry.GeometryError as exc:
        raise Invalid({"scale": str(exc)})
    luminaires = effective(project_dir)
    rooms, rects, skipped, warnings = _prepare(body, k, luminaires)
    summary = {"skipped": skipped, "warnings": warnings, "fingerprint": ""}
    if not rooms:
        return {"result": None, "placements": {}, "rooms": [], **summary, "warnings": warnings + ["no room could be calculated: give each one a luminaire and an activity or a target"]}
    used = sorted({r["luminaire"] for r in rooms})
    engine, _ = _engine()
    options = engine.Options(enforce_spacing=body.options.enforce_spacing, spacing_basis=body.options.spacing_basis, compute_points=body.options.compute_points, point_step_m=body.options.point_step_m)
    try:
        result = engine.run(_document(body, rooms, used, luminaires), options).as_dict()
    except engine.LightingError as exc:
        raise Invalid({"lighting": str(exc)})
    shown = [{"id": r["id"], "name": r["name"], "length_m": r["length_m"], "width_m": r["width_m"], "exact": rects[r["id"]].exact, "corner": geometry.corner(rects[r["id"]])} for r in rooms]
    placements, outside = _placements(result, rects, k, {r.id: r.points for r in body.sheet.rooms if r.id in rects and not rects[r.id].exact})
    return {"result": result, "placements": placements, "rooms": shown, **summary, "warnings": warnings + list(result["warnings"]) + outside, "fingerprint": _fingerprint(body, luminaires, used)}
