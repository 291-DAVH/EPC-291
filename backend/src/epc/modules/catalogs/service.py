"""The catalogs of drawing at each level: DXF layers and standard solutions, global (MASTER), company and project.

A level sees what the levels above give it plus its own changes, and stores only its own changes: a role or a solution it did not touch keeps following the level above.
"""
from pathlib import Path
from typing import List, Optional

from epc.core.errors import Invalid
from epc.modules.catalogs import repository
from epc.modules.identity import public as identity
from epc.modules.projects import public as projects

LEVELS = ("global", "company", "project")
PARENT = {"global": "factory", "company": "global", "project": "company"}


def _org(level: str, project_dir: Optional[Path]) -> str:
    """The organization a level belongs to: the project's, or the one the caller works in (a company-level request needs one)."""
    slug = projects.read_meta(project_dir).get("org", "") if project_dir is not None else identity.active_org_slug()
    if level == "company" and not slug:
        raise Invalid({"organization": "this level belongs to an organization: work inside one"})
    return slug


def _files(kind: str, level: str, project_dir: Optional[Path]) -> List[Path]:
    """The files that apply up to and including the level."""
    org = _org(level, project_dir) if level != "global" else ""
    full = repository.chain(kind, org, project_dir if level == "project" else None)
    return full


def files(project_dir: Optional[Path] = None) -> dict:
    """What the engine reads for a project (or for nothing in particular): {"layers": [...], "solutions": [...]} in order of authority."""
    org = projects.read_meta(project_dir).get("org", "") if project_dir is not None else ""
    return {kind: repository.chain(kind, org, project_dir) for kind in repository.FILES}


def _target(level: str, project_dir: Optional[Path]) -> str:
    return "global" if level == "global" else f"company:{_org(level, project_dir)}" if level == "company" else projects.project_id(project_dir)


def _audit(action: str, level: str, project_dir: Optional[Path], detail: Optional[dict] = None) -> None:
    org = "" if level == "global" else _org(level, project_dir)
    identity.audit_event(action, target=_target(level, project_dir), org_slug=org, detail=detail)


# ---------------------------------------------------------------- layers
def layers_view(level: str, project_dir: Optional[Path] = None) -> dict:
    """The catalog of layers as this level sees it, what it inherits, what it changed and what a field accepts."""
    from epc_dxf import layers as L
    chain = _files("layers", level, project_dir)
    base, effective = L.load(chain[:-1]), L.load(chain)
    return {"layers": effective, "default": base, "inherits": PARENT[level], "changed": sorted(L.override_of(effective, base)),
            "options": {"lineweights": list(L.LINEWEIGHTS), "linetypes": list(L.LINETYPES)}}


def layers_save(level: str, changes: dict, project_dir: Optional[Path] = None) -> dict:
    """Store the catalog this level sent (role -> attributes): only what differs from what it inherits is kept. Unknown roles and wrong values are refused."""
    from epc_dxf import layers as L
    chain = _files("layers", level, project_dir)
    base = L.load(chain[:-1])
    unknown = sorted(set(changes) - set(base))
    if unknown:
        raise Invalid({"layers": "unknown layer roles: " + ", ".join(unknown)})
    merged = {role: {**a, **{k: v for k, v in (changes.get(role) or {}).items() if k in L.BLANK}} for role, a in base.items()}
    errors = L.validate(merged)
    if errors:
        raise Invalid(errors)
    own = L.override_of(merged, base)
    repository.write(chain[-1], {"layers": own}) if own else repository.delete(chain[-1])
    _audit("drawing_layers_changed", level, project_dir, {"changed": sorted(own)})
    return layers_view(level, project_dir)


def layers_reset(level: str, project_dir: Optional[Path] = None) -> dict:
    repository.delete(_files("layers", level, project_dir)[-1])
    _audit("drawing_layers_reset", level, project_dir)
    return layers_view(level, project_dir)


# ---------------------------------------------------------------- standard solutions
def _symbol_ids() -> list:
    return [s["id"] for s in sld_symbols()]


def sld_symbols() -> list:
    """The symbols of the single-line library a solution may name: id, names and the text slots each one has (the engine owns the library)."""
    import json
    from epc_symbols import library_dir
    catalog = json.loads((library_dir("sld-lv-symbol") / "_catalog.json").read_text(encoding="utf-8-sig"))["symbols"]
    return [{"id": s["id"], "name": {"es": s.get("name_es", ""), "en": s.get("name_en", "")}, "slots": [{"key": x["key"], "example": x.get("example", "")} for x in s.get("label_slots") or []]}
            for s in catalog]


def solutions_view(level: str, project_dir: Optional[Path] = None) -> dict:
    """The document of standard solutions as this level sees it, what it inherits, what it changed and what the editor offers."""
    from epc_calc import solutions as S
    chain = _files("solutions", level, project_dir)
    base, doc = S.load(chain[:-1]), S.load(chain)
    changed = S.override_of(doc, base)
    return {"solutions": doc.get("solutions", {}), "add_ons": doc.get("add_ons", {}), "groups": doc.get("groups", {}), "default": base, "inherits": PARENT[level],
            "changed": sorted({i for part in S.PARTS for i in (changed.get(part) or {})}), "symbols": sld_symbols(),
            "options": {"conditions": list(S.CONDITIONS), "phases": list(S.PHASES), "ranges": list(S.RANGES), "item_keys": list(S.ITEM_KEYS)}}


def solutions_save(level: str, body: dict, project_dir: Optional[Path] = None) -> dict:
    """Store the document this level sent (solutions, add-ons and rules of groups by id; a part that is not sent stays as it is). Only what differs from what it inherits is kept.
    A document that would leave a circuit without a solution is refused."""
    from epc_calc import solutions as S
    chain = _files("solutions", level, project_dir)
    base, current = S.load(chain[:-1]), S.load(chain)
    doc = {part: current.get(part, {}) if body.get(part) is None else body[part] for part in S.PARTS}
    errors = S.validate(doc, _symbol_ids())
    if errors:
        raise Invalid(errors)
    own = S.override_of(doc, base)
    repository.write(chain[-1], own) if own else repository.delete(chain[-1])
    _audit("standard_solutions_changed", level, project_dir, {"changed": sorted({i for part in own.values() for i in part})})
    return solutions_view(level, project_dir)


def solutions_reset(level: str, project_dir: Optional[Path] = None) -> dict:
    repository.delete(_files("solutions", level, project_dir)[-1])
    _audit("standard_solutions_reset", level, project_dir)
    return solutions_view(level, project_dir)


def solutions_digest(project_dir: Optional[Path] = None) -> str:
    """A short fingerprint of the document of standard solutions in force for a project: what a calculation was made with."""
    import hashlib
    import json
    from epc_calc import solutions
    return hashlib.sha256(json.dumps(solutions.load(files(project_dir)["solutions"]), sort_keys=True).encode("utf-8")).hexdigest()[:12]
