"""add enable url scraping column to tenants table

Revision ID: 7471db7c678b
Revises: e951fbe3c462
Create Date: 2024-05-14 09:45:08.561726

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7471db7c678b"
down_revision = "e951fbe3c462"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("enable_url_scraping", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("tenants", "enable_url_scraping")
