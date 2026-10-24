"""Public interface of the masterdata module: what other modules (SLD, issuing...) may read about the office, the clients and who signs a project."""
from pathlib import Path
from typing import Optional

from epc.modules.masterdata import parties, service


def organization() -> dict:
    """The default issuing company (legal name, tax id, contact, has_logo)."""
    return service.organization()


def client(client_id: str) -> Optional[dict]:
    """Saved client by code (case-insensitive) or None."""
    return service.client(client_id)


def people() -> list:
    return service.people()


def logo_path(kind: str) -> Optional[Path]:
    """File of the logo of 'organization' (default issuer), 'issuer-<id>' or 'client-<ID>', None when there is none."""
    try:
        return service.logo_file(kind)
    except Exception:                        # noqa: BLE001 - no logo / unknown client
        return None


def project_parties(project_dir: Path) -> dict:
    """Issuer, client and per-discipline team of a project (resolved)."""
    return parties.view(project_dir)


def titleblock(project_dir: Path, discipline: str = "electrical") -> dict:
    """Company, client and people of the title block for a discipline of the project."""
    return parties.titleblock(project_dir, discipline)


def logos(project_dir: Path) -> dict:
    """{"provider": issuer logo or None, "client": client logo or None} for the project."""
    return parties.logos(project_dir)


def issuer_name(project_dir: Path) -> str:
    return parties.issuer_name(project_dir)


__all__ = ["organization", "client", "people", "logo_path", "project_parties", "titleblock", "logos", "issuer_name"]
