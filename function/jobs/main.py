import argparse
from typing import Any

from libs.constants import MAX_DEQUEUE_COUNT
from libs.logging import get_logger
from migrations import execute as migrations
from process_document import execute as process_documents
from search_index_backup import execute as search_index_backup
from search_index_backup_startup import execute as search_index_backup_startup
from search_index_restore import execute as search_index_restore

from .jobs import JOB_NAMES, Job, JobEnum
from .queue_storage import (
    delete_message,
    get_message,
    read_message,
    reset_message_visibility,
    send_message_to_poison_queue,
)

logger = get_logger(__name__)


def get_job_name_from_args() -> str:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-name", type=str, choices=JOB_NAMES, required=True)
    return parser.parse_args().job_name


def execute_queue_job(job: Job, message_content: dict[str, Any], dequeue_count: int):
    if job.root == JobEnum.MIGRATIONS:
        migrations(
            message_content=message_content,
            dequeue_count=dequeue_count,
        )
    elif job.root == JobEnum.PROCESS_DOCUMENTS:
        process_documents(
            message_content=message_content,
            dequeue_count=dequeue_count,
        )
    elif job.root == JobEnum.SEARCH_INDEX_BACKUP:
        search_index_backup(
            message_content=message_content,
            dequeue_count=dequeue_count,
        )
    elif job.root == JobEnum.SEARCH_INDEX_RESTORE:
        search_index_restore(
            message_content=message_content,
            dequeue_count=dequeue_count,
        )


def execute_timer_job(job: Job):
    if job.root == JobEnum.SEARCH_INDEX_BACKUP_STARTUP:
        search_index_backup_startup()


def execute(job_name: str):
    job = Job.from_str(job_name)
    if job.is_queue_job():
        queue_name = job.get_queue_name()
        if queue_name is None:
            raise ValueError("Invalid job name")

        # キューのメッセージが30分間見えなくなるようにする
        VISIBILITY_TIMEOUT = 60 * 30
        queue_message = get_message(queue_name, VISIBILITY_TIMEOUT)
        if queue_message is None:
            logger.info(f"No message in queue: {queue_name}")
            return

        dequeue_count = int(queue_message.dequeue_count)
        if dequeue_count > MAX_DEQUEUE_COUNT:
            # すでにMAX_DEQUEUE_COUNTまで処理されている場合は、poisonキューにメッセージを移動して、元のキューのメッセージを削除する
            logger.warning(f"Deleting message after {MAX_DEQUEUE_COUNT} tries: {queue_message}")
            send_message_to_poison_queue(f"{queue_name}-poison", queue_message)
            delete_message(queue_name, queue_message)
            return

        try:
            # キューのメッセージを読み込む
            message_content = read_message(queue_message)
            logger.info(f"Executing job {job_name} with message: {message_content}")
            # ジョブの実行
            execute_queue_job(job, message_content, dequeue_count)
            # キューのメッセージを削除する
            delete_message(queue_name, queue_message)
        except Exception as e:
            # マイグレーションジョブ以外の場合は、エラーが発生した場合に再度処理を行う
            if dequeue_count < MAX_DEQUEUE_COUNT and job.root != JobEnum.MIGRATIONS:
                # 再度処理を行うために、キューのメッセージを見えるようにする
                logger.warning(
                    f"Error in job: {job_name}. Resetting message visibility: {queue_message}. Error: {e}",
                    exc_info=e,
                )
                reset_message_visibility(queue_name, queue_message)
            else:
                # キューのメッセージをMAX_DEQUEUE_COUNT回処理してもエラーが発生した場合は、
                # poisonキューにメッセージを移動して、元のキューのメッセージを削除する
                logger.error(
                    f"Error in job: {job_name}. Deleting message after {MAX_DEQUEUE_COUNT} tries: {queue_message}. Error: {e}",
                    exc_info=e,
                )
                send_message_to_poison_queue(f"{queue_name}-poison", queue_message)
                delete_message(queue_name, queue_message)
            raise e
    elif job.is_timer_job():
        try:
            execute_timer_job(job)
        except Exception as e:
            logger.error(f"Error in job: {job_name}. Error: {e}", exc_info=e)
            raise e
    else:
        raise ValueError("Invalid job name")


def main():
    job_name = get_job_name_from_args()
    execute(job_name)


if __name__ == "__main__":
    main()
