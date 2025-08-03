"""change fk of unnecessary ondelete cascade

Revision ID: e170a43a7f1e
Revises: af15f90187f7
Create Date: 2024-11-22 01:36:05.520633

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "e170a43a7f1e"
down_revision = "af15f90187f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("metering_tenant_id_fkey", "metering", type_="foreignkey")
    op.create_foreign_key(
        "metering_tenant_id_fkey",
        "metering",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="CASCADE",
    )
    op.drop_constraint("metering_bot_id_fkey", "metering", type_="foreignkey")
    op.create_foreign_key(
        "metering_bot_id_fkey",
        "metering",
        "bots",
        ["bot_id"],
        ["id"],
        ondelete="RESTRICT",
        onupdate="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("metering_bot_id_fkey", "metering", type_="foreignkey")
    op.create_foreign_key(
        "metering_bot_id_fkey",
        "metering",
        "bots",
        ["bot_id"],
        ["id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
    op.drop_constraint("metering_tenant_id_fkey", "metering", type_="foreignkey")
    op.create_foreign_key(
        "metering_tenant_id_fkey",
        "metering",
        "tenants",
        ["tenant_id"],
        ["id"],
        ondelete="CASCADE",
        onupdate="CASCADE",
    )
