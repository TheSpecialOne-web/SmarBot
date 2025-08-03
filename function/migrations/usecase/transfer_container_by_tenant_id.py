from logging import getLogger

from azure.core.exceptions import ResourceNotFoundError

from migrations.infrastructure.blob_storage import (
    copy_blobs_between_containers,
    list_blob_names,
)
from migrations.infrastructure.postgres import (
    get_bots_by_tenant_id,
    get_documents_by_bot_id_v2,
    get_tenant_by_id,
)
from process_document.libs.document import encode_basename

logger = getLogger(__name__)
logger.setLevel("INFO")


def transfer_container_by_tenant_id(tenant_id: int):
    try:
        tenant = get_tenant_by_id(tenant_id)
    except Exception as e:
        raise Exception(f"failed to get tenant: {e}")

    # dbのtenantsテーブルにcontainer_nameがない場合はエラー
    tenant_container_name = tenant.container_name
    if tenant_container_name is None:
        raise Exception(f"container does not exist for tenant {tenant.name}")

    try:
        bots = get_bots_by_tenant_id(tenant_id)
    except Exception as e:
        raise Exception(f"failed to get bots: {e}")

    # botごとにテナントのcontainerにblobを移行
    for bot in bots:
        bot_container_name = bot.container_name
        if bot_container_name is None:
            logger.warning(f"container does not exist for bot {bot.name}")
            continue

        try:
            documents = get_documents_by_bot_id_v2(bot.id)
        except Exception as e:
            raise Exception(f"failed to get documents: {e}")

        existing_blob_names = list_blob_names(container_name=tenant_container_name, bot_id=bot.id)
        logger.info(f"existing blob names: {existing_blob_names}")

        for document in documents:
            target_blob_name = f"{bot.id}/{document.basename}.{document.file_extension}"
            # 九電のファイル名に含まれるバックスラッシュをエンコード
            target_blob_name = target_blob_name.replace("\\", "%5C")
            if target_blob_name in existing_blob_names:
                logger.warning(f"blob already exists for bot {bot.name}. document: {document.basename}")
                continue
            try:
                copy_blobs_between_containers(
                    source_container_name=bot_container_name,
                    source_blob_name=f"{encode_basename(document.basename)}.{document.file_extension}",
                    target_container_name=tenant_container_name,
                    target_blob_name=target_blob_name,
                )
            except ResourceNotFoundError:
                logger.warning(f"blob does not exist for bot {bot.name}. document: {document.basename}")
                continue
            except Exception as e:
                raise Exception(f"failed to copy blob: {e}")

        logger.info(f"copied blobs for bot {bot.name}")

    logger.info(f"copied blobs for tenant {tenant.name}")
