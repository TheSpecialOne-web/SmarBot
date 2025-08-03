from pydantic import BaseModel, StrictInt

from ..document.status import Status


class DocumentProcessingStats(BaseModel):
    num_total_documents: StrictInt
    num_pending_documents: StrictInt
    num_completed_documents: StrictInt
    num_failed_documents: StrictInt
    num_deleting_documents: StrictInt

    @classmethod
    def from_statuses(cls, statuses: list[Status]) -> "DocumentProcessingStats":
        return cls(
            num_total_documents=len(statuses),
            num_pending_documents=statuses.count(Status.PENDING),
            num_completed_documents=statuses.count(Status.COMPLETED),
            num_failed_documents=statuses.count(Status.FAILED),
            num_deleting_documents=statuses.count(Status.DELETING),
        )
