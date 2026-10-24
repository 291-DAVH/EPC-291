"""Identity data: table definitions (a mirror of database/migrations, checked by a test) and the principal that every request carries."""
from dataclasses import dataclass
from typing import Optional

import sqlalchemy as sa

metadata = sa.MetaData()

organizations = sa.Table(
    "organizations", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("slug", sa.String(64)), sa.Column("name", sa.String(200)),
    sa.Column("kind", sa.String(20)), sa.Column("seats", sa.Integer), sa.Column("active", sa.Boolean), sa.Column("created_at", sa.DateTime(timezone=True)))
users = sa.Table(
    "users", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("email", sa.String(254)), sa.Column("display_name", sa.String(200)),
    sa.Column("locale", sa.String(10)), sa.Column("active", sa.Boolean), sa.Column("password_hash", sa.String(300)),
    sa.Column("platform_role", sa.String(20)), sa.Column("last_login_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True)))
memberships = sa.Table(
    "memberships", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("user_id", sa.Uuid),
    sa.Column("role", sa.String(20)), sa.Column("active", sa.Boolean), sa.Column("created_at", sa.DateTime(timezone=True)))
sessions = sa.Table(
    "sessions", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("user_id", sa.Uuid),
    sa.Column("token_hash", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("expires_at", sa.DateTime(timezone=True)))
invitations = sa.Table(
    "invitations", metadata,
    sa.Column("id", sa.Uuid, primary_key=True), sa.Column("organization_id", sa.Uuid), sa.Column("email", sa.String(254)),
    sa.Column("role", sa.String(20)), sa.Column("token_hash", sa.String(64)), sa.Column("invited_by", sa.Uuid),
    sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("expires_at", sa.DateTime(timezone=True)), sa.Column("accepted_at", sa.DateTime(timezone=True)))

ORG_KINDS = ("individual", "company")
ORG_ROLES = ("owner", "member")
PLATFORM_ROLES = ("user", "admin", "standards")      # customer | engineering staff | norm reviewer (sees only the norms review area)
NO_ORG_ROLES = ("admin", "standards")


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
    org_role: str = ""          # owner | member | "" (staff and anonymous)
    simulated: bool = False
