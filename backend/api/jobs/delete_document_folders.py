from api.database import SessionFactory
from api.dependency_injector import get_injector
from api.domain.models import job as job_domain
from api.usecase.job.delete_document_folders import DeleteDocumentFoldersUseCase


def delete_document_folders(message_content: dict, dequeue_count: int = 0):
    msg = job_domain.DeleteDocumentFoldersQueue.from_dict(message_content)

    with SessionFactory() as session:
        injector = get_injector(session)
        delete_document_folders_interactor = injector.get(DeleteDocumentFoldersUseCase)
        delete_document_folders_interactor.delete_document_folders(
            tenant_id=msg.tenant_id, bot_id=msg.bot_id, document_folder_ids=msg.document_folder_ids
        )
