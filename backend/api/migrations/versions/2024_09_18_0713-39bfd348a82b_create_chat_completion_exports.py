"""create chat completion exports

Revision ID: 39bfd348a82b
Revises: 58123df1b6c2
Create Date: 2024-09-12 02:13:47.528500

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "39bfd348a82b"
down_revision = "58123df1b6c2"
branch_labels = None
depends_on = None

chat_completion_export_status = pg.ENUM(
    "processing", "active", "deleted", "error", name="chat_completion_export_status"
)


def upgrade() -> None:
    op.create_table(
        "chat_completion_exports",
        sa.Column(
            "id", pg.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column("user_id", sa.INTEGER, sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            chat_completion_export_status,
            nullable=False,
            server_default="processing",
        ),
        sa.Column("start_date_time", sa.DateTime, nullable=False),
        sa.Column("end_date_time", sa.DateTime, nullable=False),
        sa.Column("target_bot_id", sa.INTEGER, sa.ForeignKey("bots.id"), nullable=True),
        sa.Column("target_api_key_id", pg.UUID(as_uuid=True), sa.ForeignKey("api_keys.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("chat_completion_exports")
    chat_completion_export_status.drop(op.get_bind())
