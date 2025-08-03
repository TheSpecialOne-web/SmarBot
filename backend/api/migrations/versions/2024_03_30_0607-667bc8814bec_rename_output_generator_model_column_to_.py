"""rename output_generator_model column to response_generator_model

Revision ID: 667bc8814bec
Revises: 2c0e1a31c8ad
Create Date: 2024-03-30 06:07:06.505280

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "667bc8814bec"
down_revision = "2c0e1a31c8ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        table_name="bots",
        column_name="output_generator_model",
        new_column_name="response_generator_model",
    )


def downgrade() -> None:
    op.alter_column(
        table_name="bots",
        column_name="response_generator_model",
        new_column_name="output_generator_model",
    )
