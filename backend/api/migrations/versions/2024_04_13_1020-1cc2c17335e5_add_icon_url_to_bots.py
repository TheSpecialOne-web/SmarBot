"""add_icon_url_to_bots

Revision ID: 1cc2c17335e5
Revises: fb5f1af76f05
Create Date: 2024-04-13 10:20:36.614540

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1cc2c17335e5"

down_revision = "fb5f1af76f05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "bots",
        sa.Column(
            "icon_url",
            sa.VARCHAR(255),
            nullable=True,
        ),
    )
    pass


def downgrade() -> None:
    op.drop_column("bots", "icon_url")
    pass
