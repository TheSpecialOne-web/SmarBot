"""create unique index terms_v2

Revision ID: a54ef618b800
Revises: d198cb395bf6
Create Date: 2024-10-15 06:16:25.692603

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a54ef618b800"
down_revision = "d198cb395bf6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "terms_v2_bot_id_description_idx",
        "terms_v2",
        ["bot_id", "description"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "terms_v2_bot_id_description_idx",
        "terms_v2",
    )
