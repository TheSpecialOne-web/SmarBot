"""create_group_tables

Revision ID: a8ee3d4b21d2
Revises: 533ace29e681
Create Date: 2023-11-09 05:45:15.198254

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "a8ee3d4b21d2"
down_revision = "533ace29e681"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            pg.TIMESTAMP,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )

    # Create users_groups table
    op.create_table(
        "users_groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "group_id", sa.Integer, sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            pg.TIMESTAMP,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )

    # Create groups_policies table
    op.create_table(
        "groups_policies",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "group_id", sa.Integer, sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "bot_id", sa.Integer, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("action", pg.ENUM("read", "write", name="group_policy_action"), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            pg.TIMESTAMP,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    # Drop groups_policies table
    op.drop_table("groups_policies")

    # Drop users_groups table
    op.drop_table("users_groups")

    # Drop groups table
    op.drop_table("groups")
