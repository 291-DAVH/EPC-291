"""Public interface of the identity module (the only thing other modules may import)."""
from epc.modules.identity.guard import install_role_guard
from epc.modules.identity.service import current_user, is_admin

PUBLIC_PATHS = {"/api/health", "/api/me"}

__all__ = ["install_role_guard", "current_user", "is_admin", "PUBLIC_PATHS"]
