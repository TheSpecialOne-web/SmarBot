"""create policies table

Revision ID: 1707e42590df
Revises: 7e10a870263a
Create Date: 2023-07-10 11:17:39.372483

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "1707e42590df"
down_revision = "7e10a870263a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "policies",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("action", pg.ENUM("read", "write", name="action"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("policies")
