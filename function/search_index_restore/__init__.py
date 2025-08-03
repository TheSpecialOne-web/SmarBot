from datetime import datetime, timezone
import json
from logging import getLogger

from search_index_restore.blob_storage.blob_storage import download_blob, list_blobs
from search_index_restore.cognitive_search.cognitive_search import upload_documents
from search_index_restore.queue_storage.queue_storage import (
    RestoreIndexQueue,
    send_message_to_index_restore_queue,
)

logger = getLogger(__name__)
logger.setLevel("INFO")


RESTORE_BLOBS_LIMIT = 20


def execute(message_content: dict, dequeue_count: int = 0) -> None:
    queue = RestoreIndexQueue(**message_content)
    endpoint = queue.endpoint
    folder_name = queue.folder_name
    index_name = queue.index_name
    last_blob_version_id_str = queue.last_blob_version_id
    last_blob_version_id = datetime.fromisoformat(last_blob_version_id_str) if last_blob_version_id_str else None
    restore_index(
        folder_name=folder_name, endpoint=endpoint, index_name=index_name, last_blob_version_id=last_blob_version_id
    )


# TODO: python 3.11 以降では、datetime.fromisoformat を使う version_id ex)2024-08-29T17:08:50.5621724Z
def _parse_version_id(version_id: str) -> datetime:
    # 'Z' を削除
    if version_id.endswith("Z"):
        version_id = version_id[:-1]

    # blobのversion_idは8桁でpython3.11未満では対応できないためマイクロ秒を6桁に制限
    parts = version_id.split(".")
    if len(parts) > 1:
        microseconds = parts[1][:6]  # 最初の6桁のみを使用
        version_id = f"{parts[0]}.{microseconds}"

    # strptimeでパース
    dt = datetime.strptime(version_id, "%Y-%m-%dT%H:%M:%S.%f")

    # UTCタイムゾーンを設定
    return dt.replace(tzinfo=timezone.utc)


def restore_index(endpoint: str, folder_name: str, index_name: str, last_blob_version_id: datetime | None) -> None:
    logger.info(f"folder_name: {folder_name}, index_name: {index_name}")

    blobs = list_blobs(f"{folder_name}/{index_name}/")
    if len(blobs) == 0:
        logger.info("no blobs to restore")
        return

    sorted_blobs_by_version_id = sorted(blobs, key=lambda x: _parse_version_id(str(x.version_id)))

    # バックアップの作成日時より新しい20件のバックアップを取得(1バックアップあたり5000件のドキュメントをアップロード)
    target_blobs = [
        blob
        for blob in sorted_blobs_by_version_id
        if last_blob_version_id is None or _parse_version_id(str(blob.version_id)) > last_blob_version_id
    ][:RESTORE_BLOBS_LIMIT]

    for target_blob in target_blobs:
        if target_blob.name is None:
            raise ValueError("blob_name is None")

        blob = download_blob(target_blob.name)
        backup_data: dict[str, list[dict]] = json.loads(blob)

        documents = backup_data["documents"]
        # NOTE: Cognitive Search の upload_documents は既存のドキュメントを上書きする
        upload_documents(endpoint, index_name, documents)

    # 残りのドキュメント数を取得
    last_blob_version_id = _parse_version_id(str(target_blobs[-1].version_id))
    logger.info(f"last_blob_version_id: {last_blob_version_id}")
    remaining_blobs_count = len(
        [blob for blob in sorted_blobs_by_version_id if _parse_version_id(str(blob.version_id)) > last_blob_version_id]
    )
    logger.info(f"remaining_blobs_count: {remaining_blobs_count}")
    # 残りのドキュメント数がある場合は、再帰的に呼び出す
    if remaining_blobs_count > 0:
        send_message_to_index_restore_queue(
            folder_name=folder_name,
            endpoint=endpoint,
            index_name=index_name,
            last_blob_version_id=str(last_blob_version_id),
        )
        return
    logger.info(f"successfully restored index: {index_name}")
