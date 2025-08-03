"""create terms-v2 table

Revision ID: da6594316be0
Revises: c66fc2456cd8
Create Date: 2024-06-12 05:51:19.644002

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "da6594316be0"
down_revision = "c66fc2456cd8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "terms_v2",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "bot_id", sa.Integer, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("names", pg.ARRAY(sa.String(255)), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("terms_v2")
