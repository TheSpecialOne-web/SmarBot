from logging import getLogger

from libs.connection import get_connection
from migrations.infrastructure.postgres import (
    get_bot_by_id,
    get_bots_by_tenant_id,
    get_tenant_by_id,
)
from migrations.infrastructure.postgres.document import (
    set_document_folder_id_to_documents,
)
from migrations.infrastructure.postgres.document_folder import (
    create_root_document_folder,
)
from migrations.infrastructure.postgres.document_folder_path import (
    create_root_document_folder_path,
)

logger = getLogger(__name__)
logger.setLevel("INFO")


def init_document_folders_by_bot_id(tenant_id: int, bot_id: int):
    try:
        bot = get_bot_by_id(bot_id)
    except Exception:
        raise Exception(f"bot_id: {bot_id} is invalid.")

    # assert bot belongs to tenant
    if bot.tenant_id != tenant_id:
        raise Exception(f"bot_id: {bot_id} does not belong to tenant_id: {tenant_id}")

    logger.info(f"start migration for bot_id: {bot.id}")

    try:
        conn = get_connection()

        # root folder を作成
        root_document_folder_id = create_root_document_folder(conn, bot.id)

        # root folder の folder paths を作成
        create_root_document_folder_path(conn, root_document_folder_id)

        # 全ての document に folder_id を入れる
        set_document_folder_id_to_documents(conn, bot.id, root_document_folder_id)

        logger.info(f"completed init_document_folders for tenant_id: {tenant_id},  bot_id: {bot.id}")
    except Exception:
        conn.rollback()
        raise Exception(f"failed init_document_folders for tenant_id: {tenant_id}, bot_id: {bot.id}")
    finally:
        conn.close()


def init_document_folders(tenant_id: int):
    # assert tenant exists
    tenant = get_tenant_by_id(tenant_id)

    bots = get_bots_by_tenant_id(tenant.id)

    logger.info(f"start creating root document folders for tenant_id: {tenant.id}")

    for bot in bots:
        init_document_folders_by_bot_id(tenant_id, bot.id)

    logger.info(f"completed creating root document folders for tenant_id: {tenant.id}")


def init_document_folders_by_bot_ids(tenant_id: int, bot_ids: list[int]):
    # assert tenant exists
    tenant = get_tenant_by_id(tenant_id)

    logger.info(f"start creating root document folders for tenant_id: {tenant.id}")

    for bot_id in bot_ids:
        init_document_folders_by_bot_id(tenant_id, bot_id)

    logger.info(f"completed creating root document folders for tenant_id: {tenant.id}")
