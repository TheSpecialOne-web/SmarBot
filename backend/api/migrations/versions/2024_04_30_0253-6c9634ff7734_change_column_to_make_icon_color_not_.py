"""change column to make icon_color not nullable

Revision ID: 6c9634ff7734
Revises: 12db8e029ecb
Create Date: 2024-04-30 02:53:04.760670

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "6c9634ff7734"
down_revision = "12db8e029ecb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("bots", "icon_color")
    op.add_column("bots", sa.Column("icon_color", sa.VARCHAR(255), nullable=False, server_default="#BDBDBD"))


def downgrade() -> None:
    op.drop_column("bots", "icon_color")
    op.add_column("bots", sa.Column("icon_color", sa.VARCHAR(255), nullable=True))
