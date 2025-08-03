"""alter_alias_not_unique

Revision ID: 72c6bcead839
Revises: 12496604d55d
Create Date: 2024-02-15 06:50:16.171592

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "72c6bcead839"
down_revision = "12496604d55d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("tenants", "alias", unique=False)


def downgrade() -> None:
    op.alter_column("tenants", "alias", unique=True)
