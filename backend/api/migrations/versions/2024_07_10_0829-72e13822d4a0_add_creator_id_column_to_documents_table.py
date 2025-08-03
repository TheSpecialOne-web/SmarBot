"""add creator_id column to documents table

Revision ID: 72e13822d4a0
Revises: 7568fef1df74
Create Date: 2024-07-10 08:29:16.348320

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "72e13822d4a0"
down_revision = "7568fef1df74"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("creator_id", sa.Integer, sa.ForeignKey("users.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "creator_id")
