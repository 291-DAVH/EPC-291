import re
from pathlib import Path
from typing import Dict, List

from epc.core.errors import Invalid
from epc.modules.wbs import repository
from epc.modules.wbs.models import WbsIn

ID = re.compile(r"^[0-9]+(\.[0-9]+){0,5}$")          # 1, 1.2, 1.2.3 ... the parent is the id without its last part


def _key(i: str):
    return tuple(int(x) for x in i.split("."))


def _parent(i: str) -> str:
    return i.rsplit(".", 1)[0] if "." in i else ""


def validate(nodes: List[dict]) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    ids = [n["id"] for n in nodes]
    for n in nodes:
        i = n["id"]
        if not ID.match(i):
            errors[f"id:{i}"] = "WBS ids are dotted numbers such as 1 or 1.2"
            continue
        if ids.count(i) > 1:
            errors[f"id:{i}"] = "duplicated id"
        if _parent(i) and _parent(i) not in ids:
            errors[f"id:{i}"] = f"parent {_parent(i)} does not exist"
        if not n["name"].strip():
            errors[f"name:{i}"] = "required"
        if n["weight"] < 0:
            errors[f"weight:{i}"] = "must be >= 0"
        if not 0 <= n["progress"] <= 100:
            errors[f"progress:{i}"] = "must be between 0 and 100"
    return errors


def _rollup(nodes: List[dict]) -> List[dict]:
    by_id = {n["id"]: dict(n) for n in nodes}
    kids: Dict[str, List[str]] = {}
    for i in by_id:
        kids.setdefault(_parent(i), []).append(i)
    done: Dict[str, tuple] = {}                      # id -> (weight, progress)

    def calc(i: str) -> tuple:
        if i in done:
            return done[i]
        ch = kids.get(i)
        if not ch:
            res = (by_id[i]["weight"], by_id[i]["progress"])
        else:
            parts = [calc(c) for c in ch]
            w = sum(p[0] for p in parts)
            res = (w, sum(p[0] * p[1] for p in parts) / w if w else 0.0)
        done[i] = res
        return res

    out = []
    for i in sorted(by_id, key=_key):
        w, p = calc(i)
        n = by_id[i]
        out.append({**n, "parent": _parent(i), "level": i.count(".") + 1, "leaf": i not in kids, "weight": w, "progress": round(p, 1),
                    "status": "done" if p >= 100 else "not_started" if p <= 0 else "in_progress"})
    return out


def view(d: Path) -> dict:
    nodes = _rollup(repository.load(d))
    roots = [n for n in nodes if not n["parent"]]
    tw = sum(n["weight"] for n in roots)
    overall = round(sum(n["weight"] * n["progress"] for n in roots) / tw, 1) if tw else 0.0
    leaves = [n for n in nodes if n["leaf"]]
    return {"nodes": nodes, "progress": overall,
            "counts": {"nodes": len(nodes), "leaves": len(leaves), "done": sum(1 for n in leaves if n["status"] == "done")}}


def replace(d: Path, body: WbsIn) -> dict:
    nodes = [n.model_dump() for n in body.nodes]
    errors = validate(nodes)
    if errors:
        raise Invalid(errors)
    repository.save(d, sorted(nodes, key=lambda n: _key(n["id"])))
    return view(d)


def has_node(d: Path, node_id: str) -> bool:
    return any(n["id"] == node_id for n in repository.load(d))


def overall_progress(d: Path) -> float:
    return view(d)["progress"]
