"""add columns of limit to tenants table

Revision ID: fa739468b21e
Revises: 227735869c27
Create Date: 2024-04-02 06:40:21.116100

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "fa739468b21e"
down_revision = "227735869c27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("free_token_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("additional_token_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("free_storage_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("additional_storage_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("free_user_seat_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("additional_user_seat_limit", sa.Integer(), nullable=True))
    op.add_column("tenants", sa.Column("document_intelligence_page_limit", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "document_intelligence_page_limit")
    op.drop_column("tenants", "additional_user_seat_limit")
    op.drop_column("tenants", "free_user_seat_limit")
    op.drop_column("tenants", "additional_storage_limit")
    op.drop_column("tenants", "free_storage_limit")
    op.drop_column("tenants", "additional_token_limit")
    op.drop_column("tenants", "free_token_limit")
