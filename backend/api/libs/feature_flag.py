import os

import ldclient
from ldclient import Context
from ldclient.config import Config

from api.domain.models.tenant import (
    Id as TenantId,
    Name as TenantName,
)
from api.libs.logging import get_logger

LAUNCH_DARKLY_SDK_KEY = os.environ.get("LAUNCH_DARKLY_SDK_KEY") or ""
CONTEXT_KIND_TENANT = "tenant"

ldclient.set_config(Config(sdk_key=LAUNCH_DARKLY_SDK_KEY))
client = ldclient.get()

logger = get_logger()


def get_feature_flag(flag_key: str, tenant_id: TenantId, tenant_name: TenantName, default: bool = False) -> bool:
    if not client.is_initialized():
        logger.error("LaunchDarkly client is not initialized")
        return default

    context = Context(
        kind=CONTEXT_KIND_TENANT,
        key=f"tenant_id:{tenant_id.value}",
        name=tenant_name.value,
    )
    try:
        flag = client.variation(flag_key, context, False)
        return flag
    except Exception as e:
        logger.error("LaunchDarkly error", exc_info=e)
        return default


def get_feature_flag_with_anonymous_context(flag_key: str, default: bool = False) -> bool:
    if not client.is_initialized():
        logger.error("LaunchDarkly client is not initialized")
        return default

    context = Context(
        kind=None,
        key="anonymous",
        anonymous=True,
    )

    try:
        flag = client.variation(flag_key, context, False)
        return flag
    except Exception as e:
        logger.error("LaunchDarkly error", exc_info=e)
        return default
