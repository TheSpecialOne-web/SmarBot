"""add file extension to documents table

Revision ID: 3153d4675b1a
Revises: a8ee3d4b21d2
Create Date: 2023-11-09 12:12:03.303686

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "3153d4675b1a"
down_revision = "a8ee3d4b21d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("file_extension", pg.VARCHAR(511), nullable=False, server_default="pdf"))


def downgrade() -> None:
    op.drop_column("documents", "file_extension")
