"""add org column to bots table

Revision ID: 7ff5c4d46a4d
Revises: 1707e42590df
Create Date: 2023-07-24 08:42:06.153401

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "7ff5c4d46a4d"
down_revision = "1707e42590df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("org_id", pg.VARCHAR(255), nullable=False))
    op.add_column("bots", sa.Column("example_questions", pg.ARRAY(pg.VARCHAR(255)), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "org_id")
    op.drop_column("bots", "example_questions")
