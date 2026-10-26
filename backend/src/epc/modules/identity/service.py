"""Who is calling and what they may see (US-0018).

Two modes (`EPC_AUTH`):
* `simulated` (development default): nobody logs in; the role comes from EPC_ROLE, exactly as before. No database is touched.
* `required` (production default): every request carries a session (cookie `epc_session` or `Authorization: Bearer`). Accounts live in the database.

Accounts: a *user* belongs to one or more *organizations*. An organization is an individual subscription (one seat) or a company
subscription (a group of people, `seats`). Inside an organization a member is `owner` (manages the people) or `member`. The platform staff
(the engineering office) are users with platform role `admin`; they see every organization. A customer sees only the projects of the active
organization of the session. Code running outside a request (background jobs) is trusted and is not filtered.

The code lives in cohesive modules (passwords, checks, throttle, sessions, accounts, invitations, staff, registration, social);
this module keeps the names callers have always used (`identity.service.login`, ...) so none of them changes."""

import datetime as dt  # noqa: F401 - callers reach these through the facade
import time  # noqa: F401

from epc.modules.identity import repository as repo  # noqa: F401
from epc.modules.identity.oauth import OAuthError  # noqa: F401

from epc.modules.identity.passwords import (  # noqa: F401
    MIN_PASSWORD,
    _DUMMY_HASH,
    _check_password,
    hash_password,
    token_hash,
    verify_password,
)
from epc.modules.identity.checks import (  # noqa: F401
    EMAIL,
    RESERVED_ALIASES,
    USERNAME,
    _check_email,
    _check_username,
    _slug,
)
from epc.modules.identity.throttle import (  # noqa: F401
    _fails,
    _fails_lock,
    _throttle,
    reset_throttle,
)
from epc.modules.identity.sessions import (  # noqa: F401
    COOKIE,
    LOOPBACK,
    VIEW_AS_ROLES,
    _ctx,
    _email_of,
    _from_session,
    _master_user,
    _only_owner,
    _open_session,
    _organizations,
    account_type,
    activate,
    active_org_slug,
    audit,
    audit_event,
    audit_log,
    can,
    change_password,
    current,
    current_user,
    deactivate,
    is_admin,
    login,
    logout,
    master_enabled,
    me,
    org_exists,
    org_for_new_project,
    org_name,
    principal_for_request,
    replace_principal,
    require_manager,
    set_username,
    simulated_principal,
    switch_org,
    token_from,
    view_as,
    visible_orgs,
)
from epc.modules.identity.accounts import (  # noqa: F401
    _last_owner,
    _member_view,
    bootstrap_admin,
    organization,
    remove_member,
    signup,
    update_member,
)
from epc.modules.identity.invitations import (  # noqa: F401
    INVITATION_DAYS,
    _invite_url,
    _new_invitation,
    _open_invitation,
    _seats_left,
    accept_invitation,
    cancel_invitation,
    invitation_info,
    invite,
)
from epc.modules.identity.staff import (  # noqa: F401
    VALIDATIONS,
    _org_view,
    org_profile,
    reset_accounts,
    staff_create_org,
    staff_create_user,
    staff_orgs,
    staff_set_assignments,
    staff_set_password,
    staff_update_org,
    staff_update_user,
    staff_users,
)
from epc.modules.identity.registration import (  # noqa: F401
    CODE_ATTEMPTS,
    CODE_MINUTES,
    COMPANY_SEATS,
    RESEND_MAX,
    RESEND_SECONDS,
    _code_hash,
    _conflicts_company,
    _mask,
    _registration,
    _send_code,
    company_register,
    company_resend,
    company_verify,
    terms,
)
from epc.modules.identity.social import (  # noqa: F401
    _customer_session,
    _display_name,
    _social_invitation,
    identities_of,
    oauth_callback,
    oauth_complete,
    oauth_pending,
    oauth_providers,
    oauth_start,
    unlink_identity,
)
