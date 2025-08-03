from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.document import DocumentUseCase


def sync_document_path(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.SyncDocumentPathQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        sync_document_path_interactor = injector.get(DocumentUseCase)
        sync_document_path_interactor.sync_document_path(
            msg.tenant_id, msg.bot_id, msg.document_folder_id, msg.document_ids
        )
