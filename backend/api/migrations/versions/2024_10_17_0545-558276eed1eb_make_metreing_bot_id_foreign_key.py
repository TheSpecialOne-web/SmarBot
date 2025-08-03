"""make metreing.bot_id foreign_key

Revision ID: 558276eed1eb
Revises: b375b39c9de1
Create Date: 2024-10-17 05:45:52.716173

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "558276eed1eb"
down_revision = "b375b39c9de1"
branch_labels = None
depends_on = None

CONSTRAINT_NAME = "metering_bot_id_fkey"


def upgrade() -> None:
    op.create_foreign_key(
        constraint_name=CONSTRAINT_NAME,
        source_table="metering",
        referent_table="bots",
        local_cols=["bot_id"],
        remote_cols=["id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "metering", type_="foreignkey")
