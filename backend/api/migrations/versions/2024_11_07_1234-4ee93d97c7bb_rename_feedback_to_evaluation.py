"""rename feedback to evaluation

Revision ID: 4ee93d97c7bb
Revises: d64f33140ab3
Create Date: 2024-11-07 12:34:56.134905

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4ee93d97c7bb"
down_revision = "d64f33140ab3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation_turns", "feedback", new_column_name="evaluation")


def downgrade() -> None:
    op.alter_column("conversation_turns", "evaluation", new_column_name="feedback")
