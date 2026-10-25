"""Identity data: table definitions (a mirror of database/migrations, checked by a test) and the principal that every request carries."""
from dataclasses import dataclass
from typing import Optional, Tuple

import sqlalchemy as sa

metadata = sa.MetaData()

organizations = sa.Table(
    "organizations", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("slug", sa.String(64)), sa.Column("name", sa.String(200)),
    sa.Column("kind", sa.String(20)), sa.Column("seats", sa.Integer), sa.Column("active", sa.Boolean), sa.Column("created_at", sa.DateTime(timezone=True)),
    sa.Column("country", sa.String(2)), sa.Column("tax_id", sa.String(40)), sa.Column("validation", sa.String(20)), sa.Column("profile", sa.JSON))
registrations = sa.Table(
    "registrations", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("email", sa.String(254)), sa.Column("code_hash", sa.String(64)), sa.Column("payload", sa.JSON),
    sa.Column("attempts", sa.Integer), sa.Column("sends", sa.Integer), sa.Column("last_sent_at", sa.DateTime(timezone=True)),
    sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("expires_at", sa.DateTime(timezone=True)))
users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("email", sa.String(254)), sa.Column("username", sa.String(40)), sa.Column("display_name", sa.String(200)),
    sa.Column("locale", sa.String(10)), sa.Column("active", sa.Boolean), sa.Column("password_hash", sa.String(300)),
    sa.Column("platform_role", sa.String(20)), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True)))
memberships = sa.Table(
    "memberships", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("user_id", sa.Uuid),
    sa.Column("role", sa.String(20)), sa.Column("active", sa.Boolean), sa.Column("created_at", sa.DateTime(timezone=True)))
sessions = sa.Table(
    "sessions", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("user_id", sa.Uuid),
    sa.Column("token_hash", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.Column("view_as", sa.String(20)))          # engineering team only: the role of the organization the session is looking at the platform as
identities = sa.Table(
    "identities", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("user_id", sa.Uuid), sa.Column("provider", sa.String(20)), sa.Column("subject", sa.String(200)),
    sa.Column("email", sa.String(254)), sa.Column("created_at", sa.DateTime(timezone=True)))
audit_log = sa.Table(
    "audit_log", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("actor_id", sa.Uuid), sa.Column("actor_email", sa.String(254)),
    sa.Column("action", sa.String(60)), sa.Column("target", sa.String(300)), sa.Column("detail", sa.JSON), sa.Column("ip", sa.String(64)), sa.Column("at", sa.DateTime(timezone=True)))
user_assignments = sa.Table(
    "user_assignments", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("user_id", sa.Uuid), sa.Column("granted_by", sa.Uuid),
    sa.Column("granted_at", sa.DateTime(timezone=True)))
invitations = sa.Table(
    "invitations", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("email", sa.String(254)),
    sa.Column("role", sa.String(20)), sa.Column("token_hash", sa.String(64)), sa.Column("invited_by", sa.Uuid),
    sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("accepted_at", sa.DateTime(timezone=True)))

MASTER_EMAIL = "master@dev.invalid"      # the development-only MASTER account; the domain is reserved so nobody can register it
ORG_KINDS = ("individual", "company")
ORG_ROLES = ("owner", "admin", "member")
PLATFORM_ROLES = ("user", "admin", "standards", "inspector", "auditor")      # customer | engineering staff | norm reviewer | internal inspector | external auditor
NO_ORG_ROLES = ("admin", "standards", "inspector", "auditor")        # belong to no customer organization
ASSIGNED_ROLES = ("inspector", "auditor")                            # see only the organizations assigned to them


@dataclass(frozen=True)
class Principal:
    """Who is making the request. `role` is the platform role: `admin` (the engineering office) or `user` (a customer)."""
    authenticated: bool = False
    role: str = "user"
    name: str = ""
    email: str = ""
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    org_slug: str = ""
    org_name: str = ""
    org_kind: str = ""
    org_role: str = ""          # owner | admin | member | "" (internal accounts and anonymous)
    username: str = ""
    has_password: bool = True           # False for an account created through a provider that has not set one
    assigned: Tuple[str, ...] = ()      # inspector / auditor: slugs of the organizations assigned to them
    simulated: bool = False
    org_validation: str = ""          # validated | pending | rejected: whether the platform team confirmed the company's registration
    can_view_as: bool = False           # the engineering team can look at the platform as an organization, a member of it or an independent professional
    viewing_as: str = ""                # owner | admin | member while doing so
