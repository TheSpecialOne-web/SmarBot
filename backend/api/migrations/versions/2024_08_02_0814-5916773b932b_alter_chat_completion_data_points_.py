"""alter_chat_completion_data_points_content_type

Revision ID: 5916773b932b
Revises: 00eafde39dbe
Create Date: 2024-08-02 08:14:59.416426

"""

from alembic import op
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "5916773b932b"
down_revision = "00eafde39dbe"
branch_labels = None
depends_on = None

CHAT_COMPLETION_DATA_POINTS = "chat_completion_data_points"
CONTENT = "content"


def upgrade() -> None:
    op.alter_column(CHAT_COMPLETION_DATA_POINTS, CONTENT, type_=pg.TEXT)


def downgrade() -> None:
    op.alter_column(CHAT_COMPLETION_DATA_POINTS, CONTENT, type_=pg.VARCHAR(1023))
