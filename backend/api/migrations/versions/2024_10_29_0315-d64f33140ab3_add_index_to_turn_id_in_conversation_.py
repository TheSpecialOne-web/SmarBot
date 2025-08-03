"""Add index to turn_id in conversation_data_points

Revision ID: d64f33140ab3
Revises: 09f18af7be23
Create Date: 2024-10-29 03:15:09.681255

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d64f33140ab3"
down_revision = "09f18af7be23"
branch_labels = None
depends_on = None


def upgrade():
    # Create the index on turn_id
    op.create_index(
        "idx_turn_id",
        "conversation_data_points",
        ["turn_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade():
    # Remove the index if downgrading
    op.drop_index("idx_turn_id", "conversation_data_points")
