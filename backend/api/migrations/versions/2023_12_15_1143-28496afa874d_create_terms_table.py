"""create terms table

Revision ID: 28496afa874d
Revises: 3153d4675b1a
Create Date: 2023-12-15 11:43:16.930450

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "28496afa874d"
down_revision = "3153d4675b1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "terms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "bot_id", sa.Integer, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("terms")
