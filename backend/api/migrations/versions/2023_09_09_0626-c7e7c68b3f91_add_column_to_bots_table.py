"""add_column_to_bots_table

Revision ID: c7e7c68b3f91
Revises: ace80c4ab6ac
Create Date: 2023-09-09 06:26:18.379710

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "c7e7c68b3f91"
down_revision = "ace80c4ab6ac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("prompts", pg.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "prompts")
