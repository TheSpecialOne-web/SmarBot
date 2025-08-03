"""alter workflow tables

Revision ID: 3029e8fb650d
Revises: baa6cc194b86
Create Date: 2025-01-08 06:38:24.108793

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3029e8fb650d"
down_revision = "baa6cc194b86"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workflows", sa.Column("type", sa.String(255), nullable=False))
    op.alter_column(
        "workflows",
        "config",
        nullable=False,
        server_default="{}",
    )


def downgrade() -> None:
    op.drop_column("workflows", "type")
    op.alter_column("workflows", "config", nullable=True)
