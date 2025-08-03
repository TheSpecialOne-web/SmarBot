"""add_index_name_column_to_tenant_table

Revision ID: 12496604d55d
Revises: 3cc33fca9ab4
Create Date: 2024-02-15 06:17:31.199557

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "12496604d55d"
down_revision = "3cc33fca9ab4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("index_name", pg.VARCHAR(255)),
    )


def downgrade() -> None:
    op.drop_column("tenants", "index_name")
