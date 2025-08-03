"""add evaluation column as text

Revision ID: d198cb395bf6
Revises: df3c62488dec
Create Date: 2024-10-14 05:15:02.658092

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d198cb395bf6"
down_revision = "df3c62488dec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the evaluation column
    op.add_column("chat_completions", sa.Column("evaluation", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove the evaluation column
    op.drop_column("chat_completions", "evaluation")
