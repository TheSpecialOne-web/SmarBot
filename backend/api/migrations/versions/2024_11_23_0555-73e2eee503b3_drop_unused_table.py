"""drop unused table

Revision ID: 73e2eee503b3
Revises: e170a43a7f1e
Create Date: 2024-11-23 05:55:46.897535

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "73e2eee503b3"
down_revision = "e170a43a7f1e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("users_tenants")
    op.drop_table("terms")
    op.drop_table("groups_policies")
    op.drop_table("chat_logs")
    tenant_role = pg.ENUM("user", "admin", name="tenant_role")
    tenant_role.drop(op.get_bind(), checkfirst=True)
    group_policy_action = pg.ENUM("read", "write", name="group_policy_action", create_type=False)
    group_policy_action.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    op.create_table(
        "chat_logs",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column("chat_id", pg.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "bot_id", pg.INTEGER, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("timestamp", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("model_name", pg.VARCHAR(511)),
        sa.Column("user_input", pg.VARCHAR(1023)),
        sa.Column("bot_output", pg.VARCHAR(1023)),
        sa.Column("queries", pg.ARRAY(pg.VARCHAR(511))),
        sa.Column("query_input_token", pg.INTEGER),
        sa.Column("query_output_token", pg.INTEGER),
        sa.Column("response_input_token", pg.INTEGER),
        sa.Column("response_output_token", pg.INTEGER),
        sa.Column("query_generator_model", pg.VARCHAR(511), nullable=True),
        sa.Column("output_generator_model", pg.VARCHAR(511), nullable=True),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )
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
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )
    op.create_table(
        "terms",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "bot_id", sa.Integer, sa.ForeignKey("bots.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )
    op.create_table(
        "users_tenants",
        sa.Column("id", pg.INTEGER, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id", pg.INTEGER, sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "tenant_id",
            pg.INTEGER,
            sa.ForeignKey("tenants.id", onupdate="CASCADE", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("roles", pg.ARRAY(pg.ENUM("user", "admin", name="tenant_role")), nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )
