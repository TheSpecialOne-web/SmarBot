"""add attachment token to tenants table

Revision ID: 777724564a2b
Revises: 072e8b35d5e0
Create Date: 2024-06-25 06:50:56.193449

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "777724564a2b"
down_revision = "072e8b35d5e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("max_attachment_token", sa.Integer(), nullable=False, server_default="8000"))


def downgrade() -> None:
    op.drop_column("tenants", "max_attachment_token")
