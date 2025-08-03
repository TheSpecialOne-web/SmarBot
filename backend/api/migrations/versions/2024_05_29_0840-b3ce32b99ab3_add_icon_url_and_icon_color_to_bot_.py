"""add icon url and icon color to bot_templates table

Revision ID: b3ce32b99ab3
Revises: 14f33ca1e727
Create Date: 2024-05-29 08:40:16.940891

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b3ce32b99ab3"
down_revision = "14f33ca1e727"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_templates", sa.Column("icon_url", sa.String(255), nullable=True))
    op.add_column("bot_templates", sa.Column("icon_color", sa.String(255), nullable=False, server_default="#BDBDBD"))
    op.add_column("bot_templates", sa.Column("document_limit", sa.Integer, nullable=False, server_default="5"))


def downgrade() -> None:
    op.drop_column("bot_templates", "icon_url")
    op.drop_column("bot_templates", "icon_color")
    op.drop_column("bot_templates", "document_limit")
