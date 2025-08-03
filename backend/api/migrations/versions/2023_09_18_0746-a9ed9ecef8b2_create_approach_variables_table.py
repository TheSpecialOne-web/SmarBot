"""create_approach_valiables_table

Revision ID: a9ed9ecef8b2
Revises: 5e050de8619c
Create Date: 2023-09-18 07:46:51.501769

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "a9ed9ecef8b2"
down_revision = "5e050de8619c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "approach_variables",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("name", pg.VARCHAR(255), nullable=False),
        sa.Column("value", pg.VARCHAR(511), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("approach_variables")
