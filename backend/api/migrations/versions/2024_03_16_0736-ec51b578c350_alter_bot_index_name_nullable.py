"""alter_bot_index_name_nullable

Revision ID: ec51b578c350
Revises: 48b9cb2d422c
Create Date: 2024-03-16 07:36:21.742065

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "ec51b578c350"
down_revision = "48b9cb2d422c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("bots", "index_name", nullable=True)


def downgrade() -> None:
    op.alter_column("bots", "index_name", nullable=False)
