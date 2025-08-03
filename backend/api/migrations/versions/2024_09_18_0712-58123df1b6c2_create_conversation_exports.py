"""create conversation exports

Revision ID: 58123df1b6c2
Revises: 6d922f7b2112
Create Date: 2024-09-12 02:12:16.376785

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "58123df1b6c2"
down_revision = "6d922f7b2112"
branch_labels = None
depends_on = None


conversation_export_status = pg.ENUM("processing", "active", "deleted", "error", name="conversation_export_status")


def upgrade() -> None:
    op.create_table(
        "conversation_exports",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.INTEGER, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("start_date_time", sa.DateTime, nullable=False),
        sa.Column("end_date_time", sa.DateTime, nullable=False),
        sa.Column("target_bot_id", sa.INTEGER, sa.ForeignKey("bots.id"), nullable=True),
        sa.Column("target_user_id", sa.INTEGER, sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "status",
            conversation_export_status,
            nullable=False,
            server_default="processing",
        ),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("conversation_exports")
    conversation_export_status.drop(op.get_bind())
