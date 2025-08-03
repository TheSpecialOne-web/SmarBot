"""add enable_document_intelligence column to tenants table

Revision ID: 3347bfefb019
Revises: 667bc8814bec
Create Date: 2024-03-30 07:46:24.991505

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3347bfefb019"
down_revision = "667bc8814bec"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants", sa.Column("enable_document_intelligence", sa.Boolean(), nullable=True, server_default="false")
    )


def downgrade() -> None:
    op.drop_column("tenants", "enable_document_intelligence")
