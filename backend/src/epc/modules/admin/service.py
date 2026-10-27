"""Technical console: plugins, skills, system overview, delivery policy and project file trees (admin role only)."""
from epc.core.config import settings
from epc.core.errors import Invalid, NotFound
from epc.modules.admin import repository
from epc.modules.catalogs import public as catalogs
from epc.modules.deliverables import public as deliverables
from epc.modules.identity import public as identity
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


# ---------------------------------------------------------------- DXF layers and standard solutions (global level: the MASTER's)
# The catalogs module keeps the three levels (global, company, project); the console edits the first.
def layers() -> dict:
    return catalogs.layers_view("global")


def save_layers(changes: dict) -> dict:
    return catalogs.layers_save("global", changes)


def reset_layers() -> dict:
    return catalogs.layers_reset("global")


def solutions() -> dict:
    return catalogs.solutions_view("global")


def save_solutions(body: dict) -> dict:
    return catalogs.solutions_save("global", body)


def reset_solutions() -> dict:
    return catalogs.solutions_reset("global")
