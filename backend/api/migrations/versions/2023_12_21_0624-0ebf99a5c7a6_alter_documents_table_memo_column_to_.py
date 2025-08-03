"""alter_documents_table_memo_column_to_nullable

Revision ID: 0ebf99a5c7a6
Revises: 28496afa874d
Create Date: 2023-12-21 06:24:24.838726

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0ebf99a5c7a6"
down_revision = "28496afa874d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("documents", "memo", nullable=True)


def downgrade() -> None:
    op.alter_column("documents", "memo", nullable=False)
