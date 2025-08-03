"""add_alias_column_to_tenant_table

Revision ID: 3cc33fca9ab4
Revises: 041ebe3f13e4
Create Date: 2024-02-10 08:14:35.229890

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "3cc33fca9ab4"
down_revision = "041ebe3f13e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "alias",
            pg.VARCHAR(255),
            nullable=True,
            unique=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "alias")
