"""create_conversations_table

Revision ID: 041ebe3f13e4
Revises: 7dd4a0a6d5a9
Create Date: 2024-02-09 04:04:54.551263

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "041ebe3f13e4"
down_revision = "7dd4a0a6d5a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("title", pg.VARCHAR(255), nullable=True),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )

    op.create_table(
        "conversation_turns",
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "conversation_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("user_input", pg.VARCHAR(1023)),
        sa.Column("bot_output", pg.VARCHAR(1023)),
        sa.Column("queries", pg.ARRAY(pg.VARCHAR(255))),
        sa.Column("query_input_token", pg.INTEGER),
        sa.Column("query_output_token", pg.INTEGER),
        sa.Column("response_input_token", pg.INTEGER),
        sa.Column("response_output_token", pg.INTEGER),
        sa.Column("query_generator_model", pg.VARCHAR(255), nullable=True, server_default="gpt-3.5-turbo"),
        sa.Column("response_generator_model", pg.VARCHAR(255), nullable=True, server_default="gpt-3.5-turbo"),
        sa.Column(
            "feedback",
            pg.VARCHAR(255),
            nullable=True,
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("conversation_turns")
    op.drop_table("conversations")
