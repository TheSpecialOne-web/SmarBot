from migrations.infrastructure.blob_storage.blob_storage import create_container
from migrations.infrastructure.postgres.postgres import (
    Tenant,
    get_chat_gpt_bots,
    get_tenants,
    update_bot_container_name,
)


def filter_tenants_by_id(tenants: list[Tenant], tenant_id: int) -> Tenant | None:
    for tenant in tenants:
        if tenant.id == tenant_id:
            return tenant
    return None


def create_blob_containers_for_chat_gpt_default():
    tenants = get_tenants()
    bots = get_chat_gpt_bots()
    for bot in bots:
        tenant = filter_tenants_by_id(tenants, bot.tenant_id)
        if not tenant:
            raise Exception(f"tenant not found for bot {bot.id}")
        container_name = f"{tenant.alias}-chat-gpt-default-{bot.id}"
        try:
            create_container(container_name)
        except Exception as e:
            raise Exception(f"failed to create blob container for bot {bot.id}: {e}")

        try:
            update_bot_container_name(bot.id, container_name)
        except Exception as e:
            raise Exception(f"failed to update bot container name for bot {bot.id}: {e}")
