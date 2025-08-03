from enum import Enum

from pydantic import RootModel


class JobEnum(str, Enum):
    ALERT_CAPACITY = "alert-capacity"
    ALERT_CAPACITY_STARTUP = "alert-capacity-startup"
    CALCULATE_STORAGE_USAGE = "calculate-storage-usage"
    CONVERT_AND_UPLOAD_PDF_DOCUMENT = "convert-and-upload-pdf-document"
    CREATE_CONVERSATION_EXPORT = "create-conversation-export"
    CREATE_CHAT_COMPLETION_EXPORT = "create-chat-completion-export"
    CREATE_EMBEDDINGS = "create-embeddings"
    DELETE_ATTACHMENTS = "delete-attachments"
    DELETE_ATTACHMENTS_STARTUP = "delete-attachments-startup"
    DELETE_BOT = "delete-bot"
    DELETE_DOCUMENT_FOLDERS = "delete-document-folders"
    DELETE_MULTIPLE_DOCUMENTS = "delete-multiple-documents"
    DELETE_TENANT = "delete-tenant"
    IMPORT_USERS = "import-users"
    START_EXTERNAL_DATA_CONNECTION = "start-external-data-connection"
    SYNC_DOCUMENT_NAME = "sync-document-name"
    SYNC_DOCUMENT_PATH = "sync-document-path"
    SYNC_DOCUMENT_LOCATION = "sync-document-location"
    UPLOAD_QUESTION_ANSWERS = "upload-question-answers"
    UPLOAD_EXTERNAL_DOCUMENTS = "upload-external-documents"


JOB_NAMES = [job.value for job in JobEnum]


class Job(RootModel):
    root: JobEnum

    @classmethod
    def from_str(cls, job_name: str) -> "Job":
        return cls(root=JobEnum(job_name))

    def is_queue_job(self) -> bool:
        return self.root in [
            JobEnum.ALERT_CAPACITY,
            JobEnum.CALCULATE_STORAGE_USAGE,
            JobEnum.CONVERT_AND_UPLOAD_PDF_DOCUMENT,
            JobEnum.CREATE_CONVERSATION_EXPORT,
            JobEnum.CREATE_CHAT_COMPLETION_EXPORT,
            JobEnum.CREATE_EMBEDDINGS,
            JobEnum.DELETE_ATTACHMENTS,
            JobEnum.IMPORT_USERS,
            JobEnum.DELETE_BOT,
            JobEnum.DELETE_DOCUMENT_FOLDERS,
            JobEnum.DELETE_MULTIPLE_DOCUMENTS,
            JobEnum.DELETE_TENANT,
            JobEnum.START_EXTERNAL_DATA_CONNECTION,
            JobEnum.SYNC_DOCUMENT_NAME,
            JobEnum.SYNC_DOCUMENT_PATH,
            JobEnum.SYNC_DOCUMENT_LOCATION,
            JobEnum.UPLOAD_QUESTION_ANSWERS,
            JobEnum.UPLOAD_EXTERNAL_DOCUMENTS,
        ]

    def is_timer_job(self) -> bool:
        return self.root in [
            JobEnum.ALERT_CAPACITY_STARTUP,
            JobEnum.DELETE_ATTACHMENTS_STARTUP,
        ]

    def get_queue_name(self) -> str:
        if self.is_queue_job() is False:
            raise ValueError("Invalid job name")
        queue_name = JOB_NAMES_TO_QUEUE_NAMES.get(self.root)
        if queue_name is None:
            raise ValueError("Invalid job name")
        return queue_name


JOB_NAMES_TO_QUEUE_NAMES = {
    JobEnum.ALERT_CAPACITY: "alert-capacity-queue",
    JobEnum.CALCULATE_STORAGE_USAGE: "calculate-storage-usage-queue",
    JobEnum.CONVERT_AND_UPLOAD_PDF_DOCUMENT: "convert-and-upload-pdf-document-queue",
    JobEnum.CREATE_CONVERSATION_EXPORT: "create-conversation-export-queue",
    JobEnum.CREATE_CHAT_COMPLETION_EXPORT: "create-chat-completion-export-queue",
    JobEnum.CREATE_EMBEDDINGS: "create-embeddings-queue",
    JobEnum.DELETE_ATTACHMENTS: "delete-attachments-queue",
    JobEnum.DELETE_BOT: "delete-bot-queue",
    JobEnum.DELETE_DOCUMENT_FOLDERS: "delete-document-folders-queue",
    JobEnum.DELETE_MULTIPLE_DOCUMENTS: "delete-multiple-documents-queue",
    JobEnum.DELETE_TENANT: "delete-tenant-queue",
    JobEnum.IMPORT_USERS: "users-import-queue",
    JobEnum.START_EXTERNAL_DATA_CONNECTION: "start-external-data-connection-queue",
    JobEnum.SYNC_DOCUMENT_NAME: "sync-document-name-queue",
    JobEnum.SYNC_DOCUMENT_PATH: "sync-document-path-queue",
    JobEnum.SYNC_DOCUMENT_LOCATION: "sync-document-location-queue",
    JobEnum.UPLOAD_QUESTION_ANSWERS: "upload-question-answers-queue",
    JobEnum.UPLOAD_EXTERNAL_DOCUMENTS: "upload-external-documents-queue",
}

MAX_DEQUEUE_COUNT = 3
