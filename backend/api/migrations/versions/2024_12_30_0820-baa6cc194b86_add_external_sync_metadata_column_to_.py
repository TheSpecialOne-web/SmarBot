"""add_external_sync_metadata_column_to_document_folders

Revision ID: baa6cc194b86
Revises: 5abd4fb7d868
Create Date: 2024-12-30 08:20:33.422541

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "baa6cc194b86"
down_revision = "5abd4fb7d868"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("document_folders", sa.Column("external_sync_metadata", pg.JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("document_folders", "external_sync_metadata")
