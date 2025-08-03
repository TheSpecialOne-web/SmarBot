"""create notifications table

Revision ID: b25140d27f13
Revises: 7471db7c678b
Create Date: 2024-05-16 04:25:20.195856

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b25140d27f13"
down_revision = "7471db7c678b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("sender_id", pg.INTEGER, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("recipient_type", sa.String(255), nullable=False),
        sa.Column("start_date", sa.DateTime, nullable=False),
        sa.Column("end_date", sa.DateTime, nullable=False),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime),
    )


def downgrade() -> None:
    op.drop_table("notifications")
