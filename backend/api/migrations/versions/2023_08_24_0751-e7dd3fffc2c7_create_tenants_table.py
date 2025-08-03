"""create tenants table

Revision ID: e7dd3fffc2c7
Revises: aee9e2837fe8
Create Date: 2023-08-24 07:51:47.392111

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "e7dd3fffc2c7"
down_revision = "aee9e2837fe8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("name", pg.VARCHAR(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("tenants")
