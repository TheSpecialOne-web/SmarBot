"""create unique index to tenants alias

Revision ID: 0a6a7fe5b297
Revises: 0cae8b22acc7
Create Date: 2024-09-17 09:29:56.571677

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0a6a7fe5b297"
down_revision = "0cae8b22acc7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "tenant_alias_unique_idx",
        "tenants",
        ["alias"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "tenant_index_name_unique_idx",
        "tenants",
        ["index_name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "tenant_container_name_unique_idx",
        "tenants",
        ["container_name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "tenant_alias_unique_idx",
        "tenants",
    )
    op.drop_index(
        "tenant_index_name_unique_idx",
        "tenants",
    )
    op.drop_index(
        "tenant_container_name_unique_idx",
        "tenants",
    )
