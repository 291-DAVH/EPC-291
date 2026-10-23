"""Technical console: plugins, skills, system overview, delivery policy and project file trees (admin role only)."""
from epc.core.config import settings
from epc.core.errors import NotFound
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
