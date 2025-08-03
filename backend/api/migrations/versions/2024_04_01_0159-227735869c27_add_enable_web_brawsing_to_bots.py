"""add enable web browsing to bots

Revision ID: 227735869c27
Revises: 3347bfefb019
Create Date: 2024-04-01 01:59:57.001394

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "227735869c27"
down_revision = "3347bfefb019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("enable_web_browsing", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("bots", "enable_web_browsing")
