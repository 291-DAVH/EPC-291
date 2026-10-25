"""Company registration: tax identity, address, validation by the platform team, and the pending registrations awaiting the e-mail code.

`organizations.country`, `tax_id`, `validation` (validated | pending | rejected; every organization that existed is validated) and `profile` (address, contact e-mail, terms
accepted, who validated). `registrations` holds a sign-up between the form and the code sent to the company's e-mail: nothing is created as an account until the code is entered.

Revision ID: 0006
Revises: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    with op.batch_alter_table("organizations") as b:
        b.add_column(sa.Column("country", sa.String(2)))
        b.add_column(sa.Column("tax_id", sa.String(40)))
        b.add_column(sa.Column("validation", sa.String(20), nullable=False, server_default="validated"))
        b.add_column(sa.Column("profile", sa.JSON()))
    op.create_index("ix_organizations_tax", "organizations", ["country", "tax_id"])
    op.create_table(
        "registrations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sends", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=NOW),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_registrations_email", "registrations", ["email"])


def downgrade() -> None:
    op.drop_index("ix_registrations_email", table_name="registrations")
    op.drop_table("registrations")
    op.drop_index("ix_organizations_tax", table_name="organizations")
    with op.batch_alter_table("organizations") as b:
        b.drop_column("profile")
        b.drop_column("validation")
        b.drop_column("tax_id")
        b.drop_column("country")
