"""add status column to tenants table

Revision ID: d0b3112d377c
Revises: 6c9634ff7734
Create Date: 2024-05-01 07:41:18.315046

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "d0b3112d377c"
down_revision = "6c9634ff7734"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("status", pg.VARCHAR(255), nullable=False, server_default="trial"))


def downgrade() -> None:
    op.drop_column("tenants", "status")
