"""add enable_basic_ai_web_browsing and basic_ai_pdf_parser and available_models

Revision ID: 7306308d967b
Revises: da6594316be0
Create Date: 2024-06-13 02:47:36.384977

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision = "7306308d967b"
down_revision = "da6594316be0"
branch_labels = None
depends_on = None

# カラム名
ENABLE_BASIC_AI_WEB_BROWSING = "enable_basic_ai_web_browsing"
BASIC_AI_PDF_PARSER = "basic_ai_pdf_parser"
AVAILABLE_MODELS = "available_models"


def upgrade() -> None:
    op.add_column(
        "tenants",
        sa.Column(ENABLE_BASIC_AI_WEB_BROWSING, sa.Boolean, nullable=False, server_default="true"),
    )
    op.add_column(
        "tenants",
        sa.Column(BASIC_AI_PDF_PARSER, sa.String(511), nullable=False, server_default="pypdf"),
    )
    op.add_column(
        "tenants",
        sa.Column(AVAILABLE_MODELS, pg.ARRAY(sa.VARCHAR(511)), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("tenants", ENABLE_BASIC_AI_WEB_BROWSING)
    op.drop_column("tenants", BASIC_AI_PDF_PARSER)
    op.drop_column("tenants", AVAILABLE_MODELS)
