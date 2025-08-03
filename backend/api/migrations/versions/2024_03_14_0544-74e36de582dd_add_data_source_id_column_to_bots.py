"""add_data_source_id_column_to_bots

Revision ID: 74e36de582dd
Revises: 87c94ae7d065
Create Date: 2024-03-14 05:44:39.461791

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "74e36de582dd"
down_revision = "87c94ae7d065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bots",
        sa.Column(
            "data_source_id",
            pg.UUID(as_uuid=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("bots", "data_source_id")
