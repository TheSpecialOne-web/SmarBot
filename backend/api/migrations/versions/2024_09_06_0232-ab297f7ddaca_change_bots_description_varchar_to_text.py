"""change bots description VARCHAR to TEXT

Revision ID: ab297f7ddaca
Revises: 8ba38f5bf5cc
Create Date: 2024-09-06 02:32:53.819682

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "ab297f7ddaca"
down_revision = "8ba38f5bf5cc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(table_name="bots", column_name="description", type_=pg.TEXT())


def downgrade() -> None:
    op.alter_column(table_name="bots", column_name="description", type_=pg.VARCHAR(length=255))
