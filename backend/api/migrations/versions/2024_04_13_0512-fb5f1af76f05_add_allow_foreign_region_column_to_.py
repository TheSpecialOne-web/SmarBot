"""add allow_foreign_region column to tenants table

Revision ID: fb5f1af76f05
Revises: 85ee71cd37a9
Create Date: 2024-04-13 05:12:17.699780

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "fb5f1af76f05"

down_revision = "85ee71cd37a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("allow_foreign_region", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("tenants", "allow_foreign_region")
