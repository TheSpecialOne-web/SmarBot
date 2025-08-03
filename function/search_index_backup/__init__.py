import json
from logging import getLogger
import math
from typing import cast

from azure.search.documents.indexes.models import SearchField, SearchIndex

from search_index_backup.blob_storage.blob_storage import upload_to_blob
from search_index_backup.cognitive_search.cognitive_search import (
    get_documents_after_sort_field,
    get_documents_count_after_sort_field,
    get_index,
)
from search_index_backup.queue_storage.queue_storage import (
    send_message_to_index_backup_queue,
)
from search_index_backup.types import IndexBackupQueue, SortField

logger = getLogger(__name__)
logger.setLevel("INFO")


SORT_FIELDS = ["created_at", "construction_start_date"]


def get_sort_field_key(index: SearchIndex) -> str:
    for field in index.fields:
        try:
            field = cast(SearchField, field)
            field_name = str(field.name)
        except Exception:
            continue
        if field_name in SORT_FIELDS:
            return field_name
    raise Exception("Sort field not found")


def get_last_sort_field_value(documents: list[dict], sort_field_key: str) -> str:
    if len(documents) == 0:
        raise Exception("documents is empty")
    return documents[-1][sort_field_key]


def backup_index_documents_to_blob(
    datetime: str,
    endpoint: str,
    index_name: str,
    sort_field_value: str | None,
) -> None:
    index = get_index(endpoint, index_name)

    # ソートに使う情報を取得
    sort_field_key = get_sort_field_key(index)
    sort_field = SortField(key=sort_field_key, value=sort_field_value)

    # 残りのドキュメント数を取得
    remaining_documents_count = get_documents_count_after_sort_field(endpoint, index_name, sort_field)

    # ドキュメントがない場合は空のファイルをアップロード
    if remaining_documents_count == 0:
        json_str = json.dumps({"documents": []}, ensure_ascii=False)
        path = f"{datetime}/{index_name}/empty.json"
        upload_to_blob(path, json_str)
        return

    LIMIT = 1000
    MAX_ITERATIONS = 20

    # 残りの繰り返し回数
    remaining_iterations = math.ceil(remaining_documents_count / LIMIT)

    # 今回の繰り返し回数
    num_iterations = min(MAX_ITERATIONS, remaining_iterations)

    last_sort_field_value = None
    for i in range(num_iterations):
        # 指定したcreated_atよりも新しいドキュメントを取得
        documents = get_documents_after_sort_field(
            endpoint=endpoint,
            index_name=index_name,
            top=LIMIT,
            sort_field=sort_field,
            skip=i * LIMIT,
        )

        # 最後のドキュメントのsort_fieldの値を取得
        last_sort_field_value = get_last_sort_field_value(documents, sort_field_key)

        json_str = json.dumps({"documents": documents}, ensure_ascii=False)
        path = f"{datetime}/{index_name}/{last_sort_field_value}.json"
        upload_to_blob(path, json_str)

    if last_sort_field_value is None:
        raise Exception("last_sort_field is required")

    # まだ残りがある場合は次のキューを送信
    if remaining_iterations > MAX_ITERATIONS:
        send_message_to_index_backup_queue(
            datetime=datetime,
            endpoint=endpoint,
            index_name=index_name,
            sort_field_value=last_sort_field_value,
        )
        logger.info(f"next queue: {datetime}, {endpoint}, {index_name}, {last_sort_field_value}")
    else:
        logger.info(f"index backup completed for {index_name}")


def execute(message_content: dict, dequeue_count: int = 0):
    queue = IndexBackupQueue(**message_content)
    logger.info(f"datetime: {queue.datetime}, index_name: {queue.index_name}, sort_field: {queue.sort_field_value}")

    backup_index_documents_to_blob(queue.datetime, queue.endpoint, queue.index_name, queue.sort_field_value)
