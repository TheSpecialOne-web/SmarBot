"""add model_familiy to bot_templates

Revision ID: ac3e3b18d728
Revises: a9ff0da1c1a5
Create Date: 2024-08-13 15:38:24.214366

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ac3e3b18d728"
down_revision = "a9ff0da1c1a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("bot_templates", sa.Column("response_generator_model_family", sa.String(length=255), nullable=True))
    op.add_column("bots", sa.Column("image_generator_model_family", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("bot_templates", "response_generator_model_family")
    op.drop_column("bots", "image_generator_model_family")
