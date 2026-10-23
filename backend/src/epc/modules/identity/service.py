"""Who is calling and what they may see. Real authentication (users, organizations, SSO) will live here."""
from epc.core.config import settings


def is_admin() -> bool:
    return settings.role == "admin"


def current_user() -> dict:
    return {"role": settings.role, "name": settings.user, "org": settings.org}
