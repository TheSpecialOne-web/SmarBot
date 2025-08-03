"""add additional_platforms column to tenants table

Revision ID: be52b3f7c89e
Revises: 2db004f0349e
Create Date: 2024-04-23 07:25:10.046917

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "be52b3f7c89e"
down_revision = "2db004f0349e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column("additional_platforms", pg.ARRAY(sa.VARCHAR(255)), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tenants", "additional_platforms")
