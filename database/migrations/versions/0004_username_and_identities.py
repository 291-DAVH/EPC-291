"""Sign-in alias (username) and linked social identities.

`users.username` is an optional alias (stored lowercase, unique) that can be used instead of the email to sign in. `identities` links a user to an account at an
external provider (Google, GitHub, Facebook, LinkedIn): the pair (provider, subject) is the provider's own id for the person and is unique. A user created through a
provider has no password until they set one.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    with op.batch_alter_table("users") as b:
        b.add_column(sa.Column("username", sa.String(40)))
    op.create_index("ux_users_username", "users", ["username"], unique=True)
    op.create_table(
        "identities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("email", sa.String(254), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.UniqueConstraint("provider", "subject", name="uq_identity_provider_subject"),
    )
    op.create_index("ix_identities_user", "identities", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_identities_user", table_name="identities")
    op.drop_table("identities")
    op.drop_index("ux_users_username", table_name="users")
    with op.batch_alter_table("users") as b:
        b.drop_column("username")
