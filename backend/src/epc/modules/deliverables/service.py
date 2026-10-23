"""Deliverables of a project: list, safe downloads, counters used by dashboards."""
from pathlib import Path
from typing import Tuple

from epc.core.config import settings
from epc.core.errors import NotFound
from epc.core.fsutil import is_inside, read_json, safe_file, today
from epc.modules.deliverables import repository


def list_items(d: Path) -> list:
    base, now = repository.deliverables_dir(d), today().isoformat()
    out = []
    for x in repository.read_items(d):
        f = x.get("file")
        out.append({**x, "downloadable": bool(f and is_inside(base, f)),
                    "overdue": x.get("status") != "delivered" and bool(x.get("due")) and x["due"] < now})
    return out


def file_for(d: Path, item_id: str) -> Tuple[Path, str]:
    item = next((x for x in repository.read_items(d) if x.get("id") == item_id), None)
    if not item or not item.get("file"):
        raise NotFound("file not found")
    path = safe_file(repository.deliverables_dir(d), item["file"])
    return path, f"{item.get('code', item_id)}.{item.get('format', path.suffix.lstrip('.'))}"


def counts(d: Path) -> dict:
    items, now = repository.read_items(d), today().isoformat()
    return {"total": len(items), "delivered": sum(1 for x in items if x.get("status") == "delivered"),
            "overdue": sum(1 for x in items if x.get("status") != "delivered" and x.get("due") and x["due"] < now)}


def due_soon(d: Path, limit_iso: str) -> int:
    return sum(1 for x in repository.read_items(d) if x.get("status") != "delivered" and x.get("due") and x["due"] <= limit_iso)


def format_policy() -> dict:
    return read_json(settings.schemas_dir / "deliverable-policy.json", {"formats": {}})
