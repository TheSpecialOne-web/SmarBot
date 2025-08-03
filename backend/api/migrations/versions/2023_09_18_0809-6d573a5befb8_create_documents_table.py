"""create documents table

Revision ID: 6d573a5befb8
Revises: a9ed9ecef8b2
Create Date: 2023-09-18 08:09:15.835137

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "6d573a5befb8"
down_revision = "a9ed9ecef8b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("basename", pg.VARCHAR(255), nullable=False),
        sa.Column("memo", pg.VARCHAR(511), nullable=False),
        sa.Column("can_search", pg.BOOLEAN, nullable=False, default=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("documents")
