from logging import getLogger

from migrations.infrastructure.postgres import get_tenants
from migrations.infrastructure.queue_storage.queue_storage import (
    send_message_to_migration_queue,
)

logger = getLogger(__name__)
logger.setLevel("INFO")


def init_document_folders_startup():
    tenants = get_tenants()
    for tenant in tenants:
        message = {
            "type": "init-document-folders-by-tenant-id",
            "tenant_id": tenant.id,
        }

        try:
            send_message_to_migration_queue(message)
        except Exception as e:
            logger.error(f"failed to send message to migration queue: {e}")
            continue
