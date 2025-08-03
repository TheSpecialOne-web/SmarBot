"""create chat_logs table

Revision ID: b031d83338f7
Revises: c7e7c68b3f91
Create Date: 2023-09-09 13:46:30.683311

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "b031d83338f7"
down_revision = "c7e7c68b3f91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_logs",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("chat_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("timestamp", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("model_name", pg.VARCHAR(511)),
        sa.Column("user_input", pg.VARCHAR(511)),
        sa.Column("bot_output", pg.VARCHAR(511)),
        sa.Column("queries", pg.ARRAY(pg.VARCHAR(511))),
        sa.Column("query_input_token", pg.INTEGER),
        sa.Column("query_output_token", pg.INTEGER),
        sa.Column("response_input_token", pg.INTEGER),
        sa.Column("response_output_token", pg.INTEGER),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("chat_logs")
