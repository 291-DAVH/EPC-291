"""Conversations between disciplines, always about a place or a thing and always owned by the discipline that opened them:
  comment      a note pinned on the plan; open or resolved;
  request      one discipline asks another for something; open, in review, resolved or rejected;
  opening      a request for a pass through a wall or a slab (with its size);
  reservation  a space a discipline keeps for itself; the others keep out of it while it stands (see detection.reservation_items).
The other discipline answers on the thread; it never edits the drawing of the one that asked."""
from pathlib import Path
from typing import Any, Dict, List, Optional

from epc.core import clock
from epc.core.errors import Invalid, NotFound
from epc.core.ids import max_seq
from epc.modules.coordination import repository
from epc.modules.identity import public as identity

STATES = {"comment": ("open", "resolved"), "request": ("open", "review", "resolved", "rejected"), "opening": ("open", "review", "resolved", "rejected"), "reservation": ("open", "accepted", "released")}
FILE = "threads.json"


def _all(d: Path) -> List[dict]:
    return repository.read(d, FILE, []) or []


def _who() -> str:
    user = identity.current_user()
    return user.get("email", "") or user.get("name", "")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _opening(geom: Dict[str, Any]) -> dict:
    size = {k: geom[k] for k in ("ancho_m", "alto_m", "z_m") if k in geom}
    if not all(_is_number(v) for v in size.values()):
        raise Invalid({"geom": "sizes in metres"})
    return size


def _points_ok(pts: Any) -> bool:
    return isinstance(pts, list) and bool(pts) and all(isinstance(p, list) and len(p) == 2 and all(_is_number(v) for v in p) for p in pts)


def _level_number(level: Any) -> int:
    try:
        return int(level[1:])
    except (ValueError, TypeError):
        raise Invalid({"geom": "level such as L0, L1, L-1"})


def _reservation(geom: Dict[str, Any]) -> dict:
    pts, width, z0, z1, level = geom.get("points_m"), geom.get("width_m"), geom.get("z0"), geom.get("z1"), geom.get("level", "")
    if not _points_ok(pts) or not all(_is_number(v) for v in (width, z0, z1)) or width <= 0 or z1 <= z0:
        raise Invalid({"geom": "a reservation needs points_m (metres), a positive width_m and z0 below z1"})
    return {"points_m": pts, "width_m": width, "z0": z0, "z1": z1, "level": level, "level_number": _level_number(level), "sheet": geom.get("sheet", "")}


def _geometry(kind: str, geom: Optional[Dict[str, Any]]) -> Optional[dict]:
    """The space a reservation takes (a line in metres with a width and heights) or the size of an opening; nothing for the rest."""
    if kind in ("comment", "request"):
        return None
    return _opening(geom or {}) if kind == "opening" else _reservation(geom or {})


def _point(value: Any) -> Optional[list]:
    if value is None:
        return None
    if not (isinstance(value, list) and len(value) == 2 and all(_is_number(v) for v in value)):
        raise Invalid({"point_m": "[x, y] in metres"})
    return [float(value[0]), float(value[1])]


def _parties(kind: str, body: Dict[str, Any]) -> tuple:
    origin = repository.discipline_id(body.get("from_discipline", ""))
    target = body.get("to_discipline", "")
    if kind in ("request", "opening"):
        repository.discipline_id(target)
        if target == origin:
            raise Invalid({"to_discipline": "ask another discipline"})
    elif target:
        repository.discipline_id(target)
    return origin, target


def create(d: Path, body: dict) -> dict:
    kind = body.get("kind", "")
    if kind not in STATES:
        raise Invalid({"kind": "one of " + ", ".join(STATES)})
    origin, target = _parties(kind, body)
    title, text = (body.get("title") or "").strip(), (body.get("text") or "").strip()
    if not (title or text):
        raise Invalid({"title": "write something"})
    items = _all(d)
    now = clock.now_local()
    thread = {"id": f"T-{max_seq(items, 'T') + 1:03d}", "kind": kind, "from_discipline": origin, "to_discipline": target, "title": title[:120], "text": text[:4000], "status": "open",
              "sheet": body.get("sheet", ""), "level": body.get("level", ""), "point_m": _point(body.get("point_m")), "geom": _geometry(kind, body.get("geom")),
              "created_at": now, "created_by": _who(), "history": [{"at": now, "by": _who(), "status": "open", "comment": text[:4000]}]}
    repository.write(d, FILE, items + [thread])
    return thread


def update(d: Path, thread_id: str, body: dict) -> dict:
    """Answer a thread: a new state and/or a comment. Whoever answers is recorded; nothing is overwritten."""
    items = _all(d)
    t = next((x for x in items if x["id"] == thread_id), None)
    if t is None:
        raise NotFound("thread not found")
    status = body.get("status") or t["status"]
    if status not in STATES[t["kind"]]:
        raise Invalid({"status": "one of " + ", ".join(STATES[t["kind"]])})
    comment = (body.get("comment") or "").strip()
    if status == t["status"] and not comment:
        raise Invalid({"comment": "write a comment or change the state"})
    t["status"] = status
    t["history"].append({"at": clock.now_local(), "by": _who(), "status": status, "comment": comment[:4000]})
    repository.write(d, FILE, items)
    return t


def remove(d: Path, thread_id: str) -> None:
    items = _all(d)
    if not any(x["id"] == thread_id for x in items):
        raise NotFound("thread not found")
    repository.write(d, FILE, [x for x in items if x["id"] != thread_id])


def listing(d: Path, level: str = "", discipline: str = "", status: str = "") -> List[dict]:
    """Threads newest first, optionally those of a level, those a discipline opened or was asked, or in one state."""
    out = [t for t in _all(d) if (not level or t.get("level") == level) and (not status or t["status"] == status)
           and (not discipline or discipline in (t["from_discipline"], t["to_discipline"]))]
    return sorted(out, key=lambda t: t["created_at"], reverse=True)
