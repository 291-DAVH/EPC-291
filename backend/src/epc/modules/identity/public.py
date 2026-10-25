"""Public interface of the identity module (the only thing other modules may import)."""
from epc.modules.identity.guard import install_role_guard
from epc.modules.identity.service import active_org_slug, audit_event, can, current_user, is_admin, org_exists, org_for_new_project, org_name, org_profile, visible_orgs

PUBLIC_PATHS = {"/api/health", "/api/me"}

__all__ = ["active_org_slug", "org_name", "org_profile", "audit_event", "can", "install_role_guard", "current_user", "is_admin", "org_exists", "org_for_new_project", "visible_orgs", "PUBLIC_PATHS"]
