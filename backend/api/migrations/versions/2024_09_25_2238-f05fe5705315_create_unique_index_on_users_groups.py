"""create unique index on users_groups

Revision ID: f05fe5705315
Revises: 8f955c0c73f9
Create Date: 2024-09-25 22:38:32.460894

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f05fe5705315"
down_revision = "8f955c0c73f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "users_groups_user_id_group_id_idx",
        "users_groups",
        ["user_id", "group_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("users_groups_user_id_group_id_idx", table_name="users_groups")
