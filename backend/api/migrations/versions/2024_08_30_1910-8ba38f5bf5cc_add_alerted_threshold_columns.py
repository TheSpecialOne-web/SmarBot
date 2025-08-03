"""add alerted threshold columns

Revision ID: 8ba38f5bf5cc
Revises: 164812fcb476
Create Date: 2024-08-30 19:10:15.544153

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import column

# revision identifiers, used by Alembic.
revision = "8ba38f5bf5cc"
down_revision = "164812fcb476"
branch_labels = None
depends_on = None

thresholds = [80, 90, 100]


def upgrade() -> None:
    op.add_column("tenant_alerts", sa.Column("last_token_alerted_threshold", sa.Integer, nullable=True))
    op.add_column("tenant_alerts", sa.Column("last_storage_alerted_threshold", sa.Integer, nullable=True))
    op.add_column("tenant_alerts", sa.Column("last_ocr_alerted_threshold", sa.Integer, nullable=True))

    op.create_check_constraint(
        "ck_tenant_alerts_last_token_alerted_threshold",
        "tenant_alerts",
        sa.or_(
            column("last_token_alerted_threshold").is_(None), column("last_token_alerted_threshold").in_(thresholds)
        ),
    )
    op.create_check_constraint(
        "ck_tenant_alerts_last_storage_alerted_threshold",
        "tenant_alerts",
        sa.or_(
            column("last_storage_alerted_threshold").is_(None),
            column("last_storage_alerted_threshold").in_(thresholds),
        ),
    )
    op.create_check_constraint(
        "ck_tenant_alerts_last_ocr_alerted_threshold",
        "tenant_alerts",
        sa.or_(column("last_ocr_alerted_threshold").is_(None), column("last_ocr_alerted_threshold").in_(thresholds)),
    )


def downgrade() -> None:
    op.drop_constraint("ck_tenant_alerts_last_token_alerted_threshold", "tenant_alerts")
    op.drop_constraint("ck_tenant_alerts_last_storage_alerted_threshold", "tenant_alerts")
    op.drop_constraint("ck_tenant_alerts_last_ocr_alerted_threshold", "tenant_alerts")
    op.drop_column("tenant_alerts", "last_token_alerted_threshold")
    op.drop_column("tenant_alerts", "last_storage_alerted_threshold")
    op.drop_column("tenant_alerts", "last_ocr_alerted_threshold")
