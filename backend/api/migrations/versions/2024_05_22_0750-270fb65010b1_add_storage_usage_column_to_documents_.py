"""add storage_usage column to documents table

Revision ID: 270fb65010b1
Revises: cd1cf8c240c6
Create Date: 2024-05-22 07:50:03.072572

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "270fb65010b1"
down_revision = "cd1cf8c240c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("storage_usage", pg.BIGINT, nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "storage_usage")
