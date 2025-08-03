"""add_container_name_column_to_tenant_table

Revision ID: f9808cd72866
Revises: 0e1d85d6057b
Create Date: 2024-04-04 09:30:04.390855

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "f9808cd72866"
down_revision = "0e1d85d6057b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("container_name", pg.VARCHAR(255)),
    )


def downgrade() -> None:
    op.drop_column("tenants", "container_name")
