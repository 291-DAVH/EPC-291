"""The boards of a project: reading, saving, creating and removing them, with their title block and supply."""

import re
from pathlib import Path
from typing import Dict

from epc.core.errors import Conflict, Invalid, NotFound
from epc.modules.engineering import public as engineering
from epc.modules.masterdata import public as masterdata
from epc.modules.projects import public as projects
from epc.modules.sld import lengths, repository
from epc.modules.sld.models import Board, Circuit, SldIn, Titleblock
from epc.modules.sld.validation import options, validate


def _resolve(d: Path, bid: str) -> str:
    """The board asked for; without one, the first board of the project ("" when the project has none yet)."""
    ids = repository.board_ids(d)
    if bid:
        if bid not in ids:
            raise NotFound("board not found")
        return bid
    return ids[0] if ids else ""


BOARD_TITLEBLOCK = ("description", "location", "scale", "revision", "status", "drawing_type", "replaces", "replaced_by", "internal_code")           # what a board owns; the rest comes from the project (single source)


DISCIPLINE = "electrical"


def titleblock(d: Path, own: dict) -> dict:
    """Effective title block: the board's own fields over the project's issuer, client and team of the discipline."""
    base = Titleblock().model_dump()
    merged = {**base, **{k: v for k, v in (own or {}).items() if k in BOARD_TITLEBLOCK}}
    return {**merged, **masterdata.titleblock(d, DISCIPLINE)}


def _blank(d: Path, name: str = "") -> dict:
    meta = projects.read_meta(d)
    volt = engineering.criterion_value(d, "nominal_voltage_v") or 380
    return {"board": Board(voltage_v=volt, project=meta.get("project_code", ""), name=name).model_dump(), "circuits": [],
            "titleblock": titleblock(d, {"description": meta.get("project_name", "")})}


def view(d: Path, bid: str = "") -> dict:
    bid = _resolve(d, bid)
    saved = repository.load_input(d, bid) if bid else None
    meta = projects.read_meta(d)
    if saved:
        data = {k: saved[k] for k in ("board", "circuits") if k in saved}
        data["titleblock"] = titleblock(d, saved.get("titleblock"))
        data["board"] = {**Board().model_dump(), **data["board"]}
    else:
        data = _blank(d)
    return {"input": data, "saved": bool(saved), "board_id": bid, "lengths": lengths.info(d, data["circuits"]), "options": options(), "wiring_defaults": repository.wiring_defaults(engineering.criteria_values(d)), "status": status(d, bid),
            "boards": [{"id": b["id"], "name": b["name"]} for b in boards(d)],
            "people": [p["name"] for p in masterdata.people()], "parties": _parties_line(d),
            "logos": {k: v is not None for k, v in (("company", masterdata.logos(d)["provider"]), ("client", masterdata.logos(d)["client"]))}}


def _parties_line(d: Path) -> dict:
    """What the sheets will say about the project's issuer, client and team (read-only here: it is set once in the project)."""
    p = masterdata.project_parties(d)
    return {"issuer": (p["issuer"] or {}).get("legal_name", ""), "client": p["client"].get("name", ""), "team": p["team"].get(DISCIPLINE, {})}


def _location(data: dict) -> str:
    """Where in the building the board is (a field of its title block)."""
    return (data.get("titleblock") or {}).get("location") or ""


def boards(d: Path) -> list:
    """The boards of the project with their state; each one has its own data, calculation, memo and diagrams."""
    out = []
    for bid in repository.board_ids(d):
        data = repository.load_input(d, bid) or {}
        b = {**Board().model_dump(), **(data.get("board") or {})}
        st = repository.load_status(d, bid)
        out.append({"id": bid, "name": b["name"] or bid, "voltage_v": b["voltage_v"], "system": b["system"], "icc_ka": b["icc_ka"], "circuits": len(data.get("circuits") or []),
                    "supplied_from": b["supplied_from"], "supply_tag": b["supply_tag"], "level": b["level"], "location": _location(data), "state": st.get("state", "idle"), "finished": st.get("finished")})
    return out


def _supply_errors(d: Path, bid: str, board: dict) -> Dict[str, str]:
    up = (board.get("supplied_from") or "").strip()
    if not up:
        return {}
    ids = repository.board_ids(d)
    if up not in ids or up == bid:
        return {"board.supplied_from": "unknown board or itself"}
    seen, cur = {bid}, up                                                   # an upstream chain must not come back to this board
    while cur:
        if cur in seen:
            return {"board.supplied_from": "the supply chain would be a loop"}
        seen.add(cur)
        cur = ((repository.load_input(d, cur) or {}).get("board") or {}).get("supplied_from", "")
    tag = (board.get("supply_tag") or "").strip()
    tags = {c["tag"] for c in (repository.load_input(d, up) or {}).get("circuits", [])}
    if tag and tags and tag not in tags:
        return {"board.supply_tag": "that circuit does not exist in the upstream board"}
    return {}


def save(d: Path, body: SldIn, bid: str = "") -> dict:
    data = body.model_dump()
    for c in data["circuits"]:
        c["tag"], c["parent_tag"] = c["tag"].strip(), c["parent_tag"].strip()
    data["titleblock"] = {k: v for k, v in data["titleblock"].items() if k in BOARD_TITLEBLOCK}            # company, client and people are not the board's
    bid = _resolve(d, bid)
    errors = validate(data)
    for c in data["circuits"]:
        if c.get("route") and not errors:
            c["length_m"] = repository.route_total(c["route"])                  # with a real route, its total is the length (single source)
    errors.update(_supply_errors(d, bid, data["board"]))
    if errors:
        raise Invalid(errors)
    if not bid:
        bid = repository.new_id(d, data["board"]["name"])
    repository.save_input(d, bid, data)
    return view(d, bid)


LEVEL = re.compile(r"^L-?\d{1,2}$")


def _placement_errors(level: str, location: str) -> Dict[str, str]:
    errors = {}
    if level and not LEVEL.match(level):
        errors["level"] = "a level of the building: L-1, L0, L1..."
    if len(location) > 120:
        errors["location"] = "up to 120 characters"
    return errors


def _placement(level: str, location: str) -> tuple:
    """The level and the place of a board, clean, or `Invalid` with what to correct."""
    level, location = (level or "").strip(), (location or "").strip()
    errors = _placement_errors(level, location)
    if errors:
        raise Invalid(errors)
    return level, location


def create_board(d: Path, name: str, supplied_from: str = "", supply_tag: str = "", level: str = "", location: str = "") -> dict:
    name = (name or "").strip()
    if not name or len(name) > 60:
        raise Invalid({"name": "required, up to 60 characters"})
    level, location = _placement(level, location)
    if name.lower() in {b["name"].lower() for b in boards(d)}:
        raise Conflict({"name": "a board with that name already exists"})
    data = _blank(d, name)
    data["board"].update(supplied_from=supplied_from.strip(), supply_tag=supply_tag.strip(), level=level)
    data["titleblock"]["location"] = location
    errors = _supply_errors(d, "", data["board"])
    if errors:
        raise Invalid(errors)
    bid = repository.new_id(d, name)
    repository.save_input(d, bid, data)                                    # a draft: it has no circuits yet, so it cannot be generated until they are added
    return view(d, bid)


def remove_board(d: Path, bid: str) -> list:
    bid = _resolve(d, bid)
    if not bid:
        raise NotFound("board not found")
    if any(b["supplied_from"] == bid for b in boards(d)):
        raise Conflict({"board": "another board is supplied from this one: change its supply first"})
    if repository.load_status(d, bid).get("state") == "running":
        raise Conflict({"status": "a generation is running"})
    repository.delete_board(d, bid)
    return boards(d)


def example() -> dict:
    ex = repository.example_data()
    return {"board": Board(**ex["board"]).model_dump(), "circuits": [Circuit(**c).model_dump() for c in ex["circuits"]]}


def status(d: Path, bid: str = "") -> dict:
    bid = _resolve(d, bid)
    return repository.load_status(d, bid) if bid else {"state": "idle", "outputs": [], "log": []}


def _board_to_fill(d: Path, bid: str) -> str:
    """The board that receives new circuits: the one asked for, else the first of the project, creating it when there is none."""
    return create_board(d, "TG")["board_id"] if not bid and not repository.board_ids(d) else bid


def _circuit_of(spec: dict) -> dict:
    return Circuit(tag=spec["tag"], description=spec.get("description", ""), load=spec.get("load"), unit=spec.get("unit", "VA"), phase=spec.get("phase", "1F")).model_dump()


def add_circuits(d: Path, specs: list, bid: str = "") -> dict:
    """Add circuits (tag, description, load in VA) to a board, creating the first board of the project when there is none. A tag the board already has is left as it is.
    The caller is the plan editor, after the person accepted what it proposed."""
    v = view(d, _board_to_fill(d, bid))
    data = v["input"]
    have = {c["tag"] for c in data["circuits"]}
    added = [s for s in specs if s["tag"] not in have]
    data["circuits"] += [_circuit_of(s) for s in added]
    saved = save(d, SldIn(**data), v["board_id"]) if added else v
    return {"board_id": saved["board_id"], "added": [s["tag"] for s in added], "skipped": [s["tag"] for s in specs if s["tag"] in have]}
