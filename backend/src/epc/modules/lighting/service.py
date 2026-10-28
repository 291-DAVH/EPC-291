"""Lighting: what the editor needs to put luminaires in the rooms of a sheet.

The calculation takes the rooms as the editor has them (in the request, as the design of runs and circuits does), asks `epc_lighting` in this process and answers with a proposal:
the engine's result and the position of every luminaire as a point of the view. Nothing is saved by calculating. The catalogue of luminaires has three levels: the factory's (in
the engine), the company's and the project's; each level stores only what it changes.
"""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from epc.core.errors import Invalid
from epc.modules.identity import public as identity
from epc.modules.lighting import geometry, repository
from epc.modules.lighting.models import CalcIn, PlanRoom, RoomParams
from epc.modules.projects import public as projects

PARENT = {"company": "factory", "project": "company"}
MAX_AREA_M2 = 1.0e6                                 # an exterior area larger than a square kilometre is a wrong scale or a stray point
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


def label(entry: dict, lang: str) -> str:
    """The name of a luminaire of the catalogue in the language asked."""
    return _pick(entry.get("name"), lang)


def engine_version() -> str:
    return _engine()[0].__version__


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
    """Why a room is left out of the calculation, or None when it can be calculated. An exterior area needs its target (there is no table of typical ones yet) and a luminaire for exterior use."""
    if params is None or not params.luminaire:
        return "no luminaire chosen"
    if not (params.target_lux if params.exterior else params.activity or params.target_lux):
        return "an exterior area needs its target illuminance" if params.exterior else "no activity or target illuminance"
    if params.luminaire not in luminaires:
        return f"luminaire '{params.luminaire}' is not in the catalogue"
    if (luminaires[params.luminaire].get("kind", "interior") == "exterior") != params.exterior:
        return "the luminaire is for exterior use: choose an interior one" if not params.exterior else "the luminaire is for interior use: choose an exterior one"
    return None


def _engine_room(room: PlanRoom, params: RoomParams, rect: geometry.Rect, k: float, default_height: float) -> dict:
    length, width = geometry.to_engine(rect, k)
    body = {"id": room.id, "name": room.name or room.id, "width_m": width, "length_m": length, "height_m": params.height_m or default_height, "luminaire": params.luminaire, "method": params.method}
    for key in ("activity", "target_lux", "coefficient_of_utilisation", "work_plane_height_m", "operating_hours_per_year", "reflectances", "ugr_calculated"):
        value = getattr(params, key)
        if value not in (None, ""):
            body[key] = value
    return body


def _engine_area(room: PlanRoom, params: RoomParams, k: float) -> dict:
    body = {"id": room.id, "name": room.name or room.id, "area_m2": round(geometry.area_m2(room.points, k), 4), "luminaire": params.luminaire, "target_lux": params.target_lux, "enclosure": params.enclosure}
    for key in ("beam_utilisation", "maintenance_factor", "operating_hours_per_year"):
        value = getattr(params, key)
        if value is not None:
            body[key] = value
    return body


def _engine_emergency(room: PlanRoom, params: RoomParams, rect: geometry.Rect, k: float, default_height: float) -> dict:
    length, width = geometry.to_engine(rect, k)
    body = {"id": room.id, "name": room.name or room.id, "width_m": width, "length_m": length, "height_m": params.height_m or default_height, "luminaire": params.emergency_luminaire}
    if params.emergency_e_min_lux is not None:
        body["e_min_lux"] = params.emergency_e_min_lux
    return body


def _document(body: CalcIn, prepared: "_Prepared", luminaires: Dict[str, dict]) -> dict:
    _, catalogue = _engine()
    return {"schema_version": "1.0", "luminaires": [catalogue.as_document(lid, luminaires[lid], body.lang) for lid in prepared.used()], "rooms": prepared.rooms, "areas": prepared.areas, "emergency": prepared.emergency}


def _placements(items: List[dict], rects: Dict[str, geometry.Rect], k: float, outlines: Dict[str, list]) -> tuple:
    """The luminaires of each room (or its emergency luminaires) as points of the view (the engine's tag is kept to follow them back), and a warning for each room whose outline is not its rectangle
    and left some of them outside."""
    out, warnings = {}, []
    for room in items:
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


def fingerprint(project_dir: Path, body: CalcIn) -> str:
    """The fingerprint a calculation of this request would have, without calculating (empty when the sheet has no usable scale)."""
    try:
        k = geometry.metres_per_unit(body.sheet.scale)
    except geometry.GeometryError:
        return ""
    luminaires = effective(project_dir)
    return _fingerprint(body, luminaires, _prepare(body, k, luminaires).used())


@dataclass
class _Prepared:
    """What the sheet gives the engine: its rooms and exterior areas, the rectangle of each room, what was left out and the warnings of the geometry."""
    rooms: List[dict] = field(default_factory=list)
    areas: List[dict] = field(default_factory=list)
    emergency: List[dict] = field(default_factory=list)
    rects: Dict[str, geometry.Rect] = field(default_factory=dict)
    skipped: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def used(self) -> List[str]:
        return sorted({x["luminaire"] for x in self.rooms + self.areas + self.emergency})


def _add_room(out: _Prepared, room: PlanRoom, params: RoomParams, k: float, default_height: float, luminaires: Dict[str, dict]) -> None:
    try:
        rect = geometry.rectangle(room.points)
    except geometry.GeometryError as exc:
        out.skipped.append(_skip(room, str(exc)))
        return
    if max(geometry.to_engine(rect, k)) > MAX_ROOM_M:
        out.skipped.append(_skip(room, f"the room is longer than {MAX_ROOM_M:g} m: check the scale of the sheet and the outline"))
        return
    if not rect.exact:
        out.warnings.append(f"room '{room.name or room.id}' is not a rectangle with its sides along the axes: its bounding box was used")
    out.rects[room.id] = rect
    out.rooms.append(_engine_room(room, params, rect, k, default_height))
    _add_emergency(out, room, params, rect, k, default_height, luminaires)


def _add_emergency(out: _Prepared, room: PlanRoom, params: RoomParams, rect: geometry.Rect, k: float, default_height: float, luminaires: Dict[str, dict]) -> None:
    if not params.emergency_luminaire:
        return
    chosen = luminaires.get(params.emergency_luminaire)
    if chosen is None or chosen.get("kind", "interior") != "interior":
        out.warnings.append(f"room '{room.name or room.id}': the emergency luminaire '{params.emergency_luminaire}' is not an interior luminaire of the catalogue: no emergency lighting was calculated")
        return
    out.emergency.append(_engine_emergency(room, params, rect, k, default_height))


def _add_area(out: _Prepared, room: PlanRoom, params: RoomParams, k: float) -> None:
    area = geometry.area_m2(room.points, k)
    if area <= 0:
        out.skipped.append(_skip(room, "the outline has no area"))
    elif area > MAX_AREA_M2:
        out.skipped.append(_skip(room, f"the area is larger than {MAX_AREA_M2:g} m²: check the scale of the sheet and the outline"))
    else:
        out.areas.append(_engine_area(room, params, k))


def _prepare(body: CalcIn, k: float, luminaires: Dict[str, dict]) -> _Prepared:
    out = _Prepared()
    for room in body.sheet.rooms:
        params = body.rooms.get(room.id)
        why = _calculable(room, params, luminaires)
        if why:
            out.skipped.append(_skip(room, why))
        elif params.exterior:
            _add_area(out, room, params, k)
        else:
            _add_room(out, room, params, k, body.options.default_height_m, luminaires)
    return out


def _grid_map(room: dict, rect: geometry.Rect, k: float, outline: Optional[list]) -> Optional[dict]:
    """The illuminance of the cells of a room as a map over the plan: where its first cell is (view units), the size of a cell, and the lux of each (None where the cell is outside the outline)."""
    grid = room["points"].get("grid")
    if not grid:
        return None
    dx, dy = grid["dx_m"] / k, grid["dy_m"] / k
    values = grid["maintained_lux"]
    if outline is not None:
        centre = lambda n: (rect.x0 + (n % grid["nx"] + 0.5) * dx, rect.y0 + (n // grid["nx"] + 0.5) * dy)            # noqa: E731
        values = [v if geometry.contains(outline, *centre(n)) else None for n, v in enumerate(values)]
    seen = [v for v in values if v is not None]
    return {"x0": rect.x0, "y0": rect.y0, "dx": round(dx, 4), "dy": round(dy, 4), "nx": grid["nx"], "ny": grid["ny"], "values": values, "min": min(seen, default=0.0), "max": max(seen, default=0.0)}


def _maps(result: dict, rects: Dict[str, geometry.Rect], k: float, outlines: Dict[str, list]) -> Dict[str, dict]:
    made = {r["id"]: _grid_map(r, rects[r["id"]], k, outlines.get(r["id"])) for r in result["rooms"]}
    return {rid: m for rid, m in made.items() if m}


def _options(body: CalcIn):
    engine, _ = _engine()
    o = body.options
    return engine.Options(enforce_spacing=o.enforce_spacing, spacing_basis=o.spacing_basis, compute_points=o.compute_points or o.map, point_step_m=o.point_step_m, return_grid=o.map)


def _run(body: CalcIn, prepared: _Prepared, luminaires: Dict[str, dict]) -> dict:
    engine, _ = _engine()
    try:
        return engine.run(_document(body, prepared, luminaires), _options(body)).as_dict()
    except engine.LightingError as exc:
        raise Invalid({"lighting": str(exc)})


def calc(project_dir: Path, body: CalcIn) -> dict:
    """Luminaires for the rooms and floodlights for the exterior areas of a sheet. Answers `{result, placements, maps, rooms, areas, skipped, warnings, fingerprint}`; `result` is the engine's (None when nothing could be
    calculated), `placements` are the luminaires of each room in view units and `maps` (only when asked) the illuminance of the cells of each room."""
    try:
        k = geometry.metres_per_unit(body.sheet.scale)
    except geometry.GeometryError as exc:
        raise Invalid({"scale": str(exc)})
    luminaires = effective(project_dir)
    prepared = _prepare(body, k, luminaires)
    if not (prepared.rooms or prepared.areas):
        return {"result": None, "placements": {}, "emergency_placements": {}, "maps": {}, "rooms": [], "areas": [], "skipped": prepared.skipped, "fingerprint": "",
                "warnings": prepared.warnings + ["nothing could be calculated: give each room a luminaire and an activity or a target"]}
    result = _run(body, prepared, luminaires)
    outlines = {r.id: r.points for r in body.sheet.rooms if r.id in prepared.rects and not prepared.rects[r.id].exact}
    placements, outside = _placements(result["rooms"], prepared.rects, k, outlines)
    escape, escape_outside = _placements(result["emergency"], prepared.rects, k, outlines)
    shown = [{"id": r["id"], "name": r["name"], "length_m": r["length_m"], "width_m": r["width_m"], "exact": prepared.rects[r["id"]].exact, "corner": geometry.corner(prepared.rects[r["id"]])} for r in prepared.rooms]
    return {"result": result, "placements": placements, "emergency_placements": escape, "maps": _maps(result, prepared.rects, k, outlines) if body.options.map else {}, "rooms": shown,
            "areas": [{"id": a["id"], "name": a["name"], "area_m2": a["area_m2"]} for a in prepared.areas], "skipped": prepared.skipped,
            "warnings": prepared.warnings + list(result["warnings"]) + outside + escape_outside, "fingerprint": _fingerprint(body, luminaires, prepared.used())}
