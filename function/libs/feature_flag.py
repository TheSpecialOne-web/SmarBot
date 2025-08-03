from logging import getLogger
import os

import ldclient
from ldclient import Context
from ldclient.config import Config

logger = getLogger(__name__)
logger.setLevel("INFO")

LAUNCH_DARKLY_SDK_KEY = os.environ.get("LAUNCH_DARKLY_SDK_KEY") or ""
CONTEXT_KIND_TENANT = "tenant"

ldclient.set_config(Config(sdk_key=LAUNCH_DARKLY_SDK_KEY))
client = ldclient.get()


def get_feature_flag(flag_key: str, tenant_id: int, tenant_name: str, default: bool = False) -> bool:
    if not client.is_initialized():
        logger.error("LaunchDarkly client is not initialized")
        return default

    context = Context(
        kind=CONTEXT_KIND_TENANT,
        key=f"tenant_id:{tenant_id}",
        name=tenant_name,
    )
    try:
        flag = client.variation(flag_key, context, False)
        return flag
    except Exception as e:
        logger.error(f"failed to get feature flag: {e}")
        return default
