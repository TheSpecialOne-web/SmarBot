"""create bots table

Revision ID: 7e10a870263a
Revises:
Create Date: 2023-07-10 10:41:29.992257

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "7e10a870263a"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bots",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("name", pg.VARCHAR(255), nullable=False),
        sa.Column("description", pg.VARCHAR(255), nullable=False),
        sa.Column("index_name", pg.VARCHAR(255), nullable=False),
        sa.Column("container_name", pg.VARCHAR(255), nullable=False),
        sa.Column("approach", pg.VARCHAR(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("bots")
