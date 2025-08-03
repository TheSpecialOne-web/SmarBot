"""add archived_at column to bots table

Revision ID: c43957229095
Revises: ac24952ff440
Create Date: 2024-04-09 04:08:42.680169

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c43957229095"
down_revision = "ac24952ff440"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("archived_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "archived_at")
