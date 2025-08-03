"""create unique index users

Revision ID: af650915a844
Revises: a54ef618b800
Create Date: 2024-10-15 06:16:56.743660

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "af650915a844"
down_revision = "a54ef618b800"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "users_email_unique_idx",
        "users",
        ["email"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "users_auth0_id_unique_idx",
        "users",
        ["auth0_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "users_email_unique_idx",
        "users",
    )
    op.drop_index(
        "users_auth0_id_unique_idx",
        "users",
    )
