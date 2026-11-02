"""Receptacles: what the editor needs to put socket outlets in the rooms of a sheet.

The calculation takes the rooms as the editor has them (in the request, like the lighting calculation), asks `epc_receptacles` in this process and answers with a proposal: the engine's
result and the position of every outlet as a point of the view. Nothing is saved by calculating. The catalogue of outlets has three levels: the factory's (in the engine), the company's
and the project's; each level stores only what it changes.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from epc.core.errors import Invalid
from epc.modules.identity import public as identity
from epc.modules.lighting import public as lighting
from epc.modules.projects import public as projects
from epc.modules.receptacles import repository
from epc.modules.receptacles.models import CalcIn, PlanRoomAlias, RoomParams

geometry = lighting.geometry

PARENT = {"company": "factory", "project": "company"}
MAX_ROOM_M = 1000.0                                  # a room longer than this is a wrong scale or a stray point, not a room
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
OUTLET_KINDS = ("TG", "TE")                          # the nodes of the plan that are socket outlets: general use and special use


def _engine():
    import epc_receptacles
    from epc_receptacles import catalogue
    return epc_receptacles, catalogue


# ---------------------------------------------------------------- the catalogue of outlets
def _org(level: str, project_dir: Optional[Path]) -> str:
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
    """The outlets in force for a project and, for each, the level that last set it."""
    _, catalogue = _engine()
    levels = _levels(project_dir)
    layers = [repository.read(path) for _, path in levels]
    origin = {rid: "factory" for rid in catalogue.defaults()}
    for (level, _), layer in zip(levels, layers):
        for rid, entry in layer.items():
            if entry.get("disabled"):
                origin.pop(rid, None)
            else:
                origin[rid] = level
    return catalogue.merge(layers), origin


def effective(project_dir: Optional[Path] = None) -> Dict[str, dict]:
    """The outlets in force for a project: the factory's with the company's and the project's changes on top."""
    return _resolve(project_dir)[0]


def receptacles_view(level: str, project_dir: Optional[Path] = None) -> dict:
    """The catalogue as a level sees it, what it changed itself and the level it inherits from."""
    _, catalogue = _engine()
    files = _chain(level, project_dir)
    return {"receptacles": catalogue.merge(_layers(files)), "own": repository.read(files[-1]), "default": catalogue.merge(_layers(files[:-1])), "inherits": PARENT[level]}


def _differs(below: Dict[str, dict], own: Dict[str, dict]) -> Dict[str, dict]:
    """Only what a level changes with respect to the levels under it: an entry equal to the one below is not a change, nor is removing what is not there."""
    kept = {}
    for rid, entry in own.items():
        if entry.get("disabled"):
            if rid in below:
                kept[rid] = {"disabled": True}
        elif entry != below.get(rid):
            kept[rid] = entry
    return kept


def receptacles_save(level: str, changes: Dict[str, dict], project_dir: Optional[Path] = None) -> dict:
    """Store the changes this level sent (by id); the rest of what the level had stays. An entry that is not valid is refused with what to correct."""
    _, catalogue = _engine()
    problems = [f"{rid}: the id is letters, digits, '_', '-' or '.', up to 64 characters" for rid in changes if not ID.match(rid)]
    problems += [p for rid, entry in changes.items() if not entry.get("disabled") for p in catalogue.check(rid, entry)]
    if problems:
        raise Invalid({"receptacles": problems})
    files = _chain(level, project_dir)
    below = catalogue.merge(_layers(files[:-1]))
    own = _differs(below, {**repository.read(files[-1]), **changes})
    repository.write(files[-1], own) if own else repository.delete(files[-1])
    _audit("receptacles_changed", level, project_dir, {"changed": sorted(own)})
    return receptacles_view(level, project_dir)


def receptacles_reset(level: str, project_dir: Optional[Path] = None) -> dict:
    repository.delete(_chain(level, project_dir)[-1])
    _audit("receptacles_reset", level, project_dir)
    return receptacles_view(level, project_dir)


def _audit(action: str, level: str, project_dir: Optional[Path], detail: Optional[dict] = None) -> None:
    org = _org(level, project_dir) if level == "company" else (projects.read_meta(project_dir).get("org", "") if project_dir is not None else "")
    target = f"company:{org}" if level == "company" else projects.project_id(project_dir)
    identity.audit_event(action, target=target, org_slug=org, detail=detail)


# ---------------------------------------------------------------- what the screens offer
def _pick(label: Any, lang: str) -> str:
    """A label in the language asked (the other one when it is missing)."""
    return (label.get(lang) or label.get("en") or "") if isinstance(label, dict) else str(label or "")


def _use_rows(lang: str) -> List[dict]:
    from epc_receptacles.config import data
    return [{"id": uid, "label": _pick(u["label"], lang), "basis": u["basis"], "per_m2": u.get("per_m2"), "per_m": u.get("per_m"), "min": u["min"], "family": u["family"], "wet": bool(u.get("wet")),
             "confidence": u["confidence"], "source": u["source"]} for uid, u in data("uses")["uses"].items()]


def _outlet_rows(project_dir: Path, lang: str) -> List[dict]:
    entries, origin = _resolve(project_dir)
    return [{"id": rid, "name": _pick(e.get("name"), lang) or rid, "kind": e.get("kind", "general"), "poles": e.get("poles"), "rated_a": e.get("rated_a"), "power_va": e.get("power_va"), "height_m": e.get("height_m"),
             "ip": e.get("ip", ""), "illustrative": bool(e.get("illustrative")), "level": origin.get(rid, "factory")} for rid, e in entries.items()]


def options(project_dir: Path, lang: str = "en") -> dict:
    """The choices of the receptacles panel: the uses of a room (with how many outlets each asks for and where that comes from), the outlets in force and the sections of the norm."""
    return {"uses": _use_rows(lang), "receptacles": _outlet_rows(project_dir, lang), "norms": ["771", "770"]}


# ---------------------------------------------------------------- the calculation
@dataclass
class _Prepared:
    """What the sheet gives the engine: its rooms, the rectangle of each, what was left out and the warnings of the geometry."""
    rooms: List[dict] = field(default_factory=list)
    rects: Dict[str, Any] = field(default_factory=dict)
    kinds: Dict[str, str] = field(default_factory=dict)          # the plan's kind of node for each room: TG or TE
    skipped: List[dict] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def _skip(room: PlanRoomAlias, reason: str) -> dict:
    return {"id": room.id, "name": room.name, "reason": reason}


def _drawn(nodes: list, outline: list, rect, k: float) -> List[dict]:
    """The outlets drawn inside an outline (nodes `TG` and `TE`) as positions of the engine: metres from the corner of the room."""
    found = []
    for n in nodes:
        if n.kind in OUTLET_KINDS and geometry.contains(outline, n.x, n.y):
            found.append({"x_m": round(min(max((n.x - rect.x0) * k, 0.0), rect.width_u * k), 4), "y_m": round(min(max((n.y - rect.y0) * k, 0.0), rect.height_u * k), 4), "tag": n.tag})
    return found


def _problem(room: PlanRoomAlias, params: Optional[RoomParams], outlets: Dict[str, dict]) -> Optional[str]:
    """Why a room is left out of the calculation, or None when it can be calculated."""
    from epc_receptacles.config import data
    if params is None or not params.use:
        return "no use chosen"
    if params.use not in data("uses")["uses"]:
        return f"'{params.use}' is not a known use"
    if params.receptacle and params.receptacle not in outlets:
        return f"outlet '{params.receptacle}' is not in the catalogue"
    return None


def _engine_room(room: PlanRoomAlias, params: RoomParams, rect, k: float, drawn: Optional[list]) -> dict:
    length, width = geometry.to_engine(rect, k)
    body = {"id": room.id, "name": room.name or room.id, "length_m": length, "width_m": width, "use": params.use}
    for key in ("receptacle", "count", "height_m", "norm", "wet"):
        value = getattr(params, key)
        if value not in (None, ""):
            body[key] = value
    if drawn:
        body["positions"] = drawn
    return body


def _prepare(body: CalcIn, k: float, outlets: Dict[str, dict]) -> _Prepared:
    out = _Prepared()
    nodes = body.sheet.nodes if body.options.use_drawn else None
    for room in body.sheet.rooms:
        params = body.rooms.get(room.id)
        why = _problem(room, params, outlets)
        if why:
            out.skipped.append(_skip(room, why))
            continue
        try:
            rect = geometry.rectangle(room.points)
        except geometry.GeometryError as exc:
            out.skipped.append(_skip(room, str(exc)))
            continue
        if max(geometry.to_engine(rect, k)) > MAX_ROOM_M:
            out.skipped.append(_skip(room, f"the room is longer than {MAX_ROOM_M:g} m: check the scale of the sheet and the outline"))
            continue
        drawn = _drawn(nodes, room.points, rect, k) if nodes is not None else None
        if drawn is not None and not drawn:
            out.skipped.append(_skip(room, "there are no outlets drawn in this room: apply the outlets to the plan first"))
            continue
        if not rect.exact:
            out.warnings.append(f"room '{room.name or room.id}' is not a rectangle with its sides along the axes: its bounding box was used")
        out.rects[room.id] = rect
        out.rooms.append(_engine_room(room, params, rect, k, drawn))
    return out


def _placements(rooms: List[dict], rects: Dict[str, Any], k: float, outlines: Dict[str, list]) -> tuple:
    """The outlets of each room as points of the view (the engine's tag is kept to follow them back), and a warning for each room whose outline is not its rectangle and left some outside."""
    out, warnings = {}, []
    for room in rooms:
        points = []
        for p in room["layout"]["positions"]:
            x, y = geometry.to_view(rects[room["id"]], k, p["x_m"], p["y_m"])
            points.append({"tag": p.get("tag", ""), "x": x, "y": y, "z_m": p.get("z_m"), "wall": p.get("wall", ""), "kind": "TE" if room["family"] == "TUE" else "TG"})
        outline = outlines.get(room["id"])
        kept = [p for p in points if outline is None or geometry.contains(outline, p["x"], p["y"])]
        if len(kept) < len(points):
            warnings.append(f"room '{room['name']}': {len(points) - len(kept)} of {len(points)} outlets fall outside its outline and are not placed")
        out[room["id"]] = kept
    return out, warnings


def _scale(body: CalcIn) -> float:
    try:
        return geometry.metres_per_unit(body.sheet.scale)
    except geometry.GeometryError as exc:
        raise Invalid({"scale": str(exc)})


def calc(project_dir: Path, body: CalcIn) -> dict:
    """Outlets for the rooms of a sheet. Answers `{result, placements, skipped, warnings}`; `result` is the engine's (None when nothing calculated) and `placements` are the outlets of each room in
    view units."""
    engine, _ = _engine()
    k = _scale(body)
    prepared = _prepare(body, k, effective(project_dir))
    if not prepared.rooms:
        return {"result": None, "placements": {}, "skipped": prepared.skipped, "warnings": prepared.warnings + ["nothing could be calculated: give each room its use"]}
    doc = {"schema_version": "1.0", "receptacles": [_engine()[1].as_document(rid, e, body.lang) for rid, e in effective(project_dir).items()], "rooms": prepared.rooms}
    try:
        result = engine.run(doc, engine.Options(norm=body.options.norm)).as_dict()
    except engine.ReceptaclesError as exc:
        raise Invalid({"receptacles": str(exc)})
    outlines = {r.id: r.points for r in body.sheet.rooms if r.id in prepared.rects and not prepared.rects[r.id].exact}
    placements, outside = _placements(result["rooms"], prepared.rects, k, outlines)
    return {"result": result, "placements": placements, "skipped": prepared.skipped, "warnings": prepared.warnings + list(result["warnings"]) + outside}
