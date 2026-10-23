"""Public interface of the masterdata module: what other modules (SLD, projects...) may read about the office."""
from pathlib import Path
from typing import Optional

from epc.modules.masterdata import service


def organization() -> dict:
    """Company profile entered once (legal name, tax id, contact, has_logo)."""
    return service.organization()


def client(client_id: str) -> Optional[dict]:
    """Saved client by code (case-insensitive) or None."""
    return service.client(client_id)


def people() -> list:
    return service.people()


def logo_path(kind: str) -> Optional[Path]:
    """File of the logo of 'organization' or 'client-<ID>', None when there is none."""
    try:
        return service.logo_file(kind)
    except Exception:                        # noqa: BLE001 - no logo / unknown client
        return None


__all__ = ["organization", "client", "people", "logo_path"]
