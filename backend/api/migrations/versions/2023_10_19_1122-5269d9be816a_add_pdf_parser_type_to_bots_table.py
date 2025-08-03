"""add_pdf_parser_to_bots_table

Revision ID: 5269d9be816a
Revises: b09220947e6c
Create Date: 2023-10-19 11:22:29.088791

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "5269d9be816a"
down_revision = "b09220947e6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("pdf_parser", pg.VARCHAR(511), nullable=True, server_default="pypdf"))


def downgrade() -> None:
    op.drop_column("bots", "pdf_parser")
