"""add check constraint for basic AI

Revision ID: 164812fcb476
Revises: 8018ab8f2721
Create Date: 2024-08-29 12:22:00.003676

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "164812fcb476"
down_revision = "8018ab8f2721"
branch_labels = None
depends_on = None


# check if there are no chat_gpt_default bots with the same response generator model family
def upgrade() -> None:
    # partial unique index
    op.create_index(
        "idx_basic_ai_unique_model_family",
        "bots",
        ["response_generator_model_family", "tenant_id"],
        unique=True,
        postgresql_where="approach = 'chat_gpt_default' AND deleted_at IS NULL",
    )


def downgrade() -> None:
    op.drop_index("idx_basic_ai_unique_model_family", "bots")
