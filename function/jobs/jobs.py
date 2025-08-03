from enum import Enum

from pydantic import RootModel


class JobEnum(str, Enum):
    MIGRATIONS = "migrations"
    PROCESS_DOCUMENTS = "process-documents"
    SEARCH_INDEX_BACKUP = "search-index-backup"
    SEARCH_INDEX_BACKUP_STARTUP = "search-index-backup-startup"
    SEARCH_INDEX_RESTORE = "search-index-restore"


JOB_NAMES = [job.value for job in JobEnum]


class Job(RootModel):
    root: JobEnum

    @classmethod
    def from_str(cls, job_name: str) -> "Job":
        return cls(root=JobEnum(job_name))

    def is_queue_job(self) -> bool:
        return self.root in [
            JobEnum.MIGRATIONS,
            JobEnum.PROCESS_DOCUMENTS,
            JobEnum.SEARCH_INDEX_BACKUP,
            JobEnum.SEARCH_INDEX_RESTORE,
        ]

    def is_timer_job(self) -> bool:
        return self.root in [
            JobEnum.SEARCH_INDEX_BACKUP_STARTUP,
        ]

    def get_queue_name(self) -> str:
        if self.is_queue_job() is False:
            raise ValueError("Invalid job name")
        queue_name = JOB_NAMES_TO_QUEUE_NAMES.get(self.root)
        if queue_name is None:
            raise ValueError("Invalid job name")
        return queue_name


JOB_NAMES_TO_QUEUE_NAMES = {
    JobEnum.MIGRATIONS: "migration-queue",
    JobEnum.PROCESS_DOCUMENTS: "documents-process-queue",
    JobEnum.SEARCH_INDEX_BACKUP: "backup-index-queue",
    JobEnum.SEARCH_INDEX_RESTORE: "restore-index-queue",
}
