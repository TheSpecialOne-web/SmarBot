"""add logo_url  column to  tenants table

Revision ID: ac24952ff440
Revises: b93b9758813d
Create Date: 2024-04-06 12:36:54.492729

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ac24952ff440"
down_revision = "b93b9758813d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("logo_url", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "logo_url")
