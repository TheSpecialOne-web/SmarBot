"""Rename user_id to creator_id in chat_completion_exports

Revision ID: 09f18af7be23
Revises: 558276eed1eb
Create Date: 2024-10-11 03:01:46.159902

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "09f18af7be23"
down_revision = "558276eed1eb"
branch_labels = None
depends_on = None


def upgrade():
    # Rename the user_id column to creator_id
    op.alter_column("chat_completion_exports", "user_id", new_column_name="creator_id")


def downgrade():
    # Rename the creator_id column back to user_id
    op.alter_column("chat_completion_exports", "creator_id", new_column_name="user_id")
