from libs.logging import get_logger
from migrations.infrastructure.postgres import get_tenants
from migrations.infrastructure.postgres.postgres import (
    update_tenant_allowed_model_families,
)
from migrations.types import ModelFamily, Text2ImageModelFamily

logger = get_logger(__name__)
logger.setLevel("INFO")


def add_allowed_model_families_to_tenants():
    tenants = get_tenants()

    # tenantのadditional_platformsとallow_foreign_regionから#許可モデルファミリーを作成する
    for tenant in tenants:
        additional_platforms = tenant.additional_platforms
        allow_foreign_region = tenant.allow_foreign_region
        allowed_model_families = []
        allowed_model_families.append(ModelFamily.GPT_35_TURBO)
        allowed_model_families.append(ModelFamily.GPT_4)
        # 許可モデルファミリーを作成する
        if "gcp" in additional_platforms:
            allowed_model_families.append(ModelFamily.GEMINI_15_FLASH)
            allowed_model_families.append(ModelFamily.GEMINI_15_PRO)
            allowed_model_families.append(ModelFamily.GEMINI_10_PRO)
        if allow_foreign_region:
            allowed_model_families.append(ModelFamily.GPT_4O)
            allowed_model_families.append(ModelFamily.GPT_4_TURBO)
            allowed_model_families.append(ModelFamily.GPT_4O_MINI)
            allowed_model_families.append(Text2ImageModelFamily.DALL_E_3)

        if "gcp" in additional_platforms and allow_foreign_region:
            allowed_model_families.append(ModelFamily.CLAUDE_35_SONNET)
            allowed_model_families.append(ModelFamily.CLAUDE_3_SONNET)
            allowed_model_families.append(ModelFamily.CLAUDE_3_HAIKU)
            allowed_model_families.append(ModelFamily.CLAUDE_3_OPUS)

        update_tenant_allowed_model_families(tenant.id, allowed_model_families)
        logger.info(f"added tenant_id: {tenant.id}, allowed_model_families: {allowed_model_families}")

    logger.info("add_allowed_model_families_to_tenants finished")
