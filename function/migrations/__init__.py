from logging import getLogger

from migrations.usecase import MigrationQueueMessage, UseCase

logger = getLogger(__name__)
logger.setLevel("INFO")


def execute(message_content: dict, dequeue_count: int = 0):
    migration_queue_message = MigrationQueueMessage(**message_content)

    use_case = UseCase()
    try:
        use_case.execute(migration_queue_message)
    except Exception as e:
        logger.error(f"failed to execute use case: {e}")
        raise e
