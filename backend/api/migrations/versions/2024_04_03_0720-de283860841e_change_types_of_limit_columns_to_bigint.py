"""change types of limit columns to bigint

Revision ID: de283860841e
Revises: f35609c3d451
Create Date: 2024-04-03 07:20:31.941919

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "de283860841e"
down_revision = "f35609c3d451"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tenants", "free_token_limit", type_=sa.BigInteger(), nullable=True)
    op.alter_column("tenants", "additional_token_limit", type_=sa.BigInteger(), nullable=True)
    op.alter_column("tenants", "free_storage_limit", type_=sa.BigInteger(), nullable=True)
    op.alter_column("tenants", "additional_storage_limit", type_=sa.BigInteger(), nullable=True)


def downgrade() -> None:
    op.alter_column("tenants", "additional_storage_limit", type_=sa.Integer(), nullable=True)
    op.alter_column("tenants", "free_storage_limit", type_=sa.Integer(), nullable=True)
    op.alter_column("tenants", "additional_token_limit", type_=sa.Integer(), nullable=True)
    op.alter_column("tenants", "free_token_limit", type_=sa.Integer(), nullable=True)
