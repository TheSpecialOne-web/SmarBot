"""create workflow log tables

Revision ID: 0886b7029823
Revises: 3029e8fb650d
Create Date: 2025-01-09 09:09:26.521839

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "0886b7029823"
down_revision = "3029e8fb650d"  # 適切なダウンリビジョンIDに更新してください
branch_labels = None
depends_on = None

flow_step_status_enum = pg.ENUM("processing", "completed", "failed", name="flow_step_status_enum")


def upgrade() -> None:
    # workflow_threads テーブル作成
    op.create_table(
        "workflow_threads",
        sa.Column("id", pg.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_id", pg.UUID, sa.ForeignKey("workflows.id"), nullable=False),
        sa.Column("user_id", pg.INTEGER, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )

    # workflow_flows テーブル作成
    op.create_table(
        "workflow_thread_flows",
        sa.Column("id", pg.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_thread_id", pg.UUID, sa.ForeignKey("workflow_threads.id"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )

    # workflow_thread_flow_steps テーブル作成
    op.create_table(
        "workflow_thread_flow_steps",
        sa.Column("id", pg.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_thread_flow_id", pg.UUID, sa.ForeignKey("workflow_thread_flows.id"), nullable=False),
        sa.Column("step", sa.Integer, nullable=False),
        sa.Column("input", pg.JSONB),
        sa.Column("output", pg.JSONB),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("status", flow_step_status_enum, nullable=False, server_default="completed"),
        sa.Column("token_count", sa.Float, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
    )

    # # インデックス作成
    op.create_index("idx_workflow_id", "workflow_threads", ["workflow_id"])
    op.create_index("idx_workflow_thread_id", "workflow_thread_flows", ["workflow_thread_id"])
    op.create_index("idx_workflow_thread_flow_id", "workflow_thread_flow_steps", ["workflow_thread_flow_id"])


def downgrade() -> None:
    # enum削除
    # # インデックス削除
    op.drop_index("idx_workflow_thread_flow_id", table_name="workflow_thread_flow_steps")
    op.drop_index("idx_workflow_thread_id", table_name="workflow_thread_flows")
    op.drop_index("idx_workflow_id", table_name="workflow_threads")
    # テーブル削除
    op.drop_table("workflow_thread_flow_steps")
    op.drop_table("workflow_thread_flows")
    op.drop_table("workflow_threads")

    op.execute("DROP TYPE IF EXISTS flow_step_status_enum")
