from datetime import datetime, timezone
from logging import getLogger

from search_index_backup_startup.cognitive_search.cognitive_search import list_indexes
from search_index_backup_startup.queue_storage.queue_storage import (
    send_message_to_index_backup_queue,
)

logger = getLogger(__name__)
logger.setLevel("INFO")


def execute() -> None:
    utc_timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    indexes = list_indexes()
    for index in indexes:
        send_message_to_index_backup_queue(
            {"datetime": utc_timestamp, "endpoint": index.endpoint, "index_name": index.name}
        )
