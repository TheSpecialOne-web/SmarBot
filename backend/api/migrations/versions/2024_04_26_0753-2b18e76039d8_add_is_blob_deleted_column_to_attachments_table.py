"""add is_blob_deleted column to attachments table

Revision ID: 2b18e76039d8
Revises: 71806766c814
Create Date: 2024-04-26 07:53:04.143247

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "2b18e76039d8"
down_revision = "71806766c814"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("attachments", sa.Column("is_blob_deleted", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("attachments", "is_blob_deleted")
