"""create question_answers table

Revision ID: e951fbe3c462
Revises: c47c6c911430
Create Date: 2024-05-09 07:10:50.002768

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "e951fbe3c462"
down_revision = "c47c6c911430"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "question_answers",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id"), nullable=False),
        sa.Column("question", sa.VARCHAR(255), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("question_answers")
