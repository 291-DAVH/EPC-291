"""What changed in a drawing since its files were last made: the person sees it before making them again."""
from typing import Any, Dict, List

EPS = 1e-6


def _by_id(items: List[dict]) -> Dict[str, dict]:
    return {i["id"]: i for i in items}


def _brief(x: dict) -> dict:
    return {"id": x["id"], "kind": x["kind"], "tag": x.get("tag", "")}


def _moved_node(a: dict, b: dict) -> bool:
    return abs(a["x"] - b["x"]) > EPS or abs(a["y"] - b["y"]) > EPS


def _changed_line(a: dict, b: dict) -> bool:
    return a["points"] != b["points"] or a["kind"] != b["kind"] or (a.get("circuit") or "") != (b.get("circuit") or "")


def _compare(old: List[dict], new: List[dict], changed) -> Dict[str, List[dict]]:
    before, after = _by_id(old), _by_id(new)
    return {"added": [_brief(after[i]) for i in after if i not in before], "removed": [_brief(before[i]) for i in before if i not in after],
            "changed": [_brief(after[i]) for i in after if i in before and changed(before[i], after[i])]}


def _attrs_differ(a: dict, b: dict) -> bool:
    return (a.get("attrs") or {}) != (b.get("attrs") or {})


def _node_changed(a: dict, b: dict) -> bool:
    return _moved_node(a, b) or a["kind"] != b["kind"] or (a.get("circuit") or "") != (b.get("circuit") or "") or _attrs_differ(a, b)


def _line_edited(a: dict, b: dict) -> bool:
    return _changed_line(a, b) or _attrs_differ(a, b)


def _flags(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, bool]:
    return {"scale_changed": old.get("scale") != new.get("scale"), "origin_changed": old.get("origin") != new.get("origin"),
            "circuits_changed": old.get("circuits", []) != new.get("circuits", []), "discipline_changed": old.get("discipline") != new.get("discipline")}


def diff(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """The differences of the drawing now (`new`) against the one the files were made from (`old`): elements added, removed and moved or edited, and whether the scale, the origin or the circuits changed."""
    nodes = _compare(old.get("nodes", []), new.get("nodes", []), _node_changed)
    lines = _compare(old.get("lines", []), new.get("lines", []), _line_edited)
    return {"has_snapshot": True, **_flags(old, new), "nodes": nodes, "lines": lines, "count": sum(len(v) for part in (nodes, lines) for v in part.values())}
