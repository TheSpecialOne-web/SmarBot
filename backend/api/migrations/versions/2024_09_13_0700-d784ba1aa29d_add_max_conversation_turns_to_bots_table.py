"""add max_conversation_turns to bots table

Revision ID: d784ba1aa29d
Revises: ab297f7ddaca
Create Date: 2024-09-13 07:00:17.414730

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d784ba1aa29d"
down_revision = "ab297f7ddaca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("max_conversation_turns", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "max_conversation_turns")
