"""add clumnt to  metering table

Revision ID: b93b9758813d
Revises: d12b33da834a
Create Date: 2024-04-04 10:13:35.892593

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b93b9758813d"
down_revision = "d12b33da834a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("metering", sa.Column("bot_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("metering", "bot_id")
