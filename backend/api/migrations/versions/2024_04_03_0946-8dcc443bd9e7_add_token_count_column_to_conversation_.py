"""add token_count column to conversation_turns table

Revision ID: 8dcc443bd9e7
Revises: de283860841e
Create Date: 2024-04-03 09:46:23.927574

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8dcc443bd9e7"
down_revision = "de283860841e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("conversation_turns", sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("conversation_turns", "token_count")
