"""add enable_api_integrations column to tenants table

Revision ID: f2589876f3cb
Revises: accc24601a3c
Create Date: 2024-06-05 01:12:53.452263

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f2589876f3cb"
down_revision = "accc24601a3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants", sa.Column("enable_api_integrations", sa.Boolean(), nullable=False, server_default="false")
    )


def downgrade() -> None:
    op.drop_column("tenants", "enable_api_integrations")
