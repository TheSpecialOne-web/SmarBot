"""alter column type of user_input and bot_output to text

Revision ID: 2c0e1a31c8ad
Revises: fbd931b7a257
Create Date: 2024-03-27 08:25:41.125713

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "2c0e1a31c8ad"
down_revision = "fbd931b7a257"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation_turns", "user_input", type_=pg.TEXT)
    op.alter_column("conversation_turns", "bot_output", type_=pg.TEXT)


def downgrade() -> None:
    op.alter_column("conversation_turns", "user_input", type_=pg.VARCHAR(1023))
    op.alter_column("conversation_turns", "bot_output", type_=pg.VARCHAR(1023))
