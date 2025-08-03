"""create_conversations_bot_id_user_id_idx

Revision ID: b96561506589
Revises: ac3e3b18d728
Create Date: 2024-08-15 06:51:26.929665

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b96561506589"
down_revision = "ac3e3b18d728"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("conversations_bot_id_user_id_idx", "conversations", ["bot_id", "user_id"])


def downgrade() -> None:
    op.drop_index("conversations_bot_id_user_id_idx", "conversations")
    pass
