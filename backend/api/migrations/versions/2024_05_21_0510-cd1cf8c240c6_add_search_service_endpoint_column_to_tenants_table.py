"""add search_service_endpoint column to tenants table

Revision ID: cd1cf8c240c6
Revises: 21419ef2b28d
Create Date: 2024-05-21 05:10:27.542936

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "cd1cf8c240c6"
down_revision = "21419ef2b28d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("search_service_endpoint", sa.String(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("tenants", "search_service_endpoint")
