"""add enable_llm_document_reader column to tenant table

Revision ID: c47c6c911430
Revises: 3ff44afac685
Create Date: 2024-05-04 10:43:46.984789

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c47c6c911430"
down_revision = "3ff44afac685"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tenants", sa.Column("enable_llm_document_reader", sa.Boolean(), nullable=False, server_default="false")
    )


def downgrade() -> None:
    op.drop_column("tenants", "enable_llm_document_reader")
