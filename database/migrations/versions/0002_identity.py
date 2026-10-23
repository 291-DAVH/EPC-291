"""Identity: passwords, staff role, seats, active flags, sessions and invitations (US-0018).

Individual and corporate subscriptions are both organizations: `kind` individual has one seat, `company` is a group of people (`seats`).
Membership roles become `owner` (manages the organization and its people) and `member`. The platform staff (the engineering office) are users
with `platform_role = 'admin'`; they are not tied to a customer organization.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    with op.batch_alter_table("users") as b:
        b.add_column(sa.Column("password_hash", sa.String(300)))
        b.add_column(sa.Column("platform_role", sa.String(20), nullable=False, server_default="user"))      # user | admin (staff)
        b.add_column(sa.Column("last_login_at", sa.DateTime(timezone=True)))
    with op.batch_alter_table("organizations") as b:
        b.add_column(sa.Column("seats", sa.Integer(), nullable=False, server_default="1"))
        b.add_column(sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    with op.batch_alter_table("memberships") as b:
        b.add_column(sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
        b.add_column(sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW))
        b.alter_column("role", existing_type=sa.String(20), server_default="member")
    op.execute("UPDATE memberships SET role = 'owner' WHERE role = 'admin'")
    op.execute("UPDATE memberships SET role = 'member' WHERE role = 'user'")

    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE")),   # active organization (null for staff)
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),                              # SHA-256 of the token; the token is never stored
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sessions_user", "sessions", ["user_id"])
    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("invited_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_invitations_org", "invitations", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_invitations_org", table_name="invitations")
    op.drop_table("invitations")
    op.drop_index("ix_sessions_user", table_name="sessions")
    op.drop_table("sessions")
    op.execute("UPDATE memberships SET role = 'user' WHERE role = 'member'")
    op.execute("UPDATE memberships SET role = 'admin' WHERE role = 'owner'")
    with op.batch_alter_table("memberships") as b:
        b.alter_column("role", existing_type=sa.String(20), server_default="user")
        b.drop_column("created_at")
        b.drop_column("active")
    with op.batch_alter_table("organizations") as b:
        b.drop_column("active")
        b.drop_column("seats")
    with op.batch_alter_table("users") as b:
        b.drop_column("last_login_at")
        b.drop_column("platform_role")
        b.drop_column("password_hash")
