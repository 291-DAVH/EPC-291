"""Platform audit log and assignments of internal reviewers (inspectors and external auditors) to customer organizations.

`audit_log` records who did what to what and when for every sensitive action (sign-ins, failed sign-ins, accounts, roles, invitations, assignments); it never stores passwords or tokens.
`user_assignments` gives an inspector or an external auditor access to one organization; without an assignment they see nothing.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="SET NULL")),      # organization concerned, when there is one
        sa.Column("actor_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("actor_email", sa.String(254), nullable=False, server_default=""),
        sa.Column("action", sa.String(60), nullable=False),
        sa.Column("target", sa.String(300), nullable=False, server_default=""),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("ip", sa.String(64), nullable=False, server_default=""),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
    )
    op.create_index("ix_audit_at", "audit_log", ["at"])
    op.create_index("ix_audit_org", "audit_log", ["organization_id"])
    op.create_table(
        "user_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("granted_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.UniqueConstraint("user_id", "organization_id", name="uq_assignment_user_org"),
    )
    op.create_index("ix_assignments_user", "user_assignments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_assignments_user", table_name="user_assignments")
    op.drop_table("user_assignments")
    op.drop_index("ix_audit_org", table_name="audit_log")
    op.drop_index("ix_audit_at", table_name="audit_log")
    op.drop_table("audit_log")
