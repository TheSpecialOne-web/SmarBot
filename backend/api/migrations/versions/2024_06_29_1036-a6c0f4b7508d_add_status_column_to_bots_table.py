"""add status column to bots table

Revision ID: a6c0f4b7508d
Revises: fa823dac3d9d
Create Date: 2024-06-29 10:36:06.012685

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a6c0f4b7508d"
down_revision = "fa823dac3d9d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bots", sa.Column("status", sa.VARCHAR(255), nullable=False, server_default="active"))


def downgrade() -> None:
    op.drop_column("bots", "status")
