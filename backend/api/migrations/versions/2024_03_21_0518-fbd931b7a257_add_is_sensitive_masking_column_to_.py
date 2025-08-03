"""add is_sensitive_masked column to tenant table

Revision ID: fbd931b7a257
Revises: 1cc22b844695
Create Date: 2024-03-21 05:18:57.869927

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "fbd931b7a257"
down_revision = "1cc22b844695"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("is_sensitive_masked", sa.Boolean(), nullable=True, server_default="false"))


def downgrade() -> None:
    op.drop_column("tenants", "is_sensitive_masked")
