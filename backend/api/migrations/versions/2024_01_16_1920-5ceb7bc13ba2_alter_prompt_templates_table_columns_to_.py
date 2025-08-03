"""alter_prompt_templates_table_columns_to_description_and_prompt

Revision ID: 5ceb7bc13ba2
Revises: f01545c22b3d
Create Date: 2024-01-16 19:20:58.860406

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "5ceb7bc13ba2"
down_revision = "f01545c22b3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("prompt_templates", "content", new_column_name="prompt")
    op.add_column(
        "prompt_templates",
        sa.Column("description", sa.String(255), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("prompt_templates", "description")
    op.alter_column("prompt_templates", "prompt", new_column_name="content")
