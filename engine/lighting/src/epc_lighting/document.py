"""Reads the input document (JSON) and turns it into the engine's value objects.

Every message says what to correct. Validation happens here and only here: the
rest of the engine trusts the objects it receives.
"""
import json
import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from epc_lighting import methods
from epc_lighting.config import PARAMS, data
from epc_lighting.model import Area, Emergency, Estimate, LightingError, Luminaire, PointSpec, Project, Room, Route
from epc_lighting.tables import number, parse_cu_table, parse_photometry

SCHEMA_VERSION = "1.0"
DEFAULTS = PARAMS["defaults"]


def _fail(path: str, message: str) -> None:
    raise LightingError(f"{path}: {message}")


def load_document(source: Any) -> Dict[str, Any]:
    """A JSON document from a dict, a str or bytes."""
    if isinstance(source, dict):
        return source
    if isinstance(source, (bytes, bytearray)):
        try:
            source = bytes(source).decode("utf-8-sig")
        except UnicodeDecodeError:
            raise LightingError("the input is not UTF-8 text: save the JSON document as UTF-8")
    if not isinstance(source, str):
        raise LightingError("the input must be a JSON document (a dict, a str or bytes)")
    if not source.strip():
        raise LightingError("the input is empty")
    try:
        doc = json.loads(source)
    except json.JSONDecodeError as exc:
        raise LightingError(f"the input is not valid JSON: {exc}")
    if not isinstance(doc, dict):
        raise LightingError("the JSON document must be an object with luminaires, rooms and/or areas")
    return doc


def _object(raw: Any, path: str) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        _fail(path, "must be an object")
    return raw


def _text(raw: Dict[str, Any], key: str, path: str, required: bool = False, default: Optional[str] = None) -> Optional[str]:
    if raw.get(key) is None:
        if required:
            _fail(path, f"'{key}' is required (a text)")
        return default
    if not isinstance(raw[key], str) or not raw[key].strip():
        _fail(f"{path}.{key}", f"must be a non-empty text, got {raw[key]!r}")
    return raw[key]


def _num(raw: Dict[str, Any], key: str, path: str, required: bool = False, default: Optional[float] = None, **limits: Any) -> Optional[float]:
    if raw.get(key) is None:
        if required:
            _fail(path, f"'{key}' is required (a number)")
        return default
    return number(raw[key], f"{path}.{key}", **limits)


def _choice(value: Any, allowed: Sequence[str], path: str) -> str:
    if value not in allowed:
        _fail(path, f"'{value}' is not valid: choose one of {sorted(allowed)}")
    return value


def _items(doc: Dict[str, Any], key: str) -> List[Any]:
    raw = doc.get(key, [])
    if not isinstance(raw, list):
        _fail(key, "must be a list")
    return raw


def _check_unique(ids: List[str], where: str) -> None:
    seen = set()
    for i in ids:
        if i in seen:
            _fail(where, f"id '{i}' appears more than once: ids must be unique")
        seen.add(i)


def parse_luminaire(raw: Any, path: str) -> Luminaire:
    raw = _object(raw, path)
    lid = _text(raw, "id", path, required=True)
    here = f"{path} ('{lid}')"
    lamps = _num(raw, "lamps", here, default=1, minimum=1)
    if lamps != int(lamps):
        _fail(f"{here}.lamps", f"must be a whole number, got {lamps}")
    cu_table = parse_cu_table(raw["cu_table"], f"{here}.cu_table") if raw.get("cu_table") is not None else None
    photometry = parse_photometry(raw["photometry"], f"{here}.photometry") if raw.get("photometry") is not None else None
    distribution = raw.get("distribution")
    if distribution is not None:
        _choice(distribution, list(data("lighting_systems")["systems"]), f"{here}.distribution")
    return Luminaire(
        id=lid,
        name=_text(raw, "name", here, default=lid),
        lamps=int(lamps),
        lamp_flux_lm=_num(raw, "lamp_flux_lm", here, required=True, positive=True),
        efficiency=_num(raw, "efficiency", here, default=DEFAULTS["luminaire_efficiency"], positive=True, maximum=1),
        power_w=_num(raw, "power_w", here, minimum=0),
        cu=_num(raw, "cu", here, positive=True),
        cu_table=cu_table,
        photometry=photometry,
        distribution=distribution,
        spacing_ratio=_num(raw, "spacing_ratio", here, positive=True),
    )


def parse_reflectances(raw: Any, path: str) -> Tuple[Estimate, Estimate, Estimate]:
    given = {} if raw is None else _object(raw, path)
    keys = ("ceiling", "walls", "floor")
    unknown = sorted(set(given) - set(keys))
    if unknown:
        _fail(path, f"unknown surface(s) {unknown}: use {list(keys)}")
    return tuple(_one_reflectance(given.get(k), k, f"{path}.{k}") for k in keys)  # type: ignore[return-value]


def _one_reflectance(spec: Any, surface: str, path: str) -> Estimate:
    conf = PARAMS["reflectance_confidence"]
    if spec is None:
        value = data("reflectances")["defaults"][surface]
        return Estimate(value, "default when not given (UPV article: 0.5 ceiling, 0.3 walls, 0.1 floor)", conf["default"])
    if isinstance(spec, dict):
        return _material_reflectance(spec, path, conf)
    return Estimate(number(spec, path, minimum=0, maximum=1), "given", conf["given"])


def _material_reflectance(spec: Dict[str, Any], path: str, conf: Dict[str, float]) -> Estimate:
    materials = data("reflectances")["materials"]
    name = spec.get("material")
    if name not in materials:
        _fail(path, f"material '{name}' is not valid: choose one of {sorted(materials)} or give a number between 0 and 1")
    low, high = materials[name]["range"]
    return Estimate((low + high) / 2, f"material '{name}' (UPV table 4, range {low}-{high}), midpoint taken", conf["material_midpoint"])


def _parse_normal(raw: Any, path: str) -> Tuple[float, float, float]:
    if raw is None or raw == "horizontal":
        return (0.0, 0.0, 1.0)
    if not isinstance(raw, list) or len(raw) != 3:
        _fail(path, "must be 'horizontal' or a vector [nx, ny, nz]")
    vec = [number(v, f"{path}[{i}]") for i, v in enumerate(raw)]
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        _fail(path, "the normal vector cannot be [0, 0, 0]")
    return (vec[0] / norm, vec[1] / norm, vec[2] / norm)


def _parse_positions(raw: Any, width: float, length: float, path: str) -> Tuple[Tuple[float, float, Optional[float], Optional[str]], ...]:
    """Luminaires that are already placed (for example drawn on a plan): the room is then checked as it is, not as the engine would arrange it."""
    if raw is None:
        return ()
    if not isinstance(raw, list) or not raw:
        _fail(path, "must be a non-empty list of luminaires {x_m, y_m}")
    if len(raw) > 2000:
        _fail(path, f"has {len(raw)} luminaires: up to 2000")
    found = []
    for i, p in enumerate(raw):
        here = f"{path}[{i}]"
        p = _object(p, here)
        found.append((_num(p, "x_m", here, required=True, minimum=0, maximum=length), _num(p, "y_m", here, required=True, minimum=0, maximum=width), _num(p, "z_m", here, positive=True), _text(p, "tag", here)))
    return tuple(found)


def _parse_points(raw: Any, width: float, length: float, path: str) -> Tuple[PointSpec, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        _fail(path, "must be a list of points")
    points = []
    for i, p in enumerate(raw):
        here = f"{path}[{i}]"
        p = _object(p, here)
        x = _num(p, "x_m", here, required=True, minimum=0, maximum=length)
        y = _num(p, "y_m", here, required=True, minimum=0, maximum=width)
        points.append(PointSpec(_text(p, "id", here, default=f"P{i + 1}"), x, y, _parse_normal(p.get("normal"), f"{here}.normal")))
    return tuple(points)


def _parse_target(raw: Dict[str, Any], path: str) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    target = _num(raw, "target_lux", path, positive=True)
    rule = _text(raw, "target_rule", path)
    activity = raw.get("activity")
    if activity is not None:
        ids = [a["id"] for a in data("levels")["activities"]]
        _choice(activity, ids, f"{path}.activity")
    if target is None and activity is None and rule is None:
        _fail(path, "'target_lux', 'activity' or 'target_rule' is required: give the maintained illuminance in lux, one of the activity ids " + str(sorted(a["id"] for a in data("levels")["activities"])) + ", or the id of an approved rule of a norm")
    return target, activity, rule


def parse_room(raw: Any, path: str, luminaire_ids: Sequence[str]) -> Room:
    raw = _object(raw, path)
    rid = _text(raw, "id", path, required=True)
    here = f"{path} ('{rid}')"
    width = _num(raw, "width_m", here, required=True, positive=True)
    length = _num(raw, "length_m", here, required=True, positive=True)
    target, activity, rule = _parse_target(raw, here)
    systems = list(data("lighting_systems")["systems"])
    mode = raw.get("suspension_mode")
    if mode is not None:
        _choice(mode, ["auto_min", "auto_optimal"], f"{here}.suspension_mode")
    return Room(
        id=rid,
        name=_text(raw, "name", here, default=rid),
        width_m=width,
        length_m=length,
        height_m=_num(raw, "height_m", here, required=True, positive=True),
        work_plane_m=_num(raw, "work_plane_height_m", here, default=DEFAULTS["work_plane_height_m"], minimum=0),
        suspension_m=_num(raw, "suspension_m", here, default=DEFAULTS["suspension_m"], minimum=0),
        suspension_mode=mode,
        luminaire_id=_luminaire_ref(raw, here, luminaire_ids),
        method=_choice(raw.get("method", DEFAULTS["method"]), methods.names(), f"{here}.method"),
        system=_choice(raw.get("lighting_system", DEFAULTS["lighting_system"]), systems, f"{here}.lighting_system"),
        target_lux=target,
        activity=activity,
        reflectances=parse_reflectances(raw.get("reflectances"), f"{here}.reflectances"),
        environment=_choice(raw.get("environment", DEFAULTS["environment"]), list(data("maintenance")["interior"]), f"{here}.environment"),
        maintenance=_num(raw, "maintenance_factor", here, positive=True, maximum=1),
        cu=_num(raw, "coefficient_of_utilisation", here, positive=True),
        points=_parse_points(raw.get("points"), width, length, f"{here}.points"),
        point_step_m=_num(raw, "point_step_m", here, positive=True),
        operating_hours=_num(raw, "operating_hours_per_year", here, minimum=0, maximum=8760),
        ugr_calculated=_num(raw, "ugr_calculated", here, minimum=0),
        target_rule=rule,
        positions=_parse_positions(raw.get("positions"), width, length, f"{here}.positions"),
    )


def _luminaire_ref(raw: Dict[str, Any], path: str, luminaire_ids: Sequence[str]) -> str:
    ref = _text(raw, "luminaire", path, required=True)
    if ref not in luminaire_ids:
        _fail(f"{path}.luminaire", f"'{ref}' is not defined in 'luminaires': defined ids are {sorted(luminaire_ids)}")
    return ref


def parse_area(raw: Any, path: str, luminaire_ids: Sequence[str]) -> Area:
    raw = _object(raw, path)
    aid = _text(raw, "id", path, required=True)
    here = f"{path} ('{aid}')"
    target, activity, rule = _parse_target(raw, here)
    return Area(
        id=aid,
        name=_text(raw, "name", here, default=aid),
        area_m2=_num(raw, "area_m2", here, required=True, positive=True),
        luminaire_id=_luminaire_ref(raw, here, luminaire_ids),
        target_lux=target,
        activity=activity,
        beam_utilisation=_num(raw, "beam_utilisation", here, positive=True, maximum=1),
        enclosure=_choice(raw.get("enclosure", DEFAULTS["enclosure"]), list(data("maintenance")["exterior"]), f"{here}.enclosure"),
        maintenance=_num(raw, "maintenance_factor", here, positive=True, maximum=1),
        operating_hours=_num(raw, "operating_hours_per_year", here, minimum=0, maximum=8760),
        target_rule=rule,
    )


def _parse_xy(raw: Any, width: float, length: float, path: str) -> Tuple[float, float]:
    if not isinstance(raw, list) or len(raw) != 2:
        _fail(path, "must be a point [x_m, y_m] in metres from the corner of the room")
    return (number(raw[0], f"{path}[0]", minimum=0, maximum=length), number(raw[1], f"{path}[1]", minimum=0, maximum=width))


def _parse_routes(raw: Any, width: float, length: float, path: str) -> Tuple[Route, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        _fail(path, "must be a list of escape routes")
    routes = []
    for i, r in enumerate(raw):
        here = f"{path}[{i}]"
        r = _object(r, here)
        routes.append(Route(_text(r, "id", here, default=f"RT{i + 1}"), _parse_xy(r.get("start_m"), width, length, f"{here}.start_m"), _parse_xy(r.get("end_m"), width, length, f"{here}.end_m"),
                            _num(r, "e_min_lux", here, positive=True)))
    return tuple(routes)


def parse_emergency(raw: Any, path: str, luminaire_ids: Sequence[str]) -> Emergency:
    raw = _object(raw, path)
    eid = _text(raw, "id", path, required=True)
    here = f"{path} ('{eid}')"
    width = _num(raw, "width_m", here, required=True, positive=True)
    length = _num(raw, "length_m", here, required=True, positive=True)
    return Emergency(
        id=eid,
        name=_text(raw, "name", here, default=eid),
        width_m=width,
        length_m=length,
        height_m=_num(raw, "height_m", here, required=True, positive=True),
        luminaire_id=_luminaire_ref(raw, here, luminaire_ids),
        e_min_lux=_num(raw, "e_min_lux", here, positive=True),
        ratio_max=_num(raw, "max_over_min", here, minimum=1),
        maintenance=_num(raw, "maintenance_factor", here, positive=True, maximum=1),
        band_m=_num(raw, "band_m", here, minimum=0),
        step_m=_num(raw, "point_step_m", here, positive=True),
        routes=_parse_routes(raw.get("routes"), width, length, f"{here}.routes"),
    )


def _parse_list(doc: Dict[str, Any], key: str, parser: Callable[..., Any], *extra: Any) -> Tuple[Any, ...]:
    return tuple(parser(raw, f"{key}[{i}]", *extra) for i, raw in enumerate(_items(doc, key)))


def parse_project(doc: Dict[str, Any]) -> Project:
    """Validate the whole document and return the project it describes."""
    if doc.get("schema_version") != SCHEMA_VERSION:
        _fail("schema_version", f"must be '{SCHEMA_VERSION}', got {doc.get('schema_version')!r}")
    luminaires = _parse_list(doc, "luminaires", parse_luminaire)
    _check_unique([lum.id for lum in luminaires], "luminaires")
    ids = [lum.id for lum in luminaires]
    rooms = _parse_list(doc, "rooms", parse_room, ids)
    areas = _parse_list(doc, "areas", parse_area, ids)
    emergency = _parse_list(doc, "emergency", parse_emergency, ids)
    _check_unique([r.id for r in rooms], "rooms")
    _check_unique([a.id for a in areas], "areas")
    _check_unique([e.id for e in emergency], "emergency")
    return Project({lum.id: lum for lum in luminaires}, rooms, areas, emergency)
