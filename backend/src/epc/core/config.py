"""Runtime configuration. One mutable `settings` object read at call time (tests replace its fields).

Environment: EPC_ROLE (user|admin), EPC_ENV (dev|production), EPC_PROJECTS, EPC_DEV_KNOWLEDGE,
EPC_USER, EPC_ORG, EPC_REPO (repository root when the package is not run from a checkout).
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _find_repo() -> Path:
    env = os.environ.get("EPC_REPO")
    if env:
        return Path(env)
    for p in Path(__file__).resolve().parents:
        if (p / "engine").is_dir() and (p / "claude").is_dir():
            return p
    raise RuntimeError("EPC-291 repository root not found; set EPC_REPO")


def _first(*paths: Path) -> Path:
    for p in paths:
        if p.exists():
            return p
    return paths[0]


@dataclass
class Settings:
    repo: Path
    engine: Path
    plugins_dir: Path
    skills_dir: Path
    schemas_dir: Path
    template_dir: Path
    methodologies_dir: Path
    build_tool: Path
    skill_check_tool: Path
    projects_dir: Path
    dev_knowledge: Path
    env: str = "dev"
    role: str = "user"          # "admin" unlocks the technical console; end users never see internals
    user: str = ""
    org: str = ""

    @classmethod
    def from_env(cls, repo: Optional[Path] = None) -> "Settings":
        repo = repo or _find_repo()
        local = repo / "local"
        return cls(
            repo=repo,
            engine=repo / "engine",
            plugins_dir=repo / "claude" / "plugins",
            skills_dir=repo / "claude" / "skills",
            schemas_dir=repo / "shared" / "schemas",
            template_dir=repo / "management" / "templates" / "project-skeleton",
            methodologies_dir=_first(repo / "management" / "methodologies", repo / "platform" / "methodologies"),
            build_tool=_first(repo / "tools" / "build" / "epc_build.py", repo / "platform" / "tools" / "build" / "epc_build.py"),
            skill_check_tool=_first(repo / "tools" / "ci" / "check_skill_conflicts.py", repo / "platform" / "tools" / "ci" / "check_skill_conflicts.py"),
            projects_dir=Path(os.environ.get("EPC_PROJECTS", local / "projects")),
            dev_knowledge=Path(os.environ.get("EPC_DEV_KNOWLEDGE", local / "dev-knowledge")),
            env=os.environ.get("EPC_ENV", "dev"),
            role=os.environ.get("EPC_ROLE", "user"),
            user=os.environ.get("EPC_USER", ""),
            org=os.environ.get("EPC_ORG", ""),
        )


settings = Settings.from_env()
