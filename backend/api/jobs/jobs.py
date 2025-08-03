from dotenv import load_dotenv

load_dotenv(".env")

from typing import Any

import click

from api.domain.models.job import MAX_DEQUEUE_COUNT, Job, JobEnum
from api.libs.logging import get_logger

from .alert_capacity import alert_capacity
from .alert_capacity_start_up import alert_capacity_start_up
from .calculate_storage_usage import calculate_storage_usage
from .convert_and_upload_pdf_document import convert_and_upload_pdf_document
from .create_chat_completion_export import create_chat_completion_export
from .create_conversation_export import create_conversation_export
from .create_embeddings import create_embeddings
from .delete_attachments import delete_attachments
from .delete_attachments_start_up import delete_attachments_start_up
from .delete_bot import delete_bot
from .delete_document_folders import delete_document_folders
from .delete_multiple_documents import delete_multiple_documents
from .delete_tenant import delete_tenant
from .import_users import import_users
from .queue_storage import (
    delete_message,
    get_message,
    read_message,
    reset_message_visibility,
    send_message_to_poison_queue,
)
from .start_external_data_connection import start_external_data_connection
from .sync_document_location import sync_document_location
from .sync_document_name import sync_document_name
from .sync_document_path import sync_document_path
from .upload_external_documents import upload_external_documents
from .upload_question_answers import upload_question_answers

logger = get_logger()


@click.command("jobs")
@click.argument("job_name")
def jobs(job_name: str):
    execute_jobs(job_name)


def execute_jobs(job_name: str):
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
            # if dequeue_count < MAX_DEQUEUE_COUNT and job.root != JobEnum.MIGRATIONS:
            if dequeue_count < MAX_DEQUEUE_COUNT:
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


def execute_queue_job(job: Job, message_content: dict[str, Any], dequeue_count: int):
    if job.root == JobEnum.ALERT_CAPACITY:
        alert_capacity(message_content, dequeue_count)

    elif job.root == JobEnum.CALCULATE_STORAGE_USAGE:
        calculate_storage_usage(message_content, dequeue_count)

    elif job.root == JobEnum.SYNC_DOCUMENT_NAME:
        sync_document_name(message_content, dequeue_count)

    elif job.root == JobEnum.CONVERT_AND_UPLOAD_PDF_DOCUMENT:
        convert_and_upload_pdf_document(message_content, dequeue_count)

    elif job.root == JobEnum.CREATE_CHAT_COMPLETION_EXPORT:
        create_chat_completion_export(message_content, dequeue_count)

    elif job.root == JobEnum.CREATE_CONVERSATION_EXPORT:
        create_conversation_export(message_content, dequeue_count)

    elif job.root == JobEnum.CREATE_EMBEDDINGS:
        create_embeddings(message_content, dequeue_count)

    elif job.root == JobEnum.DELETE_ATTACHMENTS:
        delete_attachments(message_content, dequeue_count)

    elif job.root == JobEnum.DELETE_BOT:
        delete_bot(message_content, dequeue_count)

    elif job.root == JobEnum.DELETE_DOCUMENT_FOLDERS:
        delete_document_folders(message_content, dequeue_count)

    elif job.root == JobEnum.DELETE_MULTIPLE_DOCUMENTS:
        delete_multiple_documents(message_content, dequeue_count)

    elif job.root == JobEnum.DELETE_TENANT:
        delete_tenant(message_content, dequeue_count)

    elif job.root == JobEnum.IMPORT_USERS:
        import_users(message_content, dequeue_count)

    elif job.root == JobEnum.START_EXTERNAL_DATA_CONNECTION:
        start_external_data_connection(message_content, dequeue_count)

    elif job.root == JobEnum.UPLOAD_QUESTION_ANSWERS:
        upload_question_answers(message_content, dequeue_count)

    elif job.root == JobEnum.SYNC_DOCUMENT_PATH:
        sync_document_path(message_content, dequeue_count)

    elif job.root == JobEnum.SYNC_DOCUMENT_LOCATION:
        sync_document_location(message_content, dequeue_count)

    elif job.root == JobEnum.UPLOAD_EXTERNAL_DOCUMENTS:
        upload_external_documents(message_content, dequeue_count)


def execute_timer_job(job: Job):
    if job.root == JobEnum.ALERT_CAPACITY_STARTUP:
        alert_capacity_start_up()
    elif job.root == JobEnum.DELETE_ATTACHMENTS_STARTUP:
        delete_attachments_start_up()
