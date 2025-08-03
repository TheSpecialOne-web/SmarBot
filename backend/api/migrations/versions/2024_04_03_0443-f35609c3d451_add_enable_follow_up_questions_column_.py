"""add enable_follow_up_questions column to bots table

Revision ID: f35609c3d451
Revises: b0da9a64d4dc
Create Date: 2024-04-03 04:43:56.922049

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f35609c3d451"
down_revision = "b0da9a64d4dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("enable_follow_up_questions", sa.Boolean(), nullable=False, server_default="true"))


def downgrade() -> None:
    op.drop_column("bots", "enable_follow_up_questions")
