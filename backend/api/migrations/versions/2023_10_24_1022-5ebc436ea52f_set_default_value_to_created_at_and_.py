"""set default value to created_at and updated_at

Revision ID: 5ebc436ea52f
Revises: 5269d9be816a
Create Date: 2023-10-24 10:22:03.943564

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5ebc436ea52f"
down_revision = "5269d9be816a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("administrators", "created_at", server_default=sa.func.now())
    op.alter_column("administrators", "updated_at", server_default=sa.func.now(), onupdate=sa.func.now())


def downgrade() -> None:
    pass
