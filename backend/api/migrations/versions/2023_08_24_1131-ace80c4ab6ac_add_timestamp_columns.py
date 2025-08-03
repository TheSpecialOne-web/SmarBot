"""add timestamp columns

Revision ID: ace80c4ab6ac
Revises: 4b8216f16a35
Create Date: 2023-08-24 11:31:00.746436

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ace80c4ab6ac"
down_revision = "4b8216f16a35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "tenants",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("tenants", sa.Column("deleted_at", sa.DateTime, nullable=True))

    op.add_column("users", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "users",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("users", sa.Column("deleted_at", sa.DateTime, nullable=True))

    op.add_column("users_tenants", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "users_tenants",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("users_tenants", sa.Column("deleted_at", sa.DateTime, nullable=True))

    op.add_column("users_policies", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "users_policies",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("users_policies", sa.Column("deleted_at", sa.DateTime, nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "created_at")
    op.drop_column("tenants", "updated_at")
    op.drop_column("tenants", "deleted_at")

    op.drop_column("users", "created_at")
    op.drop_column("users", "updated_at")
    op.drop_column("users", "deleted_at")

    op.drop_column("users_tenants", "created_at")
    op.drop_column("users_tenants", "updated_at")
    op.drop_column("users_tenants", "deleted_at")

    op.drop_column("users_policies", "created_at")
    op.drop_column("users_policies", "updated_at")
    op.drop_column("users_policies", "deleted_at")
