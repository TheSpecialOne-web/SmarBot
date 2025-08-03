"""add basic_ai_max_conversation_turns to tenants table

Revision ID: 6d922f7b2112
Revises: 0a6a7fe5b297
Create Date: 2024-09-17 12:22:03.026358

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6d922f7b2112"
down_revision = "0a6a7fe5b297"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("basic_ai_max_conversation_turns", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "basic_ai_max_conversation_turns")
