"""create users_liked_bots table

Revision ID: b375b39c9de1
Revises: f42242f75a65
Create Date: 2024-10-17 02:37:38.546462

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b375b39c9de1"
down_revision = "f42242f75a65"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users_liked_bots",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "bot_id", sa.Integer, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("user_id", "bot_id", name="uq_user_bot"),
    )


def downgrade() -> None:
    op.drop_table("users_liked_bots")
