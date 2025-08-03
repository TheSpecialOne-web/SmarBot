"""add conversation_turn_id column to attachments

Revision ID: 1cc22b844695
Revises: 87c94ae7d065
Create Date: 2024-03-09 09:06:08.845625

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "1cc22b844695"
down_revision = "daf99eda31b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attachments", sa.Column("conversation_turn_id", pg.UUID))
    op.create_foreign_key(
        "fk_attachments_conversation_turn_id", "attachments", "conversation_turns", ["conversation_turn_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("fk_attachments_conversation_turn_id", "attachments", type_="foreignkey")
    op.drop_column("attachments", "conversation_turn_id")
