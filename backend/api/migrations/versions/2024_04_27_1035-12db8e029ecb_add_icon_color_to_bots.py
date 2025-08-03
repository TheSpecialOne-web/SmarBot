"""add icon_color to bots

Revision ID: 12db8e029ecb
Revises: 2b18e76039d8
Create Date: 2024-04-27 10:35:43.662761

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "12db8e029ecb"
down_revision = "2b18e76039d8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("icon_color", sa.VARCHAR(255), nullable=True))


def downgrade() -> None:
    op.drop_column("bots", "icon_color")
