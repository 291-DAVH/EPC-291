"""Runtime configuration. One mutable `settings` object read at call time (tests replace its fields).

Environment: EPC_ROLE (user|admin), EPC_ENV (dev|production), EPC_PROJECTS, EPC_DEV_KNOWLEDGE,
EPC_DATA, EPC_USER, EPC_ORG, EPC_REPO (repository root when the package is not run from a checkout),
EPC_DATABASE_URL, EPC_AUTH (simulated|required; production defaults to required), EPC_SIGNUP (closed|open),
EPC_SESSION_HOURS, EPC_COOKIE_SECURE (1 behind HTTPS), EPC_PUBLIC_URL (customer app address, for invitation links).
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
    data_dir: Path              # master data: company profile, clients, people, logos (EPC_DATA)
    database_url: str = ""      # identity and platform state (EPC_DATABASE_URL); empty = SQLite file in local/
    env: str = "dev"
    role: str = "user"          # "admin" unlocks the technical console; end users never see internals
    user: str = ""
    org: str = ""
    auth: str = "simulated"     # "simulated": role comes from EPC_ROLE (no login); "required": real accounts and sessions
    signup: str = "closed"      # "open": anyone may create an individual or company account; "closed": accounts by staff or invitation
    session_hours: int = 12
    cookie_secure: bool = False
    public_url: str = "http://localhost:5173"      # address of the customer app, used in invitation links (EPC_PUBLIC_URL)

    @classmethod
    def from_env(cls, repo: Optional[Path] = None) -> "Settings":
        repo = repo or _find_repo()
        local = repo / "local"
        env = os.environ.get("EPC_ENV", "dev")
        return cls(
            repo=repo,
            engine=repo / "engine",
            plugins_dir=repo / "claude" / "plugins",
            skills_dir=repo / "claude" / "skills",
            schemas_dir=repo / "shared" / "schemas",
            template_dir=repo / "management" / "templates" / "project-skeleton",
            methodologies_dir=repo / "management" / "methodologies",
            build_tool=repo / "tools" / "build" / "epc_build.py",
            skill_check_tool=repo / "tools" / "ci" / "check_skill_conflicts.py",
            projects_dir=Path(os.environ.get("EPC_PROJECTS", local / "projects")),
            dev_knowledge=Path(os.environ.get("EPC_DEV_KNOWLEDGE", local / "dev-knowledge")),
            data_dir=Path(os.environ.get("EPC_DATA", local / "data")),
            database_url=os.environ.get("EPC_DATABASE_URL", ""),
            env=env,
            role=os.environ.get("EPC_ROLE", "user"),
            user=os.environ.get("EPC_USER", ""),
            org=os.environ.get("EPC_ORG", ""),
            auth=os.environ.get("EPC_AUTH") or ("required" if env == "production" else "simulated"),
            signup=os.environ.get("EPC_SIGNUP", "closed"),
            session_hours=int(os.environ.get("EPC_SESSION_HOURS", "12")),
            cookie_secure=os.environ.get("EPC_COOKIE_SECURE", "") == "1",
            public_url=os.environ.get("EPC_PUBLIC_URL", "http://localhost:5173").rstrip("/"),
        )


settings = Settings.from_env()
