"""create users tenants table

Revision ID: 1c610eb5666d
Revises: e7dd3fffc2c7
Create Date: 2023-08-24 07:53:11.564083

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "1c610eb5666d"
down_revision = "e7dd3fffc2c7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users_tenants",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.INTEGER, nullable=False),
        sa.Column("tenant_id", pg.INTEGER, nullable=False),
        sa.Column("roles", pg.ARRAY(pg.ENUM("user", "admin", name="tenant_role")), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], onupdate="CASCADE", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], onupdate="CASCADE", ondelete="RESTRICT"),
    )


def downgrade() -> None:
    pass
