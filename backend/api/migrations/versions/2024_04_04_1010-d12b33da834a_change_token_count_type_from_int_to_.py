"""change token_count type from int to float

Revision ID: d12b33da834a
Revises: f9808cd72866
Create Date: 2024-04-04 10:10:38.501033

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d12b33da834a"
down_revision = "f9808cd72866"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation_turns", "token_count", type_=sa.Float)


def downgrade() -> None:
    op.alter_column("conversation_turns", "token_count", type_=sa.Integer)
