"""add search_method column to bots table

Revision ID: f6e0a9d2ac6d
Revises: 6d573a5befb8
Create Date: 2023-09-28 11:50:56.567807

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "f6e0a9d2ac6d"
down_revision = "6d573a5befb8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("search_method", pg.VARCHAR(255), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "search_method")
