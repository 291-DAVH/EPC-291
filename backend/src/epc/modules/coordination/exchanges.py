"""Data that crosses from one discipline to another, with a single owner: the owner publishes the value, the others take it. When the owner changes it, whoever took the
previous one is told it is out of date; nobody edits a value that is not theirs."""
from pathlib import Path
from typing import Any, Dict, List

from epc.core import clock
from epc.core.errors import Invalid, NotFound
from epc.core.ids import max_seq
from epc.modules.coordination import repository
from epc.modules.identity import public as identity

FILE = "exchanges.json"


def _all(d: Path) -> List[dict]:
    return repository.read(d, FILE, []) or []


def state_of(x: dict, consumer: str) -> str:
    """delivered (the consumer took the current value), outdated (it took an earlier one) or pending (it never took it)."""
    ack = (x.get("acks") or {}).get(consumer)
    return "pending" if ack is None else "delivered" if ack >= x["version"] else "outdated"


def _view(x: dict) -> dict:
    return {**x, "states": {c: state_of(x, c) for c in x["consumers"]}}


def listing(d: Path) -> List[dict]:
    return [_view(x) for x in _all(d)]


def _parties(body: Dict[str, Any]) -> tuple:
    owner = repository.discipline_id(body.get("owner", ""))
    consumers = [repository.discipline_id(c) for c in dict.fromkeys(body.get("consumers") or [])]
    if not consumers or owner in consumers:
        raise Invalid({"consumers": "name the other disciplines that use it"})
    return owner, consumers


def _what(body: Dict[str, Any]) -> tuple:
    tag, field = (body.get("tag") or "").strip(), (body.get("field") or "").strip()
    if not tag or not field:
        raise Invalid({"tag": "the equipment and the datum are required"})
    if body.get("value") in (None, ""):
        raise Invalid({"value": "the value is required"})
    return tag[:60], field[:60]


def _clean(body: Dict[str, Any]) -> dict:
    owner, consumers = _parties(body)
    tag, field = _what(body)
    return {"owner": owner, "consumers": consumers, "tag": tag, "field": field, "unit": (body.get("unit") or "")[:16], "value": body["value"]}


def publish(d: Path, body: Dict[str, Any]) -> dict:
    """Create the datum or give it a new value; a changed value raises the version, so those who took the old one see it outdated."""
    new = _clean(body)
    items = _all(d)
    who, now = identity.current_user().get("email", ""), clock.now_local()
    x = next((i for i in items if (i["tag"], i["field"], i["owner"]) == (new["tag"], new["field"], new["owner"])), None)
    if x is None:
        x = {"id": f"X-{max_seq(items, 'X') + 1:03d}", **new, "version": 1, "acks": {}, "updated_at": now, "updated_by": who}
        items.append(x)
    else:
        if x["value"] != new["value"]:
            x.update(value=new["value"], version=x["version"] + 1, updated_at=now, updated_by=who)
        x.update(consumers=new["consumers"], unit=new["unit"])
    repository.write(d, FILE, items)
    return _view(x)


def acknowledge(d: Path, exchange_id: str, discipline: str) -> dict:
    items = _all(d)
    x = next((i for i in items if i["id"] == exchange_id), None)
    if x is None:
        raise NotFound("datum not found")
    if discipline not in x["consumers"]:
        raise Invalid({"discipline": "only a discipline that uses the datum takes it"})
    x.setdefault("acks", {})[discipline] = x["version"]
    repository.write(d, FILE, items)
    return _view(x)


def remove(d: Path, exchange_id: str) -> None:
    items = _all(d)
    if not any(i["id"] == exchange_id for i in items):
        raise NotFound("datum not found")
    repository.write(d, FILE, [i for i in items if i["id"] != exchange_id])


def matrix(d: Path) -> List[dict]:
    """Who gives what to whom: for every pair (owner, consumer), how many data are delivered, pending or outdated."""
    cells: Dict[tuple, Dict[str, int]] = {}
    for x in _all(d):
        for c in x["consumers"]:
            cell = cells.setdefault((x["owner"], c), {"delivered": 0, "pending": 0, "outdated": 0})
            cell[state_of(x, c)] += 1
    return [{"owner": o, "consumer": c, **counts, "total": sum(counts.values())} for (o, c), counts in sorted(cells.items())]
