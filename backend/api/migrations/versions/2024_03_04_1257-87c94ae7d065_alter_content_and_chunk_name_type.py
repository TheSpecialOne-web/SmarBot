"""alter content and chunk_name type

Revision ID: 87c94ae7d065
Revises: 05913e02d2fc
Create Date: 2024-03-04 12:57:25.886197

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "87c94ae7d065"
down_revision = "05913e02d2fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("conversation_data_points", "content", type_=pg.TEXT)
    op.alter_column("conversation_data_points", "chunk_name", type_=pg.VARCHAR(1023))


def downgrade() -> None:
    op.alter_column("conversation_data_points", "content", type_=pg.VARCHAR(1023))
    op.alter_column("conversation_data_points", "chunk_name", type_=pg.TEXT)
