"""add comment to conversation_turns and chat_completions

Revision ID: 9bb370eb4e8d
Revises: 178f9a5b4aca
Create Date: 2024-10-08 12:19:45.514945

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9bb370eb4e8d"
down_revision = "178f9a5b4aca"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_turns",
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.add_column(
        "chat_completions",
        sa.Column("comment", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("conversation_turns", "comment")
    op.drop_column("chat_completions", "comment")
