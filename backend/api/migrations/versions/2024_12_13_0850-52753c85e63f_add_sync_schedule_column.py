"""add_sync_schedule_column

Revision ID: 52753c85e63f
Revises: ff33461ac9df
Create Date: 2024-12-13 08:50:43.821794

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "52753c85e63f"
down_revision = "ff33461ac9df"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "document_folders",
        sa.Column("sync_schedule", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("document_folders", "sync_schedule")
