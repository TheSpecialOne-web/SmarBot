"""add role to users_groups and add is_is_general to groups

Revision ID: 8f955c0c73f9
Revises: 39bfd348a82b
Create Date: 2024-09-18 12:09:34.612674

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "8f955c0c73f9"
down_revision = "39bfd348a82b"
branch_labels = None
depends_on = None


USERS_GROUPS_TABLE_NAME = "users_groups"
GROUPS_TABLE_NAME = "groups"
BOTS_TABLE_NAME = "bots"
TENANT_ID_COLUMN = "tenant_id"
IS_GENERAL_COLUMN = "is_general"
INDEX_NAME = "idx_groups_is_general_true"


def upgrade() -> None:
    op.add_column(USERS_GROUPS_TABLE_NAME, sa.Column("role", sa.String(), nullable=True))
    op.add_column(BOTS_TABLE_NAME, sa.Column("group_id", sa.Integer(), sa.ForeignKey("groups.id"), nullable=True))
    op.add_column(GROUPS_TABLE_NAME, sa.Column("is_general", sa.Boolean(), nullable=False, server_default="false"))

    op.create_index(
        INDEX_NAME,
        GROUPS_TABLE_NAME,
        [TENANT_ID_COLUMN],
        unique=True,
        postgresql_where="is_general = true AND deleted_at IS NULL",
    )


def downgrade() -> None:
    op.drop_column(USERS_GROUPS_TABLE_NAME, "role")
    op.drop_column(BOTS_TABLE_NAME, "group_id")
    op.drop_index(INDEX_NAME, table_name=GROUPS_TABLE_NAME)
    op.drop_column(GROUPS_TABLE_NAME, "is_general")
