"""change queries length

Revision ID: 46fa6321d04a
Revises: b9d473426713
Create Date: 2024-02-16 02:34:28.256757

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "46fa6321d04a"
down_revision = "b9d473426713"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation_turns", "queries", type_=pg.ARRAY(pg.VARCHAR(511)))


def downgrade() -> None:
    op.alter_column("conversation_turns", "queries", type_=pg.ARRAY(pg.VARCHAR(255)))
