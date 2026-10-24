"""Session "view as": the engineering team looks at the platform as an organization, a member of it or an independent professional.

`sessions.view_as` holds the role (owner, admin or member) of the organization the session is looking at the platform as; empty is the team's own view.

Revision ID: 0005
Revises: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sessions") as b:
        b.add_column(sa.Column("view_as", sa.String(20)))


def downgrade() -> None:
    with op.batch_alter_table("sessions") as b:
        b.drop_column("view_as")
