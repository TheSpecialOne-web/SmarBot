"""add timestamp columns

Revision ID: d70feddb9367
Revises: 7ff5c4d46a4d
Create Date: 2023-08-19 08:53:52.432991

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d70feddb9367"
down_revision = "7ff5c4d46a4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # botsテーブルにカラムを追加
    op.add_column("bots", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "bots",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("bots", sa.Column("deleted_at", sa.DateTime, nullable=True))

    # policiesテーブルにカラムを追加
    op.add_column("policies", sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False))
    op.add_column(
        "policies",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.add_column("policies", sa.Column("deleted_at", sa.DateTime, nullable=True))


def downgrade() -> None:
    # botsテーブルからカラムを削除
    op.drop_column("bots", "created_at")
    op.drop_column("bots", "updated_at")
    op.drop_column("bots", "deleted_at")

    # policiesテーブルからカラムを削除
    op.drop_column("policies", "created_at")
    op.drop_column("policies", "updated_at")
    op.drop_column("policies", "deleted_at")
