"""add_endpoint_column_to_bots_table

Revision ID: accc24601a3c
Revises: 19e0c54f8252
Create Date: 2024-06-04 03:26:16.911115

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "accc24601a3c"
down_revision = "19e0c54f8252"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 'pgcrypto' 拡張機能をインストール
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.add_column(
        "bots",
        sa.Column("endpoint_id", pg.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
    )


def downgrade() -> None:
    op.drop_column("bots", "endpoint_id")
