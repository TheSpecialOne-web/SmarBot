"""create_chat_completions_table

Revision ID: 072e8b35d5e0
Revises: 0b275ec1d9b8
Create Date: 2024-06-15 12:33:07.041995

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "072e8b35d5e0"
down_revision = "0b275ec1d9b8"
branch_labels = None
depends_on = None

CHAT_COMPLETIONS = "chat_completions"
CHAT_COMPLETION_DATA_POINTS = "chat_completion_data_points"


def upgrade() -> None:
    op.create_table(
        CHAT_COMPLETIONS,
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("messages", pg.JSON, nullable=False),
        sa.Column("answer", pg.TEXT, nullable=False),
        sa.Column("token_count", pg.FLOAT, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )

    op.create_table(
        CHAT_COMPLETION_DATA_POINTS,
        sa.Column(
            "id",
            pg.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "chat_completion_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("chat_completions.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cite_number", pg.INTEGER, nullable=False),
        sa.Column("chunk_name", pg.TEXT, nullable=False),
        sa.Column("content", pg.VARCHAR(1023), nullable=False),
        sa.Column("blob_path", pg.VARCHAR(1023), nullable=False),
        sa.Column("page_number", pg.INTEGER, nullable=False),
        sa.Column("additional_info", pg.JSON, nullable=True),
        sa.Column("url", sa.Text, nullable=True),
        sa.Column("type", sa.String(255), nullable=False),
        sa.Column(
            "document_id",
            sa.Integer,
            sa.ForeignKey("documents.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "question_answer_id",
            pg.UUID,
            sa.ForeignKey("question_answers.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table(CHAT_COMPLETION_DATA_POINTS)
    op.drop_table(CHAT_COMPLETIONS)
