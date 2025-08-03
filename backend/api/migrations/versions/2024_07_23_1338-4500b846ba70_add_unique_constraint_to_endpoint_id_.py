"""add unique constraint to endpoint_id and encrypted_api_key

Revision ID: 4500b846ba70
Revises: 72e13822d4a0
Create Date: 2024-07-23 13:38:38.448008

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "4500b846ba70"
down_revision = "72e13822d4a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("endpoint_id", "bots", ["endpoint_id"])
    op.create_unique_constraint("encrypted_api_key", "api_keys", ["encrypted_api_key"])
    pass


def downgrade() -> None:
    op.drop_constraint("endpoint_id", "bots", type_="unique")
    op.drop_constraint("encrypted_api_key", "api_keys", type_="unique")
    pass
