"""Baseline: organizations, users, memberships, projects, deliverables index, ledger.

Platform state only (ADR-0006). Engineering artifacts stay in project files; these tables index them.
Multi-tenancy: every table except `organizations` and `users` carries `organization_id`.

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def _org_fk() -> sa.Column:
    return sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False, server_default="company"),     # individual | company
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False, server_default="es-AR"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),         # user | admin
        sa.UniqueConstraint("organization_id", "user_id", name="uq_membership_org_user"),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("client_code", sa.String(40), nullable=False),
        sa.Column("project_code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("jurisdiction", sa.String(8), nullable=False),
        sa.Column("methodology", sa.String(20), nullable=False, server_default="pm2"),
        sa.Column("phase", sa.String(20), nullable=False, server_default="conceptual"),
        sa.Column("state", sa.String(20), nullable=False, server_default="active"),
        sa.Column("path", sa.String(500), nullable=False),                               # project folder (system of record for files)
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.UniqueConstraint("organization_id", "client_code", "project_code", name="uq_project_code"),
    )
    op.create_table(
        "deliverables",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("revision", sa.String(10), nullable=False, server_default="A"),
        sa.Column("format", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="planned"),
        sa.Column("sha256", sa.String(64)),                                              # reconciliation with the files
        sa.Column("due", sa.Date()),
        sa.Column("delivered_on", sa.Date()),
        sa.UniqueConstraint("project_id", "code", "revision", name="uq_deliverable_revision"),
    )
    op.create_index("ix_deliverables_project", "deliverables", ["project_id"])
    op.create_table(
        "ledger_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        _org_fk(),
        sa.Column("project_id", sa.Uuid(), sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("manifest_sha256", sa.String(64)),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index("ix_ledger_project_at", "ledger_entries", ["project_id", "at"])


def downgrade() -> None:
    op.drop_index("ix_ledger_project_at", table_name="ledger_entries")
    op.drop_table("ledger_entries")
    op.drop_index("ix_deliverables_project", table_name="deliverables")
    for t in ("deliverables", "projects", "memberships", "users", "organizations"):
        op.drop_table(t)
