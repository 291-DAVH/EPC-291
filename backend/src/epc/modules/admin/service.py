"""Technical console: plugins, skills, system overview, delivery policy and project file trees (admin role only)."""
from epc.core.config import settings
from epc.core.errors import Invalid, NotFound
from epc.modules.admin import repository
from epc.modules.deliverables import public as deliverables
from epc.modules.knowledge import public as knowledge
from epc.modules.projects import public as projects


def plugins() -> list:
    return list(repository.plugins())


def plugin(pid: str) -> dict:
    for p in repository.plugins():
        if p["id"] == pid:
            return {**p, "readme": repository.plugin_readme(pid)}
    raise NotFound("plugin not found")


def skills() -> list:
    return list(repository.skills())


def overview() -> dict:
    ps = plugins()
    return {"env": settings.env, "plugins": len(ps), "plugins_pending": sum(1 for p in ps if p["status"] != "active"),
            "skills": len(skills()), **knowledge.rules_stats(), "projects": projects.project_count(),
            "skill_conflicts": repository.skill_conflicts()}


def policy() -> dict:
    return deliverables.format_policy()


def project_tree(project_id: str, area: str, depth: int) -> dict:
    return projects.project_tree(project_id, area, depth, deliverables.format_policy().get("formats", {}))


# ---------------------------------------------------------------- DXF layers (global catalog)
def layers() -> dict:
    """The catalog of layers every drawing is delivered with: the effective one, the default one, what changed and the values a field accepts."""
    from epc_dxf import layers as L
    effective = L.load(settings.layers_file)
    return {"layers": effective, "default": L.defaults(), "changed": sorted(L.override_of(effective)),
            "options": {"lineweights": list(L.LINEWEIGHTS), "linetypes": list(L.LINETYPES)}}


def save_layers(changes: dict) -> dict:
    """Store the catalog the MASTER sent (role -> attributes); only what differs from the default is kept. Unknown roles and wrong values are refused."""
    from epc_dxf import layers as L
    base = L.defaults()
    unknown = sorted(set(changes) - set(base))
    if unknown:
        raise Invalid({"layers": "unknown layer roles: " + ", ".join(unknown)})
    merged = {role: {**a, **{k: v for k, v in (changes.get(role) or {}).items() if k in L.BLANK}} for role, a in base.items()}
    errors = L.validate(merged)
    if errors:
        raise Invalid(errors)
    repository.save_layers_override(L.override_of(merged))
    return layers()


def reset_layers() -> dict:
    repository.reset_layers()
    return layers()
