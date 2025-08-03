"""add allowed_ips column to tenants table

Revision ID: 762c075b3d19
Revises: 5ceb7bc13ba2
Create Date: 2024-02-01 13:02:21.776568

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "762c075b3d19"
down_revision = "5ceb7bc13ba2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(
            "allowed_ips",
            pg.ARRAY(sa.String(length=255)),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("tenants", "allowed_ips")
