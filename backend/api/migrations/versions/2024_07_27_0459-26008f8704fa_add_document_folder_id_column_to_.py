"""add_document_folder_id_column_to_conversation_turns

Revision ID: 26008f8704fa
Revises: a389c94aa682
Create Date: 2024-07-27 04:59:14.864866

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "26008f8704fa"
down_revision = "a389c94aa682"
branch_labels = None
depends_on = None

CONVERSATION_TURNS = "conversation_turns"
DOCUMENT_FOLDER_ID = "document_folder_id"


def upgrade() -> None:
    op.add_column(
        CONVERSATION_TURNS,
        sa.Column(
            DOCUMENT_FOLDER_ID,
            pg.UUID(as_uuid=True),
            sa.ForeignKey("document_folders.id", onupdate="CASCADE"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(CONVERSATION_TURNS, DOCUMENT_FOLDER_ID)
