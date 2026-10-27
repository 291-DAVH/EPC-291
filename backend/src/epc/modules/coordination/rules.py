"""The separations between disciplines at each level: the engine's defaults, the company's and the project's. A level stores only its own rules; a later level replaces
a rule with the same pair of disciplines and kinds (or removes it with `disabled`)."""
from pathlib import Path
from typing import Any, Dict, List, Optional

from epc.core.errors import Invalid
from epc.core.fsutil import read_json, write_json
from epc.modules.coordination import repository
from epc.modules.identity import public as identity
from epc.modules.projects import public as projects

NUMBER = (int, float)


def _plan():
    from epc_plan import clash
    return clash


def _org(project_dir: Optional[Path]) -> str:
    slug = projects.read_meta(project_dir).get("org", "") if project_dir is not None else identity.active_org_slug()
    if not slug:
        raise Invalid({"organization": "the company's rules belong to an organization: work inside one"})
    return slug


def _file(level: str, project_dir: Optional[Path]) -> Path:
    return repository.base(project_dir) / "rules.json" if level == "project" else repository.company_rules_file(_org(project_dir))


def _read(path: Path) -> List[Dict[str, Any]]:
    return (read_json(path, {}) or {}).get("rules", [])


def effective(project_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """The rules in force: the engine's, then the company's and the project's."""
    clash = _plan()
    org = projects.read_meta(project_dir).get("org", "") if project_dir is not None else ""
    layers = [clash.default_rules(), _read(repository.company_rules_file(org)) if org else []]
    if project_dir is not None:
        layers.append(_read(repository.base(project_dir) / "rules.json"))
    return clash.merge_rules(*layers)


def _discipline_ok(value: Any) -> bool:
    return isinstance(value, str) and (value == "*" or bool(repository.DISCIPLINE.match(value)))


def _clearance_ok(value: Any) -> bool:
    return isinstance(value, NUMBER) and not isinstance(value, bool) and value >= 0


def _kinds_ok(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(k, str) for k in value)


def _rule_errors(i: int, r: Dict[str, Any]) -> Dict[str, str]:
    out = {f"rules[{i}].{key}": "a discipline id or *" for key in ("a", "b") if not _discipline_ok(r.get(key, "*"))}
    if not _clearance_ok(r.get("clearance_m", 0.0)):
        out[f"rules[{i}].clearance_m"] = "a distance in metres, zero or more"
    out.update({f"rules[{i}].{key}": "a list of kind ids" for key in ("kinds_a", "kinds_b") if not _kinds_ok(r.get(key, []))})
    return out


def validate(rules: List[Dict[str, Any]]) -> None:
    errors: Dict[str, str] = {}
    for i, r in enumerate(rules):
        errors.update(_rule_errors(i, r))
    if errors:
        raise Invalid(errors)


def view(level: str, project_dir: Optional[Path] = None) -> dict:
    """What the level sees: the rules it inherits, its own, and what applies in the end."""
    clash = _plan()
    own = _read(_file(level, project_dir))
    if level == "project":
        org = projects.read_meta(project_dir).get("org", "")
        inherited = clash.merge_rules(clash.default_rules(), _read(repository.company_rules_file(org)) if org else [])
    else:
        inherited = clash.default_rules()
    return {"default": clash.default_rules(), "inherited": inherited, "own": own, "effective": clash.merge_rules(inherited, own)}


def save(level: str, rules: List[Dict[str, Any]], project_dir: Optional[Path] = None) -> dict:
    validate(rules)
    path = _file(level, project_dir)
    write_json(path, {"schema_version": "1.0", "rules": rules}) if rules else path.unlink(missing_ok=True)
    org = projects.read_meta(project_dir).get("org", "") if project_dir is not None else _org(None)
    identity.audit_event("clash_rules_changed", target=projects.project_id(project_dir) if level == "project" else f"company:{org}", org_slug=org, detail={"rules": len(rules)})
    return view(level, project_dir)
