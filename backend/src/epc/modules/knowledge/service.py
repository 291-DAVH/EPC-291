"""Standards and rules: browse, search and check project data against them."""
from typing import Optional

from epc.core.errors import NotFound
from epc.modules.knowledge import repository
from epc.modules.knowledge.models import CheckRequest


def rule_view(r: dict, full: bool = False) -> dict:
    v = {"id": r["id"], "standard": r["_standard"], "status": r["_status"], "clause": r["clause"], "part": r.get("part"),
         "page": r.get("page", {}).get("printed"), "topic": r["topic"], "title": r.get("title", ""), "type": r["type"],
         "summary": r.get("summary", {}), "has_check": bool(r.get("check")), "derived": bool(r.get("check", {}).get("derived")),
         "confidence": r.get("confidence"), "verification": r.get("verification"),
         "installation_types": r.get("applies_to", {}).get("installation_types", [])}
    if full:
        v.update(params=r.get("params", {}), check=r.get("check"), applies_to=r.get("applies_to", {}), table_ref=r.get("table_ref"))
    return v


def standards() -> list:
    rs, out = repository.ruleset(), []
    for sid, s in rs.standards.items():
        rules = [r for r in rs.rules if r["_standard"] == sid]
        out.append({"id": sid, "body": s.get("body"), "edition": s.get("edition"), "domain": s.get("domain"), "status": s["source_status"],
                    "validated_by": s.get("validated_by"), "rules": len(rules), "with_check": sum(1 for r in rules if r.get("check")),
                    "derived": sum(1 for r in rules if r.get("check", {}).get("derived")),
                    "low_confidence": sum(1 for r in rules if r.get("confidence") == "low")})
    return out


def topics() -> list:
    return sorted({r["topic"].split(".")[0] for r in repository.ruleset().rules})


def search(standard: Optional[str], topic: Optional[str], q: Optional[str], type: Optional[str], installation: Optional[str],
           only_checks: bool, limit: int) -> dict:
    out = []
    for r in repository.ruleset().query(topic=topic, standard=standard, installation_type=installation, type=type):
        if only_checks and not r.get("check"):
            continue
        if q:
            hay = " ".join([r["id"], r["clause"], r.get("title", ""), " ".join(r.get("summary", {}).values())]).lower()
            if q.lower() not in hay:
                continue
        out.append(rule_view(r))
    return {"total": len(out), "items": out[:limit]}


def rule(rule_id: str) -> dict:
    r = repository.ruleset().get(rule_id)
    if not r:
        raise NotFound("rule not found")
    return rule_view(r, full=True)


def check(req: CheckRequest) -> dict:
    rep = repository.ruleset().check(req.context, installation_type=req.installation_type, topic=req.topic, standard=req.standard)
    return {"summary": rep.summary(), "findings": [f.__dict__ for f in rep.findings]}


def stats() -> dict:
    rs = repository.ruleset()
    by_status: dict = {}
    for s in rs.standards.values():
        by_status[s["source_status"]] = by_status.get(s["source_status"], 0) + 1
    return {"standards": len(rs.standards), "standards_by_status": by_status, "rules": len(rs.rules),
            "rules_with_check": sum(1 for r in rs.rules if r.get("check")),
            "derived_checks": sum(1 for r in rs.rules if r.get("check", {}).get("derived"))}
