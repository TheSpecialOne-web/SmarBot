from logging import getLogger

from migrations.infrastructure.blob_storage import create_container
from migrations.infrastructure.postgres import get_tenant_by_id, set_container_name

logger = getLogger(__name__)
logger.setLevel("INFO")


def create_tenant_container(tenant_id: int):
    # テナントを取得
    try:
        tenant = get_tenant_by_id(tenant_id)
    except Exception as e:
        raise Exception(f"failed to get tenant: {e}")

    # すでにcontainerがある場合はreturn
    if tenant.container_name is not None:
        logger.warning(f"container already exists for tenant {tenant.name}")
        return

    # containerを作成
    try:
        create_container(tenant.alias)
    except Exception as e:
        raise Exception(f"failed to create container for tenant {tenant.name}: {e}")

    # container_nameをDBに保存
    try:
        set_container_name(tenant)
    except Exception as e:
        raise Exception(f"failed to save container name for tenant {tenant.name}: {e}")
