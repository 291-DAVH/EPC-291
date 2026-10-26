from pathlib import Path
from typing import Dict

from epc.core import ids
from epc.core.errors import Invalid, first_or_404
from epc.core.fsutil import today
from epc.modules.backlog import repository
from epc.modules.backlog.models import ItemPatch, NewItem
from epc.modules.wbs import public as wbs

TYPES = ("task", "change", "risk", "question", "defect")
PRIORITIES = ("P1", "P2", "P3")
STATUSES = ("backlog", "todo", "doing", "done")


def _check(d: Path, f: dict) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    if "title" in f and not (f["title"] or "").strip():
        errors["title"] = "required"
    for key, allowed in (("type", TYPES), ("priority", PRIORITIES), ("status", STATUSES)):
        if f.get(key) is not None and f[key] not in allowed:
            errors[key] = "one of " + ", ".join(allowed)
    if f.get("estimate_h") is not None and f["estimate_h"] < 0:
        errors["estimate_h"] = "must be >= 0"
    if f.get("wbs_id") and not wbs.has_node(d, f["wbs_id"]):
        errors["wbs_id"] = f"WBS node {f['wbs_id']} does not exist"
    return errors


def view(d: Path) -> dict:
    items = repository.load(d)
    by_status = {s: [i for i in items if i["status"] == s] for s in STATUSES}
    return {"items": sorted(items, key=lambda i: (STATUSES.index(i["status"]), i["priority"], i["id"])),
            "counts": {s: len(v) for s, v in by_status.items()},
            "estimate_open_h": sum(i["estimate_h"] for i in items if i["status"] != "done")}


def create(d: Path, body: NewItem) -> dict:
    f = body.model_dump()
    errors = _check(d, f)
    if errors:
        raise Invalid(errors)
    items = repository.load(d)
    n = ids.max_seq(items) + 1
    item = {"id": f"BL-{n:03d}", "status": "backlog", "created": today().isoformat(), **f, "title": f["title"].strip()}
    repository.save(d, items + [item])
    return item


def update(d: Path, item_id: str, body: ItemPatch) -> dict:
    items = repository.load(d)
    item = first_or_404((i for i in items if i["id"] == item_id), "backlog item not found")
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    errors = _check(d, changes)
    if errors:
        raise Invalid(errors)
    item.update(changes)
    repository.save(d, items)
    return item


def counts(d: Path) -> dict:
    return view(d)["counts"]
