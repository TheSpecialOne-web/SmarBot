"""add archived_at column to conversations table

Revision ID: 74f8a4ff9113
Revises: 46fa6321d04a
Create Date: 2024-02-28 07:16:56.055755

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "74f8a4ff9113"
down_revision = "46fa6321d04a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("archived_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("conversations", "archived_at")
