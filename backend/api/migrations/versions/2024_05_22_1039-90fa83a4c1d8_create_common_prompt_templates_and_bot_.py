"""create common_prompt_templates and  bot_templates tables

Revision ID: 90fa83a4c1d8
Revises: 270fb65010b1
Create Date: 2024-05-22 10:39:40.289027

"""

# revision identifiers, used by Alembic.
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "90fa83a4c1d8"
down_revision = "270fb65010b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bot_templates",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("approach", sa.String(255), nullable=False),
        sa.Column("response_generator_model", sa.String(511), nullable=False),
        sa.Column("pdf_parser", sa.String(511), nullable=False),
        sa.Column("enable_web_browsing", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("enable_follow_up_questions", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("response_system_prompt", sa.Text, nullable=False),
        sa.Column("is_public", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )
    op.create_table(
        "common_prompt_templates",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("bot_template_id", pg.UUID(as_uuid=True), sa.ForeignKey("bot_templates.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("created_at", pg.TIMESTAMP, server_default=sa.func.now()),
        sa.Column("updated_at", pg.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("deleted_at", pg.TIMESTAMP),
    )


def downgrade() -> None:
    op.drop_table("common_prompt_templates")
    op.drop_table("bot_templates")
